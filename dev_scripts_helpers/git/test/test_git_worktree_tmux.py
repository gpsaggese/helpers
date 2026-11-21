"""
Tests for `git_worktree_tmux.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_worktree_tmux as dsggtgwt
"""

import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

import dev_scripts_helpers.git.git_worktree_tmux as dsggwt

# pylint: disable=protected-access


# #############################################################################
# Test__get_repo_dir
# #############################################################################


class Test__get_repo_dir(hunitest.TestCase):
    """
    Test `_get_repo_dir()`.

    Directory structure:
    outer/
    |-- .git/
    |-- .gitmodules (lists `sub`)
    |-- repo_config.yaml (`repo_name: outer`)
    `-- sub/
        `-- repo_config.yaml (`repo_name: helpers`)
    """

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create the outer repo.
        self.outer_dir = os.path.join(temp_dir, "outer")
        hio.create_dir(os.path.join(self.outer_dir, ".git"), incremental=False)
        txt = """
        repo_info:
          repo_name: outer
        """
        hio.to_file(
            os.path.join(self.outer_dir, "repo_config.yaml"), hprint.dedent(txt)
        )
        txt = """
        [submodule "sub"]
            path = sub
            url = git@github.com:org/helpers.git
        """
        hio.to_file(
            os.path.join(self.outer_dir, ".gitmodules"), hprint.dedent(txt)
        )
        # Create the submodule.
        self.sub_dir = os.path.join(self.outer_dir, "sub")
        hio.create_dir(self.sub_dir, incremental=False)
        txt = """
        repo_info:
          repo_name: helpers
        """
        hio.to_file(
            os.path.join(self.sub_dir, "repo_config.yaml"), hprint.dedent(txt)
        )

    def test1(self) -> None:
        """
        Check that the short name of a submodule is resolved to its dir.
        """
        self.set_up_test()
        with hsystem.cd(self.outer_dir):
            actual = dsggwt._get_repo_dir("helpers")
        self.assertEqual(actual, self.sub_dir)

    def test2(self) -> None:
        """
        Check that the short name of the outermost repo is resolved to its dir.
        """
        self.set_up_test()
        with hsystem.cd(self.sub_dir):
            actual = dsggwt._get_repo_dir("outer")
        self.assertEqual(actual, self.outer_dir)


# #############################################################################
# Test__get_worktree_names
# #############################################################################


class Test__get_worktree_names(hunitest.TestCase):
    """
    Test `_get_worktree_names()`.
    """

    def test1(self) -> None:
        """
        Check the names for a branch with an issue number.
        """
        # Prepare inputs.
        branch_name = "HelpersTask1354_Improve_bookmarking_flow"
        dir_suffix = "helpers"
        src_dir = "/src"
        # Run test.
        actual = dsggwt._get_worktree_names(branch_name, dir_suffix, src_dir)
        # Check outputs.
        expected = ("/src/helpers_worktree_1354", "_worktree_1354")
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Check the names for a branch of a different repo.
        """
        # Prepare inputs.
        branch_name = "UmdTask911_Write_AI_Sw_Eng_Book_2"
        dir_suffix = "umd_classes"
        src_dir = "/home/user/src"
        # Run test.
        actual = dsggwt._get_worktree_names(branch_name, dir_suffix, src_dir)
        # Check outputs.
        expected = (
            "/home/user/src/umd_classes_worktree_911",
            "_worktree_911",
        )
        self.assertEqual(actual, expected)
