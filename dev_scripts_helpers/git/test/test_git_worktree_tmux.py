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


# #############################################################################
# Test__get_open_cmd
# #############################################################################


class Test__get_open_cmd(hunitest.TestCase):
    """
    Test `_get_open_cmd()`.
    """

    def test1(self) -> None:
        """
        Check the command that opens the tmux session on a worktree.
        """
        # Prepare inputs.
        worktree_dir = "/src/helpers_worktree_1354"
        dir_suffix = "helpers"
        index = "_worktree_1354"
        log_level = "INFO"
        # Run test.
        actual = dsggwt._get_open_cmd(worktree_dir, dir_suffix, index, log_level)
        # Check outputs.
        expected = (
            "cd /src/helpers_worktree_1354 && "
            "/src/helpers_worktree_1354/dev_scripts_helpers/thin_client/tmux.py"
            " --index _worktree_1354 -v INFO"
        )
        self.assertEqual(actual, expected)


# #############################################################################
# Test__get_delete_cmd
# #############################################################################


class Test__get_delete_cmd(hunitest.TestCase):
    """
    Test `_get_delete_cmd()`.
    """

    def test1(self) -> None:
        """
        Check the command that deletes a worktree and its tmux session.
        """
        # Prepare inputs.
        repo_root = "/src/helpers1"
        branch_name = "HelpersTask1354_Improve_bookmarking_flow"
        # Run test.
        actual = dsggwt._get_delete_cmd(repo_root, branch_name)
        # Check outputs.
        expected = (
            "cd /src/helpers1 && git_worktree_tmux.py "
            "--branch_name HelpersTask1354_Improve_bookmarking_flow "
            "--action delete"
        )
        self.assertEqual(actual, expected)


# #############################################################################
# Test__delete_worktree
# #############################################################################


class Test__delete_worktree(hunitest.TestCase):
    """
    Test `_delete_worktree()` on a real Git repo with a worktree.

    Directory structure:
    scratch/
    |-- origin/ (bare repo, upstream of `main`)
    |-- main/ (clone of origin, with branch `Task1_Fix` pushed)
    `-- main_worktree_1/ (worktree of `Task1_Fix`)
    """

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        self.origin_dir = os.path.join(temp_dir, "origin")
        self.main_dir = os.path.join(temp_dir, "main")
        self.worktree_dir = os.path.join(temp_dir, "main_worktree_1")
        self.branch_name = "Task1_Fix"
        git = "git -c user.name=test -c user.email=test@test.com"
        cmds = [
            f"git init --bare {self.origin_dir}",
            f"git clone {self.origin_dir} {self.main_dir}",
            f"{git} -C {self.main_dir} commit --allow-empty -m init",
            f"git -C {self.main_dir} push origin HEAD",
            f"git -C {self.main_dir} branch {self.branch_name}",
            f"git -C {self.main_dir} push -u origin {self.branch_name}",
            f"git -C {self.main_dir} worktree add {self.worktree_dir} "
            f"{self.branch_name}",
        ]
        for cmd in cmds:
            hsystem.system(cmd)

    def _delete(self, *, delete_branch: bool, force: bool) -> None:
        with hsystem.cd(self.main_dir):
            dsggwt._delete_worktree(
                self.main_dir,
                self.branch_name,
                self.worktree_dir,
                "no_such_tmux_session_for_test",
                delete_branch=delete_branch,
                force=force,
                dry_run=False,
            )

    def _get_branches(self) -> str:
        cmd = f"git -C {self.main_dir} branch --format='%(refname:short)'"
        _, txt = hsystem.system_to_string(cmd)
        return txt

    def test1(self) -> None:
        """
        Check that a clean worktree is removed and its branch is kept.
        """
        self.set_up_test()
        self._delete(delete_branch=False, force=False)
        self.assertFalse(os.path.exists(self.worktree_dir))
        self.assertIn(self.branch_name, self._get_branches())

    def test2(self) -> None:
        """
        Check that the branch is also deleted with `delete_branch`.
        """
        self.set_up_test()
        self._delete(delete_branch=True, force=False)
        self.assertFalse(os.path.exists(self.worktree_dir))
        self.assertNotIn(self.branch_name, self._get_branches())

    def test3(self) -> None:
        """
        Check that a worktree with uncommitted changes is not removed.
        """
        self.set_up_test()
        hio.to_file(os.path.join(self.worktree_dir, "new_file.txt"), "text")
        with self.assertRaises(AssertionError) as cm:
            self._delete(delete_branch=False, force=False)
        self.assertIn("has uncommitted changes", str(cm.exception))
        self.assertTrue(os.path.exists(self.worktree_dir))

    def test4(self) -> None:
        """
        Check that a worktree with uncommitted changes is removed with `force`.
        """
        self.set_up_test()
        hio.to_file(os.path.join(self.worktree_dir, "new_file.txt"), "text")
        self._delete(delete_branch=False, force=True)
        self.assertFalse(os.path.exists(self.worktree_dir))

    def test5(self) -> None:
        """
        Check that a branch with unpushed commits is not deleted.
        """
        self.set_up_test()
        git = "git -c user.name=test -c user.email=test@test.com"
        cmd = f"{git} -C {self.worktree_dir} commit --allow-empty -m local"
        hsystem.system(cmd)
        with self.assertRaises(AssertionError) as cm:
            self._delete(delete_branch=True, force=False)
        self.assertIn("has commits not pushed", str(cm.exception))
        self.assertTrue(os.path.exists(self.worktree_dir))
        self.assertIn(self.branch_name, self._get_branches())

    def test6(self) -> None:
        """
        Check that running from the worktree to delete is refused.
        """
        self.set_up_test()
        with self.assertRaises(AssertionError) as cm:
            dsggwt._delete_worktree(
                self.worktree_dir,
                self.branch_name,
                self.worktree_dir,
                "no_such_tmux_session_for_test",
                delete_branch=False,
                force=False,
                dry_run=False,
            )
        self.assertIn("Run from the main repo", str(cm.exception))
        self.assertTrue(os.path.exists(self.worktree_dir))
