#!/usr/bin/env python

"""
Create a Git worktree for an existing branch / PR and open a tmux session on it.

The script operates on the repo of the current dir (e.g., run it from
`helpers_root` to work on a `helpers` PR), or on the repo passed with
`--repo_short_name`, which is the `repo_name` in `repo_config.yaml` of the
outermost repo or of one of its submodules (e.g., `helpers`). A PR number refers
to the PR numbering of that repo.

The worktree is created in `$AM_SRC_DIR` (or `~/src`) as
`<dir_suffix>_worktree_<issue_id>` (e.g., `helpers_worktree_1354`), so that
the `thin_client/tmux.py` of the repo can build the tmux session on top of it
(windows `dbash1..3`, `regr`, `jupyter`).

If the worktree already exists it is reused, so the script can also be used to
re-open the tmux session.

Run it outside tmux: inside tmux it only creates the worktree and prints the
command to run to open the session.

# Usage Example

- Create the worktree and the tmux session for a PR:
> git_worktree_tmux.py --pr_number 1355

- Create the worktree and the tmux session for a branch:
> git_worktree_tmux.py --branch_name HelpersTask1354_Improve_bookmarking_flow

- Do it for a PR of the `helpers` submodule from anywhere in the outer repo:
> git_worktree_tmux.py --repo_short_name helpers --pr_number 1355

- Show what would be done without doing it:
> git_worktree_tmux.py --pr_number 1355 --dry_run

Import as:

import dev_scripts_helpers.git.git_worktree_tmux as dsggwt
"""

import argparse
import logging
import os
import shlex
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helpers
# #############################################################################


def _get_repo_dir(repo_short_name: str) -> str:
    """
    Return the root dir of the repo that owns the branch / PR.

    :param repo_short_name: short name of the repo
        - `current`: the repo of the current dir (a submodule, if we are in one)
        - Otherwise the `repo_name` in `repo_config.yaml` of the outermost repo
          or of one of its submodules, e.g., `helpers`
    :return: root dir of the repo
    """
    _LOG.debug(hprint.to_str("repo_short_name"))
    if repo_short_name == "current":
        repo_dir = hgit.get_client_root(super_module=False)
    else:
        # Collect the repos that can be reached: the outermost repo and its
        # submodules.
        outer_dir = hgit.find_git_root()
        # E.g., `submodule.helpers_root.path helpers_root`.
        cmd = f"git -C {outer_dir} config --file .gitmodules --get-regexp path"
        rc, txt = hsystem.system_to_string(cmd, abort_on_error=False)
        candidate_dirs = [outer_dir]
        if rc == 0:
            for line in txt.splitlines():
                candidate_dirs.append(os.path.join(outer_dir, line.split()[1]))
        # Find the repo with the requested short name.
        repo_dir = ""
        for candidate_dir in candidate_dirs:
            config_file = os.path.join(candidate_dir, "repo_config.yaml")
            if not os.path.exists(config_file):
                continue
            repo_config = hrecouti.RepoConfig.from_file(config_file)
            if repo_config.get_repo_short_name() == repo_short_name:
                repo_dir = candidate_dir
                break
        hdbg.dassert_ne(
            repo_dir,
            "",
            "Cannot find a repo named '%s' among '%s'",
            repo_short_name,
            candidate_dirs,
        )
    _LOG.debug("return=%s", repo_dir)
    return repo_dir


def _get_branch_name(branch_name: str, pr_number: int) -> str:
    """
    Return the name of the branch to open, resolving it from the PR if needed.

    :param branch_name: name of the branch or `""` if a PR is passed
    :param pr_number: number of the PR or `0` if a branch is passed
    :return: name of the branch, e.g., `HelpersTask1354_Improve_bookmarking_flow`
    """
    _LOG.debug(hprint.to_str("branch_name pr_number"))
    if pr_number > 0:
        # Ask GitHub for the head branch of the PR.
        cmd = f"gh pr view {pr_number} --json headRefName -q .headRefName"
        _, branch_name = hsystem.system_to_one_line(cmd)
    hdbg.dassert_ne(branch_name, "", "Cannot find the name of the branch")
    _LOG.debug("return=%s", branch_name)
    return branch_name


def _get_worktree_names(
    branch_name: str, dir_suffix: str, src_dir: str
) -> Tuple[str, str]:
    """
    Return the dir of the worktree and the index to pass to `tmux.py`.

    E.g., `HelpersTask1354_Improve_bookmarking_flow`, `helpers`, and `/src` are
    mapped to
    ```
    ('/src/helpers_worktree_1354', '_worktree_1354')
    ```

    :param branch_name: name of the branch, which includes the issue number
    :param dir_suffix: suffix of the `dev_scripts_<dir_suffix>` dir of the repo
    :param src_dir: dir containing the clients of the repo
    :return: dir of the worktree and index of the tmux session
    """
    _LOG.debug(hprint.to_str("branch_name dir_suffix src_dir"))
    issue_id = hgit.extract_gh_issue_number_from_branch(branch_name)
    hdbg.dassert_is_not(
        issue_id,
        None,
        "Cannot extract the issue number from branch '%s'",
        branch_name,
    )
    # `tmux.py` names the session `<dir_suffix><index>` and looks for the client
    # in `<src_dir>/<dir_suffix><index>`, so the worktree must follow this
    # pattern.
    index = f"_worktree_{issue_id}"
    worktree_dir = os.path.join(src_dir, f"{dir_suffix}{index}")
    _LOG.debug("return=%s", (worktree_dir, index))
    return worktree_dir, index


def _create_worktree(
    branch_name: str, worktree_dir: str, *, dry_run: bool
) -> None:
    """
    Create the worktree for a branch, unless it already exists.

    :param branch_name: name of the branch to check out in the worktree
    :param worktree_dir: dir of the worktree to create
    :param dry_run: print the commands without executing them
    """
    _LOG.debug(hprint.to_str("branch_name worktree_dir dry_run"))
    if os.path.exists(worktree_dir):
        _LOG.warning("Worktree '%s' already exists: reusing it", worktree_dir)
        return
    quoted_branch = shlex.quote(branch_name)
    # Make the remote branch of the PR visible locally.
    cmd = f"git fetch origin {quoted_branch}"
    hsystem.system(cmd, dry_run=dry_run, log_level=logging.INFO)
    # Reuse the local branch if there is one, otherwise create one that tracks
    # the remote branch.
    cmd = f"git show-ref --verify --quiet refs/heads/{quoted_branch}"
    rc, _ = hsystem.system_to_string(cmd, abort_on_error=False)
    if rc == 0:
        cmd = f"git worktree add {worktree_dir} {quoted_branch}"
    else:
        cmd = (
            f"git worktree add --track -b {quoted_branch} {worktree_dir} "
            f"origin/{quoted_branch}"
        )
    hsystem.system(cmd, dry_run=dry_run, log_level=logging.INFO)
    # A new worktree has empty submodule dirs: fill them.
    if hgit.get_submodule_paths():
        cmd = f"git -C {worktree_dir} submodule update --init --recursive"
        hsystem.system(cmd, dry_run=dry_run, log_level=logging.INFO)


def _open_tmux(
    worktree_dir: str,
    dir_suffix: str,
    index: str,
    log_level: str,
    *,
    dry_run: bool,
) -> None:
    """
    Open the tmux session on the worktree using the `tmux.py` of the repo.

    :param worktree_dir: dir of the worktree
    :param dir_suffix: suffix of the `dev_scripts_<dir_suffix>` dir of the repo
    :param index: index of the tmux session
    :param log_level: verbosity to forward to `tmux.py`
    :param dry_run: print the command without executing it
    """
    _LOG.debug(hprint.to_str("worktree_dir dir_suffix index log_level dry_run"))
    tmux_script = os.path.join(
        worktree_dir, f"dev_scripts_{dir_suffix}", "thin_client", "tmux.py"
    )
    cmd = [
        tmux_script,
        f"--index {index}",
        f"-v {log_level}",
    ]
    cmd = " ".join(cmd)
    cmd = f"cd {worktree_dir} && {cmd}"
    if dry_run:
        _LOG.warning("[DRY_RUN] Would run '%s'", cmd)
    elif "TMUX" in os.environ:
        # `tmux.py` refuses to run inside tmux.
        _LOG.warning(
            "Inside tmux: run this command from a terminal outside tmux:\n%s",
            cmd,
        )
    else:
        hdbg.dassert_file_exists(tmux_script)
        # Replace this process with `tmux.py`, so that `tmux attach` owns the
        # terminal.
        os.chdir(worktree_dir)
        os.execv(tmux_script, [tmux_script, "--index", index, "-v", log_level])


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--branch_name",
        action="store",
        type=str,
        default="",
        help="Name of the existing branch to open",
    )
    group.add_argument(
        "--pr_number",
        action="store",
        type=int,
        default=0,
        help="Number of the PR whose branch to open",
    )
    parser.add_argument(
        "--repo_short_name",
        action="store",
        type=str,
        default="current",
        help="Short name of the repo that owns the branch / PR (e.g., helpers)",
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
    # Work in the repo of the current dir (a submodule, if we are in one), since
    # the branch lives there.
    repo_root = _get_repo_dir(args.repo_short_name)
    os.chdir(repo_root)
    dir_suffix = hrecouti.get_repo_config().get_dir_suffix()
    _LOG.info("repo_root='%s' dir_suffix='%s'", repo_root, dir_suffix)
    # Find what to create.
    branch_name = _get_branch_name(args.branch_name, args.pr_number)
    src_dir = os.environ.get("AM_SRC_DIR", os.path.expanduser("~/src"))
    worktree_dir, index = _get_worktree_names(branch_name, dir_suffix, src_dir)
    _LOG.info("branch_name='%s' worktree_dir='%s'", branch_name, worktree_dir)
    # Create the worktree and the tmux session on it.
    _create_worktree(branch_name, worktree_dir, dry_run=args.dry_run)
    _open_tmux(
        worktree_dir, dir_suffix, index, args.log_level, dry_run=args.dry_run
    )


if __name__ == "__main__":
    _main(_parse())
