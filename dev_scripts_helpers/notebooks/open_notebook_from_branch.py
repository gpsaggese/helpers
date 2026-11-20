#!/usr/bin/env python

r"""
Open a notebook from a git branch in a live Jupyter Lab, in a git worktree.

The current client is not touched. The script:
- resolves a PR URL passed as `--branch` to the head branch of the PR with `gh`
- fetches the branch from `origin`
- creates a git worktree for the branch, or reuses and fast-forwards the existing
  one
- finds the project dir (i.e., the closest dir above the notebook storing
  `docker_jupyter.sh`)
- builds the project Docker image with `docker_build.sh`
- starts Jupyter Lab with `docker_jupyter.sh`
- opens the notebook in the browser as soon as Jupyter Lab answers

Stop Jupyter Lab with Ctrl+C. The worktree is left in place, remove it with
`git worktree remove <worktree_dir>`.

# Usage Example

- Open a notebook from a branch:
> open_notebook_from_branch.py \
    -i research/Optimal_strategy_for_racket_sports/notebooks/racket_shot_probability.ipynb \
    --branch UmdTask788_Racket_sports_Change_color_of_heatmaps

- Open a notebook from the branch of a PR, passing the PR URL:
> open_notebook_from_branch.py \
    -i tutorials/AutoGluon/AutoGluon.API.ipynb \
    --branch https://github.com/gpsaggese/gpsaggese.github.io/pull/895

- Print the commands that change the client or start containers without
  running them:
> open_notebook_from_branch.py -i <notebook> --branch <branch> --dry_run

- Skip the Docker build, since the image is already built:
> open_notebook_from_branch.py -i <notebook> --branch <branch> --no_build

- Use another port and stop the Jupyter container already running:
> open_notebook_from_branch.py -i <notebook> --branch <branch> --port 8889 \
    --kill_existing_jupyter

Import as:

import dev_scripts_helpers.notebooks.open_notebook_from_branch as dsnoonfb
"""

import argparse
import json
import logging
import os
import re
import shlex
import socket
import threading
import time
import urllib.parse
import webbrowser
from typing import Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Seconds to wait for Jupyter Lab to answer before giving up on opening the
# browser (the first run can take long to pull the image).
_JUPYTER_READY_TIMEOUT_IN_SECS = 600

# #############################################################################
# Git helpers
# #############################################################################


def _normalize_branch(branch: str) -> str:
    """
    Remove the `origin/` prefix from a branch name.

    :param branch: branch name, with or without the remote
        - E.g., `origin/UmdTask788_Racket_sports` or `UmdTask788_Racket_sports`
    :return: branch name without remote
        - E.g., `UmdTask788_Racket_sports`
    """
    prefix = "origin/"
    branch = branch.removeprefix(prefix)
    return branch


def _parse_pr_url(txt: str) -> Optional[Tuple[str, int]]:
    """
    Parse a GitHub PR URL into the repo full name and the PR number.

    Trailing parts of the URL (e.g., `/files`, `?diff=split`, `#issuecomment-1`)
    are ignored.

    :param txt: string passed to `--branch`
        - E.g., `https://github.com/gpsaggese/gpsaggese.github.io/pull/895`
    :return: `(repo_full_name, pr_number)` if `txt` is a PR URL, `None` if it is
        a branch name
        - E.g., `("gpsaggese/gpsaggese.github.io", 895)`
    """
    # Match `https://github.com/<owner>/<repo>/pull/<number>` followed by
    # nothing or by a `/`, `?` or `#` part.
    pr_url_re = re.compile(
        r"""
        ^https?://github\.com/
        (?P<repo>[^/\s]+/[^/\s]+)/
        pull/(?P<num>\d+)
        (?:[/?#].*)?$
        """,
        re.VERBOSE,
    )
    match = pr_url_re.match(txt.strip())
    ret: Optional[Tuple[str, int]] = None
    if match:
        ret = (match.group("repo"), int(match.group("num")))
    return ret


def _parse_pr_head_branch(txt: str, pr_url: str) -> str:
    """
    Get the head branch of a PR from the JSON output of `gh pr view`.

    :param txt: JSON with the keys `headRefName` and `isCrossRepository`
        - E.g., `{"headRefName": "UmdTask1_Foo", "isCrossRepository": false}`
    :param pr_url: PR URL, used only in the error messages
    :return: head branch name without remote
    """
    info = json.loads(txt)
    hdbg.dassert(
        not info["isCrossRepository"],
        "PR '%s' comes from a fork, so its branch is not on 'origin'",
        pr_url,
    )
    branch = info["headRefName"]
    return branch


def _resolve_branch(branch: str, *, git_root: str) -> str:
    """
    Get the branch name from a branch name or a GitHub PR URL.

    A PR URL is resolved to its head branch with `gh`. This is a read-only query,
    so it runs also in a dry run.

    :param branch: branch name, with or without the remote, or PR URL
        - E.g., `UmdTask788_Racket_sports`, `origin/UmdTask788_Racket_sports`, or
          `https://github.com/gpsaggese/gpsaggese.github.io/pull/895`
    :param git_root: absolute path of the git root
    :return: branch name without remote
    """
    pr_info = _parse_pr_url(branch)
    if pr_info is None:
        ret = _normalize_branch(branch)
    else:
        pr_repo, pr_num = pr_info
        # The branch is fetched from `origin`, so the PR must belong to it.
        origin_repo = hgit.get_repo_full_name_from_dirname(
            git_root, include_host_name=False
        )
        hdbg.dassert_eq(
            pr_repo,
            origin_repo,
            "PR is not in the repo of 'origin': run the script from a client "
            "of the PR repo",
        )
        cmd = [
            f"gh pr view {shlex.quote(branch.strip())}",
            "--json headRefName,isCrossRepository",
        ]
        cmd = " ".join(cmd)
        _, txt = hsystem.system_to_string(cmd, suppress_output=True)
        ret = _parse_pr_head_branch(txt, branch)
        _LOG.info("PR #%s is on branch '%s'", pr_num, ret)
    return ret


def _get_notebook_rel_path(notebook: str, git_root: str) -> str:
    """
    Get the path of the notebook relative to the git root.

    A path that exists locally (absolute or relative to the current dir) is
    converted to a path relative to the git root. Any other path is assumed to be
    already relative to the git root, since the notebook can exist only on the
    branch.

    :param notebook: path of the notebook
    :param git_root: absolute path of the git root
    :return: path relative to the git root
        - E.g., `research/Racket/notebooks/racket_shot_probability.ipynb`
    """
    if os.path.isabs(notebook) or os.path.exists(notebook):
        rel_path = os.path.relpath(os.path.abspath(notebook), git_root)
    else:
        rel_path = notebook
    hdbg.dassert(rel_path.endswith(".ipynb"), "'%s' is not a notebook", rel_path)
    hdbg.dassert(
        not rel_path.startswith(".."),
        "'%s' is outside the git root '%s'",
        rel_path,
        git_root,
    )
    return rel_path


def _fetch_branch(branch: str, *, git_root: str) -> None:
    """
    Fetch a branch from `origin`, falling back to the local remote-tracking ref.

    The fetch fails when the remote branch is deleted (e.g., after the PR is
    merged) or when offline. In this case the local `origin/<branch>` ref, if
    any, is used.

    :param branch: branch name without remote
    :param git_root: absolute path of the git root
    """
    git_cmd = f"git -C {shlex.quote(git_root)}"
    branch_arg = shlex.quote(branch)
    rc, _ = hsystem.system_to_string(
        f"{git_cmd} fetch origin {branch_arg}", abort_on_error=False
    )
    if rc != 0:
        # Check that the remote-tracking ref is known locally.
        ref = shlex.quote(f"origin/{branch}")
        rc, _ = hsystem.system_to_string(
            f"{git_cmd} rev-parse --verify --quiet {ref}", abort_on_error=False
        )
        hdbg.dassert_eq(
            rc,
            0,
            "Can't fetch branch 'origin/%s' and it is not known locally",
            branch,
        )
        _LOG.warning(
            "Can't fetch 'origin/%s' (e.g., offline or deleted after the "
            "merge): using the local copy",
            branch,
        )


def _find_project_dir(branch: str, rel_notebook: str, *, git_root: str) -> str:
    """
    Find the closest dir above the notebook that stores `docker_jupyter.sh`.

    :param branch: branch name without remote
    :param rel_notebook: path of the notebook relative to the git root
    :param git_root: absolute path of the git root
    :return: project dir relative to the git root (empty for the git root)
        - E.g., `research/Optimal_strategy_for_racket_sports`
    """
    dir_name = os.path.dirname(rel_notebook)
    project_dir: Optional[str] = None
    while project_dir is None:
        script = os.path.join(dir_name, "docker_jupyter.sh")
        if hgit.exists_on_ref(f"origin/{branch}", script, git_root=git_root):
            project_dir = dir_name
        else:
            hdbg.dassert_ne(
                dir_name,
                "",
                "No 'docker_jupyter.sh' found above '%s' on branch '%s'",
                rel_notebook,
                branch,
            )
            dir_name = os.path.dirname(dir_name)
    return project_dir


# #############################################################################
# Run commands
# #############################################################################


def _run(cmd: str, *, dry_run: bool) -> None:
    """
    Run a command showing its output, or only report it in a dry run.

    :param cmd: command to run
    :param dry_run: report the command without running it
    """
    if dry_run:
        _LOG.warning("[DRY_RUN] Would run: %s", cmd)
    else:
        _LOG.info("Running: %s", cmd)
        hsystem.system(cmd, suppress_output=False)


# #############################################################################
# Jupyter
# #############################################################################


def _is_port_in_use(port: int) -> bool:
    """
    Check if something is listening on a local port.

    :param port: port on the host
    :return: whether a connection to the port succeeds
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        in_use = sock.connect_ex(("localhost", port)) == 0
    return in_use


def _get_notebook_url(rel_notebook: str, port: int) -> str:
    """
    Get the URL of a notebook served by Jupyter Lab in the container.

    The git root is mounted at `/git_root` in the container.

    :param rel_notebook: path of the notebook relative to the git root
    :param port: port of Jupyter Lab on the host
    :return: URL of the notebook
        - E.g., `http://localhost:8888/lab/tree/git_root/dir/notebook.ipynb`
    """
    quoted_path = urllib.parse.quote(rel_notebook)
    url = f"http://localhost:{port}/lab/tree/git_root/{quoted_path}"
    return url


def _open_browser_when_ready(url: str, port: int) -> None:
    """
    Wait for Jupyter Lab to answer and open a URL in the browser.

    :param url: URL to open
    :param port: port of Jupyter Lab on the host
    """
    cmd = f"curl --silent --fail --max-time 2 http://localhost:{port}/api"
    start_time = time.time()
    is_ready = False
    while (
        not is_ready
        and time.time() - start_time < _JUPYTER_READY_TIMEOUT_IN_SECS
    ):
        rc, _ = hsystem.system_to_string(
            cmd, abort_on_error=False, print_command=False
        )
        is_ready = rc == 0
        if not is_ready:
            time.sleep(2)
    if is_ready:
        _LOG.info("Opening '%s'", url)
        webbrowser.open(url)
    else:
        _LOG.warning(
            "Jupyter Lab did not answer in %s secs: open '%s' by hand",
            _JUPYTER_READY_TIMEOUT_IN_SECS,
            url,
        )


def _start_jupyter(
    project_dir: str,
    url: str,
    *,
    port: int,
    kill_existing_jupyter: bool,
    open_browser: bool,
    dry_run: bool,
) -> None:
    """
    Start Jupyter Lab in the project container and open the notebook.

    The call blocks until Jupyter Lab is stopped.

    :param project_dir: absolute path of the dir storing `docker_jupyter.sh`
    :param url: URL of the notebook to open
    :param port: port of Jupyter Lab on the host
    :param kill_existing_jupyter: stop the Jupyter container already running
        for the project
    :param open_browser: open the notebook in the browser when Jupyter Lab is
        ready
    :param dry_run: report the command without running it
    """
    cmd = [
        f"cd {shlex.quote(project_dir)} &&",
        "./docker_jupyter.sh",
        f"-p {port}",
    ]
    if kill_existing_jupyter:
        cmd.append("-f")
    cmd = " ".join(cmd)
    if not dry_run:
        if not kill_existing_jupyter:
            hdbg.dassert(
                not _is_port_in_use(port),
                "Port %s is in use: use --port or --kill_existing_jupyter",
                port,
            )
        if open_browser:
            thread = threading.Thread(
                target=_open_browser_when_ready, args=(url, port), daemon=True
            )
            thread.start()
    _run(cmd, dry_run=dry_run)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hparser.add_input_file_arg(
        parser,
        help_=(
            "Path of the notebook, relative to the git root or to the current "
            "dir (it can exist only on the branch)"
        ),
    )
    parser.add_argument(
        "--branch",
        action="store",
        required=True,
        help="Git branch with the notebook, with or without the `origin/` "
        "prefix, or URL of a GitHub PR "
        "(e.g., `https://github.com/<owner>/<repo>/pull/<n>`)",
    )
    parser.add_argument(
        "--worktree_dir",
        action="store",
        default=None,
        help="Dir of the new worktree, if the branch has no worktree yet "
        "(by default a sibling of the git root named `<repo>_<issue>`)",
    )
    parser.add_argument(
        "--port",
        action="store",
        type=int,
        default=8888,
        help="Host port for Jupyter Lab",
    )
    parser.add_argument(
        "--kill_existing_jupyter",
        action="store_true",
        help="Stop the Jupyter container already running for the project",
    )
    hparser.add_bool_arg(
        parser,
        "build",
        default_value=True,
        help_="Build the Docker image with `docker_build.sh` before starting",
    )
    hparser.add_bool_arg(
        parser,
        "open_browser",
        default_value=True,
        help_="Open the notebook in the browser when Jupyter Lab is ready",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    dry_run = args.dry_run
    git_root = hgit.find_git_root()
    # Accept a branch name or a PR URL.
    branch = _resolve_branch(args.branch, git_root=git_root)
    rel_notebook = _get_notebook_rel_path(args.input, git_root)
    # Get the branch. The fetch only updates the remote-tracking ref, so it is
    # run also in a dry run to be able to inspect the branch.
    _fetch_branch(branch, git_root=git_root)
    hdbg.dassert(
        hgit.exists_on_ref(f"origin/{branch}", rel_notebook, git_root=git_root),
        "Notebook '%s' not found on branch 'origin/%s'",
        rel_notebook,
        branch,
    )
    project_dir = _find_project_dir(branch, rel_notebook, git_root=git_root)
    _LOG.info("Project dir: '%s'", project_dir)
    # Get a worktree synced with the branch.
    cmd = f"git -C {shlex.quote(git_root)} worktree list --porcelain"
    _, txt = hsystem.system_to_string(cmd)
    worktree_dir = hgit.parse_worktree_list(txt, branch)
    if worktree_dir is None:
        worktree_dir = args.worktree_dir or hgit.get_default_worktree_dir(
            branch, git_root=git_root
        )
        worktree_dir = os.path.abspath(worktree_dir)
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=git_root,
            submodule_paths=[],
            dry_run=dry_run,
        )
    else:
        _LOG.info("Reusing worktree '%s' of branch '%s'", worktree_dir, branch)
        if args.worktree_dir:
            _LOG.warning("Ignoring --worktree_dir, since the worktree exists")
        hgit.sync_worktree(branch, worktree_dir, dry_run=dry_run)
    # Build the image and start Jupyter Lab from the project dir.
    abs_project_dir = os.path.join(worktree_dir, project_dir)
    if args.build:
        cmd = f"cd {shlex.quote(abs_project_dir)} && ./docker_build.sh"
        _run(cmd, dry_run=dry_run)
    url = _get_notebook_url(rel_notebook, args.port)
    _LOG.info("Notebook URL: %s", url)
    _LOG.info(
        "Stop with Ctrl+C. Remove the worktree with: git worktree remove '%s'",
        worktree_dir,
    )
    _start_jupyter(
        abs_project_dir,
        url,
        port=args.port,
        kill_existing_jupyter=args.kill_existing_jupyter,
        open_browser=args.open_browser,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
