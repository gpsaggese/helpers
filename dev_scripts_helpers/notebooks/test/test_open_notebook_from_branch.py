import os

import helpers.hunit_test as hunitest

import dev_scripts_helpers.notebooks.open_notebook_from_branch as dsnoonfb

# #############################################################################
# Test_normalize_branch
# #############################################################################


class Test_normalize_branch(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._normalize_branch()`.
    """

    def test1(self) -> None:
        """
        Test that the `origin/` prefix is removed.
        """
        # Prepare inputs.
        branch = "origin/UmdTask788_Racket_sports"
        # Run test.
        actual = dsnoonfb._normalize_branch(branch)
        # Check outputs.
        expected = "UmdTask788_Racket_sports"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a branch without remote is not changed.
        """
        # Prepare inputs.
        branch = "UmdTask788_Racket_sports"
        # Run test.
        actual = dsnoonfb._normalize_branch(branch)
        # Check outputs.
        expected = branch
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that only the leading `origin/` is removed.
        """
        # Prepare inputs.
        branch = "origin/feature/origin/fix"
        # Run test.
        actual = dsnoonfb._normalize_branch(branch)
        # Check outputs.
        expected = "feature/origin/fix"
        self.assert_equal(actual, expected)


# #############################################################################
# Test_parse_pr_url
# #############################################################################


class Test_parse_pr_url(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._parse_pr_url()`.
    """

    def test1(self) -> None:
        """
        Test that a PR URL is parsed into the repo and the PR number.
        """
        # Prepare inputs.
        txt = "https://github.com/gpsaggese/gpsaggese.github.io/pull/895"
        # Run test.
        actual = dsnoonfb._parse_pr_url(txt)
        # Check outputs.
        expected = ("gpsaggese/gpsaggese.github.io", 895)
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that the trailing parts of a PR URL are ignored.
        """
        # Prepare inputs.
        txt = "https://github.com/gpsaggese/helpers/pull/12/files?diff=split#r1"
        # Run test.
        actual = dsnoonfb._parse_pr_url(txt)
        # Check outputs.
        expected = ("gpsaggese/helpers", 12)
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that a branch name is not a PR URL.
        """
        # Prepare inputs.
        txt = "UmdTask673_ADS_Implement_Tutorial_for_AutoGluon"
        # Run test.
        actual = dsnoonfb._parse_pr_url(txt)
        # Check outputs.
        self.assertIsNone(actual)

    def test4(self) -> None:
        """
        Test that a branch name with a slash is not a PR URL.
        """
        # Prepare inputs.
        txt = "origin/feature/pull/12"
        # Run test.
        actual = dsnoonfb._parse_pr_url(txt)
        # Check outputs.
        self.assertIsNone(actual)

    def test5(self) -> None:
        """
        Test that a GitHub URL that is not a PR is not a PR URL.
        """
        # Prepare inputs.
        txt = "https://github.com/gpsaggese/helpers/issues/12"
        # Run test.
        actual = dsnoonfb._parse_pr_url(txt)
        # Check outputs.
        self.assertIsNone(actual)


# #############################################################################
# Test_parse_pr_head_branch
# #############################################################################


class Test_parse_pr_head_branch(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._parse_pr_head_branch()`.
    """

    def test1(self) -> None:
        """
        Test that the head branch is extracted from the `gh pr view` output.
        """
        # Prepare inputs.
        txt = '{"headRefName": "UmdTask673_ADS", "isCrossRepository": false}'
        pr_url = "https://github.com/gpsaggese/gpsaggese.github.io/pull/895"
        # Run test.
        actual = dsnoonfb._parse_pr_head_branch(txt, pr_url)
        # Check outputs.
        expected = "UmdTask673_ADS"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a PR from a fork is rejected.
        """
        # Prepare inputs.
        txt = '{"headRefName": "fix", "isCrossRepository": true}'
        pr_url = "https://github.com/gpsaggese/helpers/pull/12"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsnoonfb._parse_pr_head_branch(txt, pr_url)
        # Check outputs.
        self.assertIn("comes from a fork", str(cm.exception))


# #############################################################################
# Test_get_notebook_rel_path
# #############################################################################


class Test_get_notebook_rel_path(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._get_notebook_rel_path()`.
    """

    def test1(self) -> None:
        """
        Test that a path missing locally is assumed relative to the git root.
        """
        # Prepare inputs.
        notebook = "no_such_dir_xyz/notebooks/nb.ipynb"
        git_root = "/git/root"
        # Run test.
        actual = dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        expected = notebook
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that an absolute path is converted to be relative to the git root.
        """
        # Prepare inputs.
        git_root = "/git/root"
        notebook = os.path.join(git_root, "project/notebooks/nb.ipynb")
        # Run test.
        actual = dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        expected = "project/notebooks/nb.ipynb"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that a file that is not a notebook is rejected.
        """
        # Prepare inputs.
        notebook = "project/notebooks/nb.py"
        git_root = "/git/root"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        self.assertIn("is not a notebook", str(cm.exception))

    def test4(self) -> None:
        """
        Test that an absolute path outside the git root is rejected.
        """
        # Prepare inputs.
        notebook = "/other/dir/nb.ipynb"
        git_root = "/git/root"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        self.assertIn("is outside the git root", str(cm.exception))


# #############################################################################
# Test_get_notebook_url
# #############################################################################


class Test_get_notebook_url(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._get_notebook_url()`.
    """

    def test1(self) -> None:
        """
        Test the URL of a notebook inside the container.
        """
        # Prepare inputs.
        rel_notebook = "research/Racket/notebooks/racket_shot_probability.ipynb"
        # Run test.
        actual = dsnoonfb._get_notebook_url(rel_notebook, 8888)
        # Check outputs.
        expected = (
            "http://localhost:8888/lab/tree/git_root/research/Racket/"
            "notebooks/racket_shot_probability.ipynb"
        )
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that special characters in the path are escaped.
        """
        # Prepare inputs.
        rel_notebook = "my dir/nb #1.ipynb"
        # Run test.
        actual = dsnoonfb._get_notebook_url(rel_notebook, 8889)
        # Check outputs.
        expected = (
            "http://localhost:8889/lab/tree/git_root/my%20dir/nb%20%231.ipynb"
        )
        self.assert_equal(actual, expected)
