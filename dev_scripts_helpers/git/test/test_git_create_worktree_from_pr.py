"""
Import as:

import dev_scripts_helpers.git.test.test_git_create_worktree_from_pr as dsggtgcwfp
"""

import logging

import dev_scripts_helpers.git.git_create_worktree_from_pr as dsggcwfp
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
