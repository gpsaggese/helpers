#!/usr/bin/env python3

"""
Create a git worktree to work on (e.g., review) the branch of a GitHub PR.

The worktree is a sibling of the current client, named after the client dir with
its trailing digits replaced by the PR number. E.g., from `~/src/umd_classes3`
and the PR 888, the worktree is `~/src/umd_classes888`.

The PR is identified either by its URL (`--url`) or by its head branch
(`--branch`), optionally prefixed by the owner of the head repo, as in
`<owner>:<branch>`. The owner is needed to tell apart PRs from different forks
that use the same branch name.

Workflow:
1. Find the PR from its branch, if needed, parse the PR URL, and check that the
   PR belongs to the current repo
2. Create a detached worktree, then run `gh pr checkout` inside it, so that
   `gh` sets up the local branch and its upstream (also for PRs from forks)
3. Create a worktree of each submodule (e.g., `helpers_root`) of the worktree,
   at the commits recorded by the PR branch, unless `--no_submodules` is passed
   - The submodule worktrees share the objects with the submodules of the
     current client, so no new clone is needed
   - A submodule that the current client has not initialized is cloned instead
4. Create the script `git_worktree_remove.sh` in the worktree, and an identical
   copy `git_worktree_remove_<PR number>.sh` in the current client, that remove
   the worktree and its submodule worktrees
5. Print instructions for using the worktree

If the creation of the branch fails, the half-created worktree is removed.

# Usage Example

- Create the worktree for a PR:
> git_create_worktree_from_pr.py --url https://github.com/gpsaggese/umd_classes/pull/888

- Create the worktree for the PR opened from a fork:
> git_create_worktree_from_pr.py --branch MitaliPurwar21:UmdTask657_MSML610_Fall2026_WB_Weave_Project1_3_canonical_pr

- Create the worktree for the PR with a given branch:
> git_create_worktree_from_pr.py --branch UmdTask657_MSML610_Fall2026_WB_Weave_Project1_3_canonical_pr

- Create the worktree for a PR, leaving its submodules empty:
> git_create_worktree_from_pr.py --url https://github.com/gpsaggese/umd_classes/pull/888 --no_submodules

- Show what would be done, without doing it:
> git_create_worktree_from_pr.py --url https://github.com/gpsaggese/umd_classes/pull/888 --dry_run

Import as:

import dev_scripts_helpers.git.git_create_worktree_from_pr as dsggcwfp
"""

import argparse
import json
import logging
import os
import re
import shlex
from typing import Any, Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)

# #############################################################################
# URL parsing and naming
# #############################################################################


def _parse_pr_url(url: str) -> Tuple[str, int]:
    """
    Parse the URL of a GitHub PR.

    :param url: URL of a PR, with an optional trailing path, query, or anchor
        - E.g., `https://github.com/gpsaggese/umd_classes/pull/888`
        - E.g., `https://github.com/gpsaggese/umd_classes/pull/888/files`
    :return: full name of the repo (with host) and the PR number
        ```
        ("github.com/gpsaggese/umd_classes", 888)
        ```
    """
    _LOG.debug(hprint.to_str("url"))
    # Match a PR URL: host, owner login, repo name, PR number, and an optional
    # trailing path (e.g., `/files`), query, or anchor.
    _PR_URL_RE = re.compile(
        r"""
        ^https?://
        (?P<host>[^/]+)/          # host
        (?P<owner>[^/]+)/         # owner login
        (?P<repo>[^/]+)/          # repo name
        pull/(?P<number>\d+)      # PR number
        (?:[/?#].*)?$             # optional trailing path, query, or anchor
        """,
        re.VERBOSE,
    )
    match = _PR_URL_RE.match(url.strip())
    match = hdbg.dassert_re_match(
        match,
        "Can't parse '%s' as a PR URL like "
        "https://github.com/<owner>/<repo>/pull/<number>",
        url,
    )
    repo_full_name_with_host = "/".join(
        [match.group("host"), match.group("owner"), match.group("repo")]
    )
    pr_number = int(match.group("number"))
    _LOG.debug("return=%s", (repo_full_name_with_host, pr_number))
    return repo_full_name_with_host, pr_number


def _parse_branch_spec(branch_spec: str) -> Tuple[str, str]:
    """
    Parse the spec of the head branch of a PR.

    A colon is not allowed in the name of a git branch, so it is safe to use it
    as a separator between the owner of the head repo and the branch.

    :param branch_spec: branch, optionally prefixed by the owner of the head repo
        - E.g., `MitaliPurwar21:UmdTask657_canonical_pr`
        - E.g., `UmdTask657_canonical_pr`
    :return: owner (empty string if not specified) and branch name
        ```
        ("MitaliPurwar21", "UmdTask657_canonical_pr")
        ("", "UmdTask657_canonical_pr")
        ```
    """
    _LOG.debug(hprint.to_str("branch_spec"))
    branch_spec = branch_spec.strip()
    owner, sep, branch = branch_spec.rpartition(":")
    if not sep:
        # There is no owner, e.g., `UmdTask657_canonical_pr`.
        owner, branch = "", branch_spec
    hdbg.dassert_ne(branch, "", "Empty branch in spec '%s'", branch_spec)
    _LOG.debug("return=%s", (owner, branch))
    return owner, branch


def _select_pr_url(prs: List[Dict[str, Any]], owner: str, branch: str) -> str:
    """
    Select the PR to use among the PRs with a given head branch.

    :param prs: PRs as returned by `gh pr list --json url,headRepositoryOwner`
    :param owner: owner of the head repo, or empty string to accept any owner
    :param branch: head branch, used only in the messages
    :return: URL of the only PR matching the owner
    """
    _LOG.debug(hprint.to_str("owner branch"))
    if owner:
        # A fork can have a branch with the same name as the one in the repo.
        prs = [
            pr
            for pr in prs
            if (pr.get("headRepositoryOwner") or {}).get("login") == owner
        ]
    spec = f"{owner}:{branch}" if owner else branch
    hdbg.dassert_lt(
        0, len(prs), "Can't find an open PR with head branch '%s'", spec
    )
    pr_urls = [pr["url"] for pr in prs]
    hdbg.dassert_eq(
        len(pr_urls),
        1,
        "Multiple open PRs have head branch '%s', use `<owner>:<branch>`: %s",
        spec,
        ", ".join(pr_urls),
    )
    pr_url = pr_urls[0]
    _LOG.debug("return=%s", pr_url)
    return pr_url


def _get_pr_url_from_branch(
    repo_full_name_with_host: str, branch_spec: str
) -> str:
    """
    Find the URL of the open PR with a given head branch.

    :param repo_full_name_with_host: repo where the PR was opened
        - E.g., `github.com/gpsaggese/umd_classes`
    :param branch_spec: branch, optionally prefixed by the owner of the head
        repo (see `_parse_branch_spec()`)
    :return: URL of the PR
    """
    _LOG.debug(hprint.to_str("repo_full_name_with_host branch_spec"))
    owner, branch = _parse_branch_spec(branch_spec)
    # `gh pr list --head` accepts only the branch name, so filter the owner of
    # the head repo (i.e., the fork) on our side.
    cmd = [
        f"gh pr list --repo {shlex.quote(repo_full_name_with_host)}",
        f"--head {shlex.quote(branch)}",
        "--json url,headRepositoryOwner",
    ]
    cmd = " ".join(cmd)
    _, output = hsystem.system_to_string(cmd)
    prs = json.loads(output)
    pr_url = _select_pr_url(prs, owner, branch)
    _LOG.info("Branch '%s' -> PR '%s'", branch_spec, pr_url)
    return pr_url


def _get_worktree_path(client_root: str, pr_number: int) -> str:
    """
    Return the path of the worktree for a PR.

    The worktree name is the client dir name without its trailing digits,
    followed by the PR number.

    :param client_root: root of the current client
        - E.g., `/Users/user/src/umd_classes3`
    :param pr_number: PR number
    :return: sibling dir of the client
        - E.g., `/Users/user/src/umd_classes888`
    """
    _LOG.debug(hprint.to_str("client_root pr_number"))
    parent_dir = os.path.dirname(client_root)
    client_name = os.path.basename(client_root)
    # Remove the digits that index the client (e.g., "umd_classes3").
    base_name = re.sub(r"\d+$", "", client_name)
    hdbg.dassert_ne(
        base_name,
        "",
        "Can't build a worktree name from client dir '%s'",
        client_name,
    )
    worktree_path = os.path.join(parent_dir, f"{base_name}{pr_number}")
    _LOG.debug("return=%s", worktree_path)
    return worktree_path


# #############################################################################
# Git and GitHub
# #############################################################################


def _get_pr_branch(pr_url: str) -> str:
    """
    Get the name of the head branch of a PR.

    :param pr_url: URL of the PR
    :return: branch name, e.g., `HelpersTask1451_Implement_tools_1`
    """
    _LOG.debug(hprint.to_str("pr_url"))
    cmd = [
        f"gh pr view {shlex.quote(pr_url)}",
        "--json headRefName",
        "-q .headRefName",
    ]
    cmd = " ".join(cmd)
    _, branch_name = hsystem.system_to_one_line(cmd)
    hdbg.dassert_ne(branch_name, "", "Can't find the branch of PR '%s'", pr_url)
    _LOG.debug("return=%s", branch_name)
    return branch_name


def _get_checked_out_branches(client_root: str) -> List[str]:
    """
    Get the branches checked out in any worktree of the client.

    :param client_root: root of the current client
    :return: branch names, e.g., `["master", "Task1_foo"]`
    """
    _LOG.debug(hprint.to_str("client_root"))
    cmd = f"git -C {shlex.quote(client_root)} worktree list --porcelain"
    _, output = hsystem.system_to_string(cmd)
    # The output has a line `branch refs/heads/<name>` per worktree on a branch.
    prefix = "branch refs/heads/"
    branches = [
        line[len(prefix) :]
        for line in output.splitlines()
        if line.startswith(prefix)
    ]
    _LOG.debug("return=%s", branches)
    return branches


def _create_worktree(
    client_root: str, pr_url: str, worktree_path: str, *, dry_run: bool = False
) -> None:
    """
    Create a worktree on the branch of a PR.

    The worktree is created detached and then switched to the PR branch with
    `gh pr checkout`, which also works for PRs from forks. If the checkout
    fails, the worktree is removed.

    :param client_root: root of the current client
    :param pr_url: URL of the PR
    :param worktree_path: path of the worktree to create
    :param dry_run: if True, only report the commands
    """
    _LOG.debug(hprint.to_str("client_root pr_url worktree_path dry_run"))
    quoted_client = shlex.quote(client_root)
    quoted_path = shlex.quote(worktree_path)
    # Create the worktree detached, since the PR branch is not known locally.
    create_cmd = " ".join(
        [
            f"git -C {quoted_client}",
            f"worktree add --detach {quoted_path}",
        ]
    )
    # Let `gh` create the local branch and set its upstream.
    checkout_cmd = " ".join(
        [
            f"cd {quoted_path} &&",
            f"gh pr checkout {shlex.quote(pr_url)}",
        ]
    )
    if dry_run:
        _LOG.warning("[DRY_RUN] Would run: %s", create_cmd)
        _LOG.warning("[DRY_RUN] Would run: %s", checkout_cmd)
        return
    _LOG.info("Creating worktree at '%s'", worktree_path)
    hsystem.system(create_cmd, log_level=logging.INFO)
    rc = hsystem.system(
        checkout_cmd, abort_on_error=False, log_level=logging.INFO
    )
    if rc != 0:
        # Don't leave a worktree on a detached HEAD behind.
        _LOG.error(
            "Checkout of '%s' failed, removing worktree '%s'",
            pr_url,
            worktree_path,
        )
        remove_cmd = " ".join(
            [
                f"git -C {quoted_client}",
                f"worktree remove --force {quoted_path}",
            ]
        )
        hsystem.system(remove_cmd, log_level=logging.INFO)
        raise RuntimeError(f"Can't check out PR '{pr_url}', rc={rc}")


def _parse_gitlinks(ls_files_output: str) -> List[Tuple[str, str]]:
    """
    Parse the submodules recorded in a repo.

    :param ls_files_output: output of `git ls-files --stage`, where a submodule
        has mode `160000`
        ```
        100644 8e3a6c1 0\tREADME.md
        160000 98eef91 0\thelpers_root
        ```
    :return: path and commit of each submodule
        ```
        [("helpers_root", "98eef91")]
        ```
    """
    _LOG.debug(hprint.to_str("ls_files_output"))
    gitlinks = []
    for line in ls_files_output.splitlines():
        meta, _, path = line.partition("\t")
        mode, commit, _ = meta.split()
        if mode == "160000":
            gitlinks.append((path, commit))
    _LOG.debug("return=%s", gitlinks)
    return gitlinks


def _fetch_commit_if_missing(repo_dir: str, commit: str) -> None:
    """
    Fetch from the remote the commit of a submodule, if it is not local.

    A PR can point a submodule to a commit that the client doesn't have yet.

    :param repo_dir: dir of the (sub)module repo
    :param commit: commit that must be available
    """
    _LOG.debug(hprint.to_str("repo_dir commit"))
    quoted_dir = shlex.quote(repo_dir)
    cmd = f"git -C {quoted_dir} cat-file -e {commit}^{{commit}}"
    rc = hsystem.system(cmd, abort_on_error=False)
    if rc != 0:
        _LOG.info("Commit '%s' not in '%s', fetching it", commit, repo_dir)
        hsystem.system(
            f"git -C {quoted_dir} fetch origin", log_level=logging.INFO
        )


def _create_submodule_worktrees(
    src_dir: str, worktree_path: str
) -> List[Tuple[str, str]]:
    """
    Create a worktree of each submodule of a worktree, recursively.

    A worktree of a submodule shares the objects with the submodule of the
    client, so it is fast and it doesn't need the network, unless the PR points
    to a commit that the client doesn't have. Each submodule lands on the
    commit recorded by the PR branch, with a detached HEAD.

    If the client has not initialized a submodule, we can't create a worktree
    of it, so we fall back to initializing it with a separate clone.

    :param src_dir: dir of the repo (the client or one of its submodules) that
        is the source of `worktree_path`
    :param worktree_path: path of the worktree of `src_dir`
    :return: source dir and worktree dir of each created submodule worktree,
        with each submodule before its nested ones
        ```
        [("/src/umd_classes3/helpers_root", "/src/umd_classes888/helpers_root")]
        ```
    """
    _LOG.debug(hprint.to_str("src_dir worktree_path"))
    cmd = f"git -C {shlex.quote(worktree_path)} ls-files --stage"
    _, output = hsystem.system_to_string(cmd)
    submodule_worktrees = []
    for path, commit in _parse_gitlinks(output):
        src_submodule_dir = os.path.join(src_dir, path)
        worktree_submodule_dir = os.path.join(worktree_path, path)
        if os.path.exists(os.path.join(src_submodule_dir, ".git")):
            # Reuse the repo of the submodule in the client. The empty dir of
            # the submodule in the worktree is accepted by `git worktree add`.
            _fetch_commit_if_missing(src_submodule_dir, commit)
            create_cmd = " ".join(
                [
                    f"git -C {shlex.quote(src_submodule_dir)}",
                    "worktree add --detach",
                    shlex.quote(worktree_submodule_dir),
                    commit,
                ]
            )
            _LOG.info("Creating worktree at '%s'", worktree_submodule_dir)
            hsystem.system(create_cmd, log_level=logging.INFO)
            submodule_worktrees.append(
                (src_submodule_dir, worktree_submodule_dir)
            )
            # Handle the submodules of the submodule.
            submodule_worktrees.extend(
                _create_submodule_worktrees(
                    src_submodule_dir, worktree_submodule_dir
                )
            )
        else:
            _LOG.warning(
                "Submodule '%s' is not initialized in '%s', cloning it",
                path,
                src_dir,
            )
            clone_cmd = " ".join(
                [
                    f"git -C {shlex.quote(worktree_path)}",
                    "submodule update --init --recursive",
                    f"-- {shlex.quote(path)}",
                ]
            )
            hsystem.system(clone_cmd, log_level=logging.INFO)
    _LOG.debug("return=%s", submodule_worktrees)
    return submodule_worktrees


def _get_remove_script(
    client_root: str,
    worktree_path: str,
    script_paths: List[str],
    submodule_worktrees: List[Tuple[str, str]],
) -> str:
    """
    Build the bash script that removes a worktree and its submodule worktrees.

    The script uses only absolute paths, so it works from any dir and from any
    of its copies.

    :param client_root: root of the client the worktree was created from
    :param worktree_path: path of the worktree
    :param script_paths: paths of the copies of the script, which the script
        deletes
    :param submodule_worktrees: source dir and worktree dir of each submodule
        worktree, as returned by `_create_submodule_worktrees()`
    :return: content of the script
    """
    _LOG.debug(hprint.to_str("client_root worktree_path script_paths"))
    quote = shlex.quote
    header = f'''
    #!/bin/bash
    # """
    # Remove the worktree {quote(worktree_path)} created by
    # `git_create_worktree_from_pr.py`.
    # """

    set -e

    # Run from the client, since the dir of the worktree is deleted.
    cd {quote(client_root)}
    '''
    sections = [hprint.dedent(header)]
    if submodule_worktrees:
        # Git refuses to remove a worktree with a populated submodule. So remove
        # the worktree of each submodule, nested ones first, and restore its
        # empty dir, to leave the outer worktree clean.
        cmds = []
        for src_dir, submodule_dir in reversed(submodule_worktrees):
            cmds.append(
                f"git -C {quote(src_dir)} worktree remove {quote(submodule_dir)}"
            )
            cmds.append(f"mkdir {quote(submodule_dir)}")
        sections.append(
            "# Remove the worktree of each submodule, nested ones first. Git\n"
            "# refuses to remove a worktree with a populated submodule, so\n"
            "# restore its empty dir.\n" + "\n".join(cmds)
        )
    footer = f"""
    # Remove the copies of this script, since Git refuses to remove a worktree
    # with untracked files.
    rm -f {" ".join(quote(path) for path in script_paths)}

    # Remove the worktree.
    git worktree remove {quote(worktree_path)}
    """
    sections.append(hprint.dedent(footer))
    script = "\n\n".join(sections) + "\n"
    _LOG.debug("return=%s", script)
    return script


def _create_remove_scripts(
    client_root: str,
    worktree_path: str,
    pr_number: int,
    submodule_worktrees: List[Tuple[str, str]],
) -> List[str]:
    """
    Create two identical scripts that remove the worktree.

    One script is in the worktree and one in the client the worktree was
    created from, so that the removal can be run from either place. The copy in
    the client has the PR number in its name, to tell apart the worktrees.

    :param client_root: root of the client the worktree was created from
    :param worktree_path: path of the worktree
    :param pr_number: PR number
    :param submodule_worktrees: source dir and worktree dir of each submodule
        worktree, as returned by `_create_submodule_worktrees()`
    :return: paths of the scripts in the worktree and in the client
    """
    _LOG.debug(hprint.to_str("client_root worktree_path pr_number"))
    script_paths = [
        os.path.join(worktree_path, "git_worktree_remove.sh"),
        os.path.join(client_root, f"git_worktree_remove_{pr_number}.sh"),
    ]
    script = _get_remove_script(
        client_root, worktree_path, script_paths, submodule_worktrees
    )
    for script_path in script_paths:
        hio.to_file(script_path, script)
        os.chmod(script_path, 0o755)
        _LOG.info("Created '%s'", script_path)
    return script_paths


def _get_tmux_script(worktree_path: str, dir_suffix: str) -> str:
    """
    Return the path of the `tmux.py` script of the repo, relative to the worktree.

    Each repo has its own copy of the thin client scripts in
    `dev_scripts_{dir_suffix}/thin_client/` (e.g., in `umd_classes` it is a
    symlink to the one in `helpers_root`), so the one of `helpers` is not
    always the right one.

    :param worktree_path: path of the worktree
    :param dir_suffix: suffix of the `dev_scripts_{dir_suffix}` dir of the repo,
        as returned by `RepoConfig.get_dir_suffix()`
    :return: path of `tmux.py` relative to the worktree
    """
    tmux_script = os.path.join(
        f"dev_scripts_{dir_suffix}", "thin_client", "tmux.py"
    )
    if not os.path.exists(os.path.join(worktree_path, tmux_script)):
        # This is only advice in a message, so don't fail.
        _LOG.warning(
            "Can't find '%s' in the worktree '%s'", tmux_script, worktree_path
        )
    return tmux_script


def _print_usage_instructions(
    worktree_path: str,
    pr_number: int,
    branch_name: str,
    tmux_script: str,
    script_paths: List[str],
) -> None:
    """
    Print instructions on how to use the created worktree.

    :param worktree_path: path of the worktree
    :param pr_number: PR number
    :param branch_name: branch checked out in the worktree
    :param tmux_script: path of `tmux.py` relative to the worktree, as returned
        by `_get_tmux_script()`
    :param script_paths: paths of the scripts that remove the worktree, as
        returned by `_create_remove_scripts()`
    """
    _LOG.debug(
        hprint.to_str(
            "worktree_path pr_number branch_name tmux_script script_paths"
        )
    )
    remove_txt = "\n".join(f"> {path}" for path in script_paths)
    msg = f"""
    Worktree created successfully for PR #{pr_number} on branch '{branch_name}'!

    To open tmux session:
    > cd {worktree_path}; {tmux_script} --index {pr_number}

    To remove the worktree, run one of these identical scripts:
    """
    msg = hprint.dedent(msg) + "\n" + remove_txt
    msg = hprint.color_highlight(msg, "green")
    print(msg)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # The PR is identified either by its URL or by its head branch.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--url",
        type=str,
        default="",
        help=(
            "URL of the GitHub PR, e.g., "
            "https://github.com/gpsaggese/umd_classes/pull/888"
        ),
    )
    group.add_argument(
        "--branch",
        type=str,
        default="",
        help=(
            "Head branch of an open PR of the current repo, optionally "
            "prefixed by the owner of the head repo (e.g., a fork), e.g., "
            "MitaliPurwar21:UmdTask657_canonical_pr or UmdTask657_canonical_pr"
        ),
    )
    hparser.add_bool_arg(
        parser,
        "submodules",
        default_value=True,
        help_=(
            "Also create a worktree of every submodule, at the commit "
            "recorded by the PR branch. With --no_submodules, operate on the "
            "outer repo only, leaving the submodules empty"
        ),
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Use the repo of the current dir, even when it is a submodule (e.g.,
    # `helpers_root`), and not its super-module, since the PR must be in the repo
    # we are running in.
    client_root = hgit.get_client_root(super_module=False)
    client_repo = hgit.get_repo_full_name_from_dirname(
        client_root, include_host_name=True
    )
    if args.url:
        pr_url = args.url
    else:
        # Look for the PR in the repo of the client.
        pr_url = _get_pr_url_from_branch(client_repo, args.branch)
    repo_full_name_with_host, pr_number = _parse_pr_url(pr_url)
    # The PR branch must exist in the repo of the client.
    hdbg.dassert_eq(
        repo_full_name_with_host,
        client_repo,
        "The PR is not in the repo of the current dir '%s'",
        client_root,
    )
    worktree_path = _get_worktree_path(client_root, pr_number)
    hdbg.dassert_path_not_exists(
        worktree_path, "The worktree for the PR already exists"
    )
    branch_name = _get_pr_branch(pr_url)
    # A branch can be checked out in only one worktree.
    hdbg.dassert_not_in(
        branch_name,
        _get_checked_out_branches(client_root),
        "Branch '%s' is already checked out in another worktree",
        branch_name,
    )
    _LOG.info(
        "PR #%s -> branch '%s' -> worktree '%s'",
        pr_number,
        branch_name,
        worktree_path,
    )
    _create_worktree(client_root, pr_url, worktree_path, dry_run=args.dry_run)
    submodule_worktrees: List[Tuple[str, str]] = []
    if args.submodules:
        if args.dry_run:
            # The worktree does not exist yet, so we can't tell if it has
            # submodules.
            _LOG.warning(
                "[DRY_RUN] Would create a worktree of each submodule of '%s', "
                "if any",
                worktree_path,
            )
        else:
            submodule_worktrees = _create_submodule_worktrees(
                client_root, worktree_path
            )
    if not args.dry_run:
        script_paths = _create_remove_scripts(
            client_root, worktree_path, pr_number, submodule_worktrees
        )
        # The worktree has the layout of the current repo, so use its suffix.
        dir_suffix = hrecouti.get_repo_config().get_dir_suffix()
        tmux_script = _get_tmux_script(worktree_path, dir_suffix)
        _print_usage_instructions(
            worktree_path, pr_number, branch_name, tmux_script, script_paths
        )


if __name__ == "__main__":
    _main(_parse())
