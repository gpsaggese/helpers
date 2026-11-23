"""
Import as:

import dev_scripts_helpers.git.test.test_git_create_worktree_from_pr as dsggtgcwfp
"""

import logging
import os
import unittest.mock as umock
from typing import Any, Dict, List, Tuple

import dev_scripts_helpers.git.git_create_worktree_from_pr as dsggcwfp
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_pr_url
# #############################################################################


class Test_parse_pr_url(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._parse_pr_url()`.
    """

    def helper(self, url: str, expected: str) -> None:
        """
        Parse `url` and compare the repo and the PR number with `expected`.

        :param url: URL of the PR
        :param expected: expected repo and PR number, as `<repo> <number>`
        """
        # Run test.
        repo, pr_number = dsggcwfp._parse_pr_url(url)
        # Check outputs.
        actual = f"{repo} {pr_number}"
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a plain PR URL.
        """
        # Prepare inputs.
        url = "https://github.com/gpsaggese/gpsaggese.github.io/pull/888"
        # Prepare outputs.
        expected = "github.com/gpsaggese/gpsaggese.github.io 888"
        # Run test.
        self.helper(url, expected)

    def test2(self) -> None:
        """
        Test a PR URL pointing to a sub-page, with a query and an anchor.
        """
        # Prepare inputs.
        url = "https://github.com/gpsaggese/helpers/pull/1451/files?w=1#diff-1"
        # Prepare outputs.
        expected = "github.com/gpsaggese/helpers 1451"
        # Run test.
        self.helper(url, expected)

    def test3(self) -> None:
        """
        Test a PR URL with surrounding whitespace.
        """
        # Prepare inputs.
        url = "  https://github.com/gpsaggese/helpers/pull/7\n"
        # Prepare outputs.
        expected = "github.com/gpsaggese/helpers 7"
        # Run test.
        self.helper(url, expected)

    def test4(self) -> None:
        """
        Test that an issue URL is rejected.
        """
        # Prepare inputs.
        url = "https://github.com/gpsaggese/helpers/issues/1451"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsggcwfp._parse_pr_url(url)
        # Check outputs.
        self.assertIn("Can't parse", str(cm.exception))


# #############################################################################
# Test_parse_branch_spec
# #############################################################################


class Test_parse_branch_spec(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._parse_branch_spec()`.
    """

    def helper(self, branch_spec: str, expected: Tuple[str, str]) -> None:
        """
        Parse `branch_spec` and compare the owner and branch with `expected`.

        :param branch_spec: branch, optionally prefixed by the owner
        :param expected: expected owner and branch
        """
        # Run test.
        actual = dsggcwfp._parse_branch_spec(branch_spec)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test a branch prefixed by the owner of the head repo.
        """
        # Prepare inputs.
        branch_spec = "MitaliPurwar21:UmdTask657_canonical_pr"
        # Prepare outputs.
        expected = ("MitaliPurwar21", "UmdTask657_canonical_pr")
        # Run test.
        self.helper(branch_spec, expected)

    def test2(self) -> None:
        """
        Test a branch without the owner.
        """
        # Prepare inputs.
        branch_spec = "UmdTask657_canonical_pr"
        # Prepare outputs.
        expected = ("", "UmdTask657_canonical_pr")
        # Run test.
        self.helper(branch_spec, expected)

    def test3(self) -> None:
        """
        Test a branch with a slash and surrounding whitespace.
        """
        # Prepare inputs.
        branch_spec = "  user1:feature/Task1_foo\n"
        # Prepare outputs.
        expected = ("user1", "feature/Task1_foo")
        # Run test.
        self.helper(branch_spec, expected)


# #############################################################################
# Test_select_pr_url
# #############################################################################


class Test_select_pr_url(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._select_pr_url()`.
    """

    def helper(
        self, prs: List[Dict[str, Any]], owner: str, expected: str
    ) -> None:
        """
        Select the PR and compare its URL with `expected`.

        :param prs: PRs with the same head branch
        :param owner: owner of the head repo, or empty string for any owner
        :param expected: expected URL of the PR
        """
        # Run test.
        actual = dsggcwfp._select_pr_url(prs, owner, "Task1_foo")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test that the owner picks the PR among the ones with the same branch.
        """
        # Prepare inputs.
        prs = [
            {
                "url": "https://github.com/org/repo/pull/1",
                "headRepositoryOwner": {"login": "user1"},
            },
            {
                "url": "https://github.com/org/repo/pull/2",
                "headRepositoryOwner": {"login": "user2"},
            },
        ]
        owner = "user2"
        # Prepare outputs.
        expected = "https://github.com/org/repo/pull/2"
        # Run test.
        self.helper(prs, owner, expected)

    def test2(self) -> None:
        """
        Test that a single PR is picked when the owner is not specified.
        """
        # Prepare inputs.
        prs = [
            {
                "url": "https://github.com/org/repo/pull/1",
                "headRepositoryOwner": {"login": "user1"},
            },
        ]
        owner = ""
        # Prepare outputs.
        expected = "https://github.com/org/repo/pull/1"
        # Run test.
        self.helper(prs, owner, expected)

    def test3(self) -> None:
        """
        Test that multiple PRs and no owner are rejected as ambiguous.
        """
        # Prepare inputs.
        prs = [
            {
                "url": "https://github.com/org/repo/pull/1",
                "headRepositoryOwner": {"login": "user1"},
            },
            {
                "url": "https://github.com/org/repo/pull/2",
                "headRepositoryOwner": {"login": "user2"},
            },
        ]
        owner = ""
        # Prepare outputs.
        expected = "Multiple open PRs have head branch 'Task1_foo'"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsggcwfp._select_pr_url(prs, owner, "Task1_foo")
        # Check outputs.
        self.assertIn(expected, str(cm.exception))

    def test4(self) -> None:
        """
        Test that an owner without a PR is rejected.
        """
        # Prepare inputs.
        prs = [
            {
                "url": "https://github.com/org/repo/pull/1",
                "headRepositoryOwner": {"login": "user1"},
            },
        ]
        owner = "user3"
        # Prepare outputs.
        expected = "Can't find an open PR with head branch 'user3:Task1_foo'"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsggcwfp._select_pr_url(prs, owner, "Task1_foo")
        # Check outputs.
        self.assertIn(expected, str(cm.exception))


# #############################################################################
# Test_parse_gitlinks
# #############################################################################


class Test_parse_gitlinks(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._parse_gitlinks()`.
    """

    def helper(
        self, ls_files_output: str, expected: List[Tuple[str, str]]
    ) -> None:
        """
        Parse the output of `git ls-files --stage` and compare the submodules.

        :param ls_files_output: output of `git ls-files --stage`
        :param expected: expected path and commit of each submodule
        """
        # Run test.
        actual = dsggcwfp._parse_gitlinks(ls_files_output)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that only the entries with the submodule mode are returned.
        """
        # Prepare inputs.
        ls_files_output = (
            "100644 8e3a6c1 0\tREADME.md\n160000 98eef91 0\thelpers_root\n"
        )
        # Prepare outputs.
        expected = [("helpers_root", "98eef91")]
        # Run test.
        self.helper(ls_files_output, expected)

    def test2(self) -> None:
        """
        Test a repo without submodules.
        """
        # Prepare inputs.
        ls_files_output = "100644 8e3a6c1 0\tREADME.md\n"
        # Prepare outputs.
        expected: List[Tuple[str, str]] = []
        # Run test.
        self.helper(ls_files_output, expected)

    def test3(self) -> None:
        """
        Test multiple submodules, one of them in a nested dir.
        """
        # Prepare inputs.
        ls_files_output = (
            "160000 aaa1111 0\tdeps/lib_a\n"
            "100644 8e3a6c1 0\tdeps/README.md\n"
            "160000 bbb2222 0\thelpers_root\n"
        )
        # Prepare outputs.
        expected = [("deps/lib_a", "aaa1111"), ("helpers_root", "bbb2222")]
        # Run test.
        self.helper(ls_files_output, expected)


# #############################################################################
# Test_get_remove_script
# #############################################################################


class Test_get_remove_script(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._get_remove_script()`.
    """

    def helper(
        self,
        submodule_worktrees: List[Tuple[str, str]],
        expected: str,
    ) -> None:
        """
        Build the script and compare it with `expected`.

        :param submodule_worktrees: source dir and worktree dir of each
            submodule worktree
        :param expected: expected content of the script
        """
        # Prepare inputs.
        client_root = "/src/umd_classes3"
        worktree_path = "/src/umd_classes888"
        script_paths = [
            "/src/umd_classes888/git_worktree_remove.sh",
            "/src/umd_classes3/git_worktree_remove_888.sh",
        ]
        # Run test.
        actual = dsggcwfp._get_remove_script(
            client_root, worktree_path, script_paths, submodule_worktrees
        )
        # Check outputs.
        self.assert_equal(actual, hprint.dedent(expected) + "\n")

    def test1(self) -> None:
        """
        Test a worktree without submodules.
        """
        # Prepare inputs.
        submodule_worktrees: List[Tuple[str, str]] = []
        # Prepare outputs.
        expected = """
        #!/bin/bash
        # \"\"\"
        # Remove the worktree /src/umd_classes888 created by
        # `git_create_worktree_from_pr.py`.
        # \"\"\"

        set -e

        # Run from the client, since the dir of the worktree is deleted.
        cd /src/umd_classes3

        # Remove the copies of this script, since Git refuses to remove a worktree
        # with untracked files.
        rm -f /src/umd_classes888/git_worktree_remove.sh /src/umd_classes3/git_worktree_remove_888.sh

        # Remove the worktree.
        git worktree remove /src/umd_classes888
        """
        # Run test.
        self.helper(submodule_worktrees, expected)

    def test2(self) -> None:
        """
        Test a worktree with a submodule that has a nested submodule.
        """
        # Prepare inputs.
        submodule_worktrees = [
            (
                "/src/umd_classes3/helpers_root",
                "/src/umd_classes888/helpers_root",
            ),
            (
                "/src/umd_classes3/helpers_root/deps/lib",
                "/src/umd_classes888/helpers_root/deps/lib",
            ),
        ]
        # Prepare outputs.
        expected = """
        #!/bin/bash
        # \"\"\"
        # Remove the worktree /src/umd_classes888 created by
        # `git_create_worktree_from_pr.py`.
        # \"\"\"

        set -e

        # Run from the client, since the dir of the worktree is deleted.
        cd /src/umd_classes3

        # Remove the worktree of each submodule, nested ones first. Git
        # refuses to remove a worktree with a populated submodule, so
        # restore its empty dir.
        git -C /src/umd_classes3/helpers_root/deps/lib worktree remove /src/umd_classes888/helpers_root/deps/lib
        mkdir /src/umd_classes888/helpers_root/deps/lib
        git -C /src/umd_classes3/helpers_root worktree remove /src/umd_classes888/helpers_root
        mkdir /src/umd_classes888/helpers_root

        # Remove the copies of this script, since Git refuses to remove a worktree
        # with untracked files.
        rm -f /src/umd_classes888/git_worktree_remove.sh /src/umd_classes3/git_worktree_remove_888.sh

        # Remove the worktree.
        git worktree remove /src/umd_classes888
        """
        # Run test.
        self.helper(submodule_worktrees, expected)


# #############################################################################
# Test_get_tmux_script
# #############################################################################


class Test_get_tmux_script(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._get_tmux_script()`.
    """

    def helper(
        self, dir_suffix: str, create_script: bool, expected: str
    ) -> None:
        """
        Get the path of `tmux.py` in a worktree and compare it with `expected`.

        :param dir_suffix: suffix of the `dev_scripts_{dir_suffix}` dir
        :param create_script: whether the worktree contains the script
        :param expected: expected path of the script, relative to the worktree
        """
        # Prepare inputs.
        worktree_path = self.get_scratch_space()
        if create_script:
            script_path = os.path.join(worktree_path, expected)
            hio.create_dir(os.path.dirname(script_path), incremental=True)
            hio.to_file(script_path, "")
        # Run test.
        actual = dsggcwfp._get_tmux_script(worktree_path, dir_suffix)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test the repo that has its own thin client dir (e.g., `umd_classes`).
        """
        # Prepare inputs.
        dir_suffix = "umd_classes"
        create_script = True
        # Prepare outputs.
        expected = "dev_scripts_umd_classes/thin_client/tmux.py"
        # Run test.
        self.helper(dir_suffix, create_script, expected)

    def test2(self) -> None:
        """
        Test the `helpers` repo.
        """
        # Prepare inputs.
        dir_suffix = "helpers"
        create_script = True
        # Prepare outputs.
        expected = "dev_scripts_helpers/thin_client/tmux.py"
        # Run test.
        self.helper(dir_suffix, create_script, expected)

    def test3(self) -> None:
        """
        Test that a script missing from the worktree is not an error.
        """
        # Prepare inputs.
        dir_suffix = "umd_classes"
        create_script = False
        # Prepare outputs.
        expected = "dev_scripts_umd_classes/thin_client/tmux.py"
        # Run test.
        self.helper(dir_suffix, create_script, expected)


# #############################################################################
# Test_get_worktree_path
# #############################################################################


class Test_get_worktree_path(hunitest.TestCase):
    """
    Test `git_create_worktree_from_pr._get_worktree_path()`.
    """

    def helper(self, client_root: str, pr_number: int, expected: str) -> None:
        """
        Build the worktree path and compare it with `expected`.

        :param client_root: root of the client
        :param pr_number: PR number
        :param expected: expected worktree path
        """
        # Run test.
        actual = dsggcwfp._get_worktree_path(client_root, pr_number)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test that the digits of the client dir are replaced by the PR number.
        """
        # Prepare inputs.
        client_root = "/Users/user/src/umd_classes3"
        pr_number = 888
        # Prepare outputs.
        expected = "/Users/user/src/umd_classes888"
        # Run test.
        self.helper(client_root, pr_number, expected)

    def test2(self) -> None:
        """
        Test a client dir without trailing digits.
        """
        # Prepare inputs.
        client_root = "/Users/user/src/helpers"
        pr_number = 1451
        # Prepare outputs.
        expected = "/Users/user/src/helpers1451"
        # Run test.
        self.helper(client_root, pr_number, expected)

    def test3(self) -> None:
        """
        Test that only the trailing digits are replaced.
        """
        # Prepare inputs.
        client_root = "/Users/user/src/data605_classes12"
        pr_number = 5
        # Prepare outputs.
        expected = "/Users/user/src/data605_classes5"
        # Run test.
        self.helper(client_root, pr_number, expected)


# #############################################################################
# Test_git_create_worktree_from_pr_py
# #############################################################################


class Test_git_create_worktree_from_pr_py(hunitest.TestCase):
    """
    Test the `git_create_worktree_from_pr.py` executable.
    """

    def test1(self) -> None:
        """
        Test that a PR of a different repo than the current one is rejected.
        """
        # Prepare inputs.
        parser = dsggcwfp._parse()
        url = "https://github.com/not_an_owner/not_a_repo/pull/1"
        argv = ["git_create_worktree_from_pr.py", "--url", url, "--dry_run"]
        # Prepare outputs.
        expected = "The PR is not in the repo of the current dir"
        # Run test.
        with (
            umock.patch("sys.argv", argv),
            self.assertRaises(AssertionError) as cm,
        ):
            dsggcwfp._main(parser)
        # Check outputs.
        self.assertIn(expected, str(cm.exception))
