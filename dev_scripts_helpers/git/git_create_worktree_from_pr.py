#!/usr/bin/env python3

"""
Create a git worktree to work on (e.g., review) the branch of a GitHub PR.

The worktree is a sibling of the current client, named after the client dir with
its trailing digits replaced by the PR number. E.g., from `~/src/umd_classes3`
and the PR 888, the worktree is `~/src/umd_classes888`.

Workflow:
1. Parse the PR URL and check that the PR belongs to the current repo
2. Create a detached worktree, then run `gh pr checkout` inside it, so that
   `gh` sets up the local branch and its upstream (also for PRs from forks)
3. Initialize the submodules (e.g., `helpers_root`) in the worktree, at the
   commits recorded by the PR branch, only if `--submodules` is passed
4. Print instructions for using the worktree

If the creation of the branch fails, the half-created worktree is removed.

# Usage Example

- Create the worktree for a PR:
> git_create_worktree_from_pr.py --url https://github.com/gpsaggese/umd_classes/pull/888

- Create the worktree for a PR and also initialize its submodules:
> git_create_worktree_from_pr.py --url https://github.com/gpsaggese/umd_classes/pull/888 --submodules

- Show what would be done, without doing it:
> git_create_worktree_from_pr.py --url https://github.com/gpsaggese/umd_classes/pull/888 --dry_run

Import as:

import dev_scripts_helpers.git.git_create_worktree_from_pr as dsggcwfp
"""

import argparse
import logging
import os
import re
import shlex
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

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
    rc = hsystem.system(checkout_cmd, abort_on_error=False, log_level=logging.INFO)
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


def _init_submodules(worktree_path: str, *, dry_run: bool = False) -> None:
    """
    Initialize the submodules of the worktree, if any.

    Each submodule lands on the commit recorded by the PR branch.

    :param worktree_path: path of the worktree
    :param dry_run: if True, only report the command
    """
    _LOG.debug(hprint.to_str("worktree_path dry_run"))
    cmd = " ".join(
        [
            f"git -C {shlex.quote(worktree_path)}",
            "submodule update --init --recursive",
        ]
    )
    if dry_run:
        # The worktree does not exist yet, so we can't tell if it has submodules.
        _LOG.warning("[DRY_RUN] Would run, if there are submodules: %s", cmd)
    elif os.path.exists(os.path.join(worktree_path, ".gitmodules")):
        _LOG.info("Initializing submodules in '%s'", worktree_path)
        hsystem.system(cmd, log_level=logging.INFO)
    else:
        _LOG.debug("No submodules in '%s'", worktree_path)


def _print_usage_instructions(
    worktree_path: str, pr_number: int, branch_name: str
) -> None:
    """
    Print instructions on how to use the created worktree.

    :param worktree_path: path of the worktree
    :param pr_number: PR number
    :param branch_name: branch checked out in the worktree
    """
    _LOG.debug(hprint.to_str("worktree_path pr_number branch_name"))
    msg = f"""
    Worktree created successfully for PR #{pr_number} on branch '{branch_name}'!

    To open tmux session:
    > cd {worktree_path}; dev_scripts_helpers/thin_client/tmux.py --index {pr_number}

    To remove the worktree:
    > git worktree remove {worktree_path}
    """
    msg = hprint.dedent(msg)
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
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help=(
            "URL of the GitHub PR, e.g., "
            "https://github.com/gpsaggese/umd_classes/pull/888"
        ),
    )
    parser.add_argument(
        "--submodules",
        action="store_true",
        default=False,
        help=(
            "Enable submodule handling: also initialize every submodule in "
            "the worktree, if present. Default: operate on the outer repo "
            "only, leaving the submodules uninitialized"
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
    repo_full_name_with_host, pr_number = _parse_pr_url(args.url)
    # The PR branch must exist in the repo of the client.
    client_root = hgit.get_client_root(super_module=True)
    client_repo = hgit.get_repo_full_name_from_dirname(
        client_root, include_host_name=True
    )
    hdbg.dassert_eq(
        repo_full_name_with_host,
        client_repo,
        "The PR is in a different repo than the client '%s'",
        client_root,
    )
    worktree_path = _get_worktree_path(client_root, pr_number)
    hdbg.dassert_path_not_exists(
        worktree_path, "The worktree for the PR already exists"
    )
    branch_name = _get_pr_branch(args.url)
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
    _create_worktree(
        client_root, args.url, worktree_path, dry_run=args.dry_run
    )
    if args.submodules:
        _init_submodules(worktree_path, dry_run=args.dry_run)
    if not args.dry_run:
        _print_usage_instructions(worktree_path, pr_number, branch_name)


if __name__ == "__main__":
    _main(_parse())
