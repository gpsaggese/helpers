import logging
import os
import tempfile
from typing import Generator, List, Optional

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# Unfortunately we can't check the outcome of some of these functions since we
# don't know in which dir we are running. Thus we just test that the function
# completes and visually inspect the outcome, if possible.


def _check_find_git_root(
    test_case: hunitest.TestCase,
    working_dir: str,
    expected_root: str,
) -> None:
    """
    Check that find_git_root returns the expected root from working_dir.
    """
    with hsystem.cd(working_dir):
        git_root = hgit.find_git_root(".")
        test_case.assert_equal(git_root, expected_root)


def _call_get_files_to_process(
    *,
    files: str = "",
    from_file: str = "",
    modified: bool = False,
    branch: bool = False,
    last_commit: bool = False,
    all_: bool = False,
    mutually_exclusive: bool = True,
    remove_dirs: bool = False,
    dir_name: Optional[str] = None,
) -> List[str]:
    """
    Call get_files_to_process with default values.
    """
    return hgit.get_files_to_process(
        files,
        from_file,
        modified,
        branch,
        last_commit,
        all_,
        mutually_exclusive=mutually_exclusive,
        remove_dirs=remove_dirs,
        dir_name=dir_name,
    )


# #############################################################################
# Test_git_submodule1
# #############################################################################


class Test_git_submodule1(hunitest.TestCase):
    def test_get_client_root1(self) -> None:
        actual = hgit.get_client_root(super_module=True)
        _LOG.debug("actual=%s", actual)

    def test_get_client_root2(self) -> None:
        actual = hgit.get_client_root(super_module=False)
        _LOG.debug("actual=%s", actual)

    def test_get_project_dirname1(self) -> None:
        actual = hgit.get_project_dirname()
        _LOG.debug("actual=%s", actual)

    def test_get_branch_name1(self) -> None:
        actual = hgit.get_branch_name()
        _LOG.debug("actual=%s", actual)

    def test_is_inside_submodule1(self) -> None:
        actual = hgit.is_inside_submodule()
        _LOG.debug("actual=%s", actual)

    # Outside CK infra, the following call hangs, so we skip it.
    # TODO(gp): I don't see why it requires our infra.
    @pytest.mark.requires_ck_infra
    def test_is_amp(self) -> None:
        actual = hgit.is_amp()
        _LOG.debug("actual=%s", actual)

    def test_get_path_from_supermodule1(self) -> None:
        actual = hgit.get_path_from_supermodule()
        _LOG.debug("actual=%s", actual)

    def test_get_submodule_paths1(self) -> None:
        actual = hgit.get_submodule_paths()
        _LOG.debug("actual=%s", actual)


# #############################################################################
# Test_git_submodule2
# #############################################################################


class Test_git_submodule2(hunitest.TestCase):
    # def test_get_submodule_hash1(self) -> None:
    #     dir_name = "amp"
    #     _ = hgit._get_submodule_hash(dir_name)

    def test_get_remote_head_hash1(self) -> None:
        dir_name = "."
        actual = hgit.get_head_hash(dir_name)
        _LOG.debug("actual=%s", actual)

    # def test_report_submodule_status1(self) -> None:
    #     dir_names = ["."]
    #     short_hash = True
    #     _ = hgit.report_submodule_status(dir_names, short_hash)

    def test_get_head_hash1(self) -> None:
        dir_name = "."
        actual = hgit.get_head_hash(dir_name)
        _LOG.debug("actual=%s", actual)

    def _helper_group_hashes(
        self,
        head_hash: str,
        remh_hash: str,
        subm_hash: Optional[str],
        expected: str,
    ) -> None:
        actual = hgit._group_hashes(head_hash, remh_hash, subm_hash)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_group_hashes1(self) -> None:
        # Prepare inputs.
        head_hash = "a2bfc704"
        remh_hash = "a2bfc704"
        subm_hash = None
        expected = "head_hash = remh_hash = a2bfc704"
        # Run test.
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, expected)

    def test_group_hashes2(self) -> None:
        # Prepare inputs.
        head_hash = "22996772"
        remh_hash = "92167662"
        subm_hash = "92167662"
        expected = """
        head_hash = 22996772
        remh_hash = subm_hash = 92167662
        """
        # Run test.
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, expected)

    def test_group_hashes3(self) -> None:
        # Prepare inputs.
        head_hash = "7ea03eb6"
        remh_hash = "7ea03eb6"
        subm_hash = "7ea03eb6"
        expected = "head_hash = remh_hash = subm_hash = 7ea03eb6"
        # Run test.
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, expected)


# #############################################################################
# Test_git_repo_name1
# #############################################################################


class Test_git_repo_name1(hunitest.TestCase):
    def _helper_parse_github_repo_name(
        self,
        repo_name: str,
        expected_host: str,
        expected_repo: str,
    ) -> None:
        host_name, actual_repo = hgit._parse_github_repo_name(repo_name)
        self.assert_equal(host_name, expected_host)
        self.assert_equal(actual_repo, expected_repo)

    def test_parse_github_repo_name1(self) -> None:
        repo_name = "git@github.com:alphamatic/amp"
        expected_host = "github.com"
        expected_repo = "alphamatic/amp"
        self._helper_parse_github_repo_name(
            repo_name, expected_host, expected_repo
        )

    def test_parse_github_repo_name2(self) -> None:
        repo_name = "https://github.com/alphamatic/amp"
        expected_host = "github.com"
        expected_repo = "alphamatic/amp"
        self._helper_parse_github_repo_name(
            repo_name, expected_host, expected_repo
        )

    def test_parse_github_repo_name3(self) -> None:
        repo_name = "git@github.fake.com:alphamatic/amp"
        expected_host = "github.fake.com"
        expected_repo = "alphamatic/amp"
        self._helper_parse_github_repo_name(
            repo_name, expected_host, expected_repo
        )

    def test_parse_github_repo_name4(self) -> None:
        repo_name = "https://github.fake.com/alphamatic/amp"
        expected_host = "github.fake.com"
        expected_repo = "alphamatic/amp"
        self._helper_parse_github_repo_name(
            repo_name, expected_host, expected_repo
        )

    def test_get_repo_full_name_from_dirname1(self) -> None:
        actual = hgit.get_repo_full_name_from_dirname(
            dir_name=".", include_host_name=False
        )
        _LOG.debug("actual=%s", actual)

    def test_get_repo_full_name_from_dirname2(self) -> None:
        actual = hgit.get_repo_full_name_from_dirname(
            dir_name=".", include_host_name=True
        )
        _LOG.debug("actual=%s", actual)

    def test_get_repo_full_name_from_client1(self) -> None:
        actual = hgit.get_repo_full_name_from_client(super_module=True)
        _LOG.debug("actual=%s", actual)

    def test_get_repo_full_name_from_client2(self) -> None:
        actual = hgit.get_repo_full_name_from_client(super_module=False)
        _LOG.debug("actual=%s", actual)


# #############################################################################
# Test_git_path1
# #############################################################################


# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
class Test_git_path1(hunitest.TestCase):
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_supermodule(),
        reason="Run only in amp as super-module",
    )
    def test_get_path_from_git_root1(self) -> None:
        file_name = "/app/helpers/test/test_hgit.py"
        actual = hgit.get_path_from_git_root(file_name, super_module=True)
        _LOG.debug("get_path_from_git_root()=%s", actual)
        # Check.
        expected = "helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(),
        reason="Run only in amp as sub-module",
    )
    def test_get_path_from_git_root2(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        actual = hgit.get_path_from_git_root(file_name, super_module=True)
        _LOG.debug("get_path_from_git_root()=%s", actual)
        # Check.
        expected = "amp/helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    def test_get_path_from_git_root3(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        git_root = "/app"
        actual = hgit.get_path_from_git_root(
            file_name, super_module=False, git_root=git_root
        )
        # Check.
        expected = "amp/helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    def test_get_path_from_git_root4(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        git_root = "/app/amp"
        actual = hgit.get_path_from_git_root(
            file_name, super_module=False, git_root=git_root
        )
        # Check.
        expected = "helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    def test_get_path_from_git_root5(self) -> None:
        file_name = "helpers/test/test_hgit.py"
        git_root = "/app/amp"
        with self.assertRaises(ValueError):
            hgit.get_path_from_git_root(
                file_name, super_module=False, git_root=git_root
            )


# #############################################################################
# Test_git_modified_files1
# #############################################################################


# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
class Test_git_modified_files1(hunitest.TestCase):
    # This will be run before and after each test.
    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        # Run before each test.
        self.set_up_test()
        yield

    def set_up_test(self) -> None:
        """
        All these tests need a reference to Git master branch.
        """
        hgit.fetch_origin_master_if_needed()

    def test_get_modified_files1(self) -> None:
        actual = hgit.get_modified_files()
        _LOG.debug("actual=%s", actual)

    def test_get_previous_committed_files1(self) -> None:
        actual = hgit.get_previous_committed_files()
        _LOG.debug("actual=%s", actual)

    def test_get_modified_files_in_branch1(self) -> None:
        actual = hgit.get_modified_files_in_branch("master")
        _LOG.debug("actual=%s", actual)

    def test_get_modified_files_in_branch2(self) -> None:
        actual = hgit.get_modified_files_in_branch(
            "master", use_branch_point=True
        )
        _LOG.debug("actual=%s", actual)

    def test_get_summary_files_in_branch1(self) -> None:
        actual = hgit.get_summary_files_in_branch("master")
        _LOG.debug("actual=%s", actual)

    def test_git_log1(self) -> None:
        actual = hgit.git_log()
        _LOG.debug("actual=%s", actual)


# #############################################################################
# Test_find_docker_file1
# #############################################################################


# TODO(ai_gp): Factor out common code.
# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
class Test_find_docker_file1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test for a file `amp/helpers/test/test_hgit.py` that is not from Docker
        (i.e., it doesn't start with `/app`) and exists in the repo.
        """
        amp_dir = hgit.get_amp_abs_path()
        # Use this file since `find_docker_file()` needs to do a `find` in the
        # repo, and we need to have a fixed file structure.
        file_name = hgit.find_file_in_git_tree("test_hgit.py")
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
        )
        expected = ["helpers/test/test_hgit.py"]
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test2(self) -> None:
        """
        Test for a file `/app/amp/helpers/test/test_hgit.py` that is from
        Docker (i.e., it starts with `/app`) and exists in the repo.
        """
        amp_dir = hgit.get_amp_abs_path()
        # Use this file since `find_docker_file()` needs to do a `find` in the
        # repo, and we need to have a fixed file structure.
        file_name = hgit.find_file_in_git_tree("test_hgit.py")
        expected = ["helpers/test/test_hgit.py"]
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
        )
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test3(self) -> None:
        """
        Test for a file `/venv/lib/python3.8/site-packages/invoke/tasks.py`
        that is from Docker (e.g., it starts with `/app`), but doesn't exist in
        the repo.
        """
        file_name = "/venv/lib/python3.8/site-packages/invoke/tasks.py"
        actual = hgit.find_docker_file(file_name)
        expected: List[str] = []
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test4(self) -> None:
        """
        Test for a file `./core/dataflow/utils.py` that is from Docker (i.e.,
        it starts with `/app`), but has multiple copies in the repo.
        """
        amp_dir = hgit.get_amp_abs_path()
        file_name = "/app/amp/core/dataflow/utils.py"
        dir_depth = 1
        candidate_files = [
            "core/dataflow/utils.py",
            "core/foo/utils.py",
            "core/bar/utils.py",
        ]
        candidate_files = [os.path.join(amp_dir, f) for f in candidate_files]
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
            dir_depth=dir_depth,
            candidate_files=candidate_files,
        )
        # Only one candidate file matches basename and one dirname.
        expected = ["core/dataflow/utils.py"]
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test5(self) -> None:
        amp_dir = hgit.get_amp_abs_path()
        file_name = "/app/amp/core/dataflow/utils.py"
        dir_depth = -1
        candidate_files = [
            "core/dataflow/utils.py",
            "bar/dataflow/utils.py",
            "core/foo/utils.py",
        ]
        candidate_files = [os.path.join(amp_dir, f) for f in candidate_files]
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
            dir_depth=dir_depth,
            candidate_files=candidate_files,
        )
        # Only one file matches `utils.py` using all the 3 dir levels.
        expected = ["core/dataflow/utils.py"]
        self.assert_equal(str(actual), str(expected), purify_text=True)


# #############################################################################
# Test_extract_gh_issue_number_from_branch
# #############################################################################


class Test_extract_gh_issue_number_from_branch(hunitest.TestCase):
    def _helper(self, branch_name: str, expected: str) -> None:
        """
        Helper to test extract_gh_issue_number_from_branch.
        """
        actual = hgit.extract_gh_issue_number_from_branch(branch_name)
        self.assert_equal(str(actual), expected)

    def test_extract_gh_issue_number_from_branch1(self) -> None:
        """
        Tests extraction from a branch name with a specific format.
        """
        branch_name = "CmampTask10725_Add_more_tabs_to_orange_tmux"
        expected = "10725"
        # Run test.
        self._helper(branch_name, expected)

    def test_extract_gh_issue_number_from_branch2(self) -> None:
        """
        Tests extraction from another branch name format.
        """
        branch_name = "HelpersTask23_Add_more_tabs_to_orange_tmux"
        expected = "23"
        # Run test.
        self._helper(branch_name, expected)

    def test_extract_gh_issue_number_from_branch3(self) -> None:
        """
        Tests extraction from a short branch name format.
        """
        branch_name = "CmTask3434"
        expected = "3434"
        # Run test.
        self._helper(branch_name, expected)

    def test_extract_gh_issue_number_from_branch4(self) -> None:
        """
        Tests behavior when no issue number is present in the branch name.
        """
        branch_name = "NoTaskNumberHere"
        expected = "None"
        # Run test.
        self._helper(branch_name, expected)


# #############################################################################
# Test__get_max_branch_num
# #############################################################################


class Test__get_max_branch_num(hunitest.TestCase):
    def helper(
        self, branch_names: List[str], curr_branch_name: str, expected: int
    ) -> None:
        """
        Check the highest number among the branches `<curr_branch_name>_N`.
        """
        actual = hgit._get_max_branch_num(branch_names, curr_branch_name)
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that the highest number is returned, not the last or the count.
        """
        branch_names = ["gp_1", "gp_10", "gp_2", "gp_6"]
        curr_branch_name = "gp"
        expected = 10
        # Run test.
        self.helper(branch_names, curr_branch_name, expected)

    def test2(self) -> None:
        """
        Test that remote-tracking branches are matched.
        """
        branch_names = ["gp_1", "origin/gp_6", "origin/gp_3"]
        curr_branch_name = "gp"
        expected = 6
        # Run test.
        self.helper(branch_names, curr_branch_name, expected)

    def test3(self) -> None:
        """
        Test that branches with a different prefix or suffix are ignored.
        """
        branch_names = ["gp", "gp_scratch_9", "gp_qa_1", "xgp_7", "gp_3_tmp"]
        curr_branch_name = "gp"
        expected = 0
        # Run test.
        self.helper(branch_names, curr_branch_name, expected)

    def test4(self) -> None:
        """
        Test that an empty list and empty lines return 0.
        """
        branch_names = [""]
        curr_branch_name = "gp"
        expected = 0
        # Run test.
        self.helper(branch_names, curr_branch_name, expected)

    def test5(self) -> None:
        """
        Test that special regex characters in the branch name are escaped.
        """
        branch_names = ["gp-fix.v2_4", "gpXfixXv2_9"]
        curr_branch_name = "gp-fix.v2"
        expected = 4
        # Run test.
        self.helper(branch_names, curr_branch_name, expected)


# #############################################################################
# Test_find_git_root1
# #############################################################################


class Test_find_git_root1(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a super repo (e.g. //orange)
    - the repo contains another super repo (e.g. //amp) as submodule (first level)
    - the first level submodule contains another submodule (e.g. //helpers) (second level)

    Directory structure:
    orange/
    |-- .git/
    `-- amp/
        |-- .git (points to ../.git/modules/amp)
        |-- ck.infra/
        `-- helpers_root/
            `-- .git (points to ../../.git/modules/amp/modules/helpers_root)
    """

    def _helper_find_git_root(self, working_dir_attr: str) -> None:
        self.set_up_test()
        working_dir = getattr(self, working_dir_attr)
        _check_find_git_root(self, working_dir, self.repo_dir)

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create `orange` repo.
        self.repo_dir = os.path.join(temp_dir, "orange")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create `amp` submodule under `orange`.
        self.submodule_dir = os.path.join(self.repo_dir, "amp")
        hio.create_dir(self.submodule_dir, incremental=False)
        submodule_git_file = os.path.join(self.submodule_dir, ".git")
        txt = "gitdir: ../.git/modules/amp"
        hio.to_file(submodule_git_file, txt)
        submodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "amp"
        )
        hio.create_dir(submodule_git_file_dir, incremental=False)
        # Create `helpers_root` submodule under `amp`.
        self.subsubmodule_dir = os.path.join(self.submodule_dir, "helpers_root")
        hio.create_dir(self.subsubmodule_dir, incremental=False)
        subsubmodule_git_file = os.path.join(self.subsubmodule_dir, ".git")
        txt = "gitdir: ../../.git/modules/amp/modules/helpers_root"
        hio.to_file(subsubmodule_git_file, txt)
        subsubmodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "amp", "modules", "helpers_root"
        )
        hio.create_dir(subsubmodule_git_file_dir, incremental=False)
        # Create `ck.infra` runnable dir under `amp`.
        self.runnable_dir = os.path.join(self.submodule_dir, "ck.infra")
        hio.create_dir(self.runnable_dir, incremental=False)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in the super repo (e.g. //orange)
        """
        self._helper_find_git_root("repo_dir")

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in first level submodule (e.g. //amp)
        """
        self._helper_find_git_root("submodule_dir")

    def test3(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in second level submodule (e.g. //helpers)
        """
        self._helper_find_git_root("subsubmodule_dir")

    def test4(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in a runnable dir (e.g. ck.infra) under the
            first level submodule (e.g. //amp)
        """
        self._helper_find_git_root("runnable_dir")


# #############################################################################
# Test_find_git_root2
# #############################################################################


class Test_find_git_root2(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a super repo (e.g. //cmamp)
    - the repo contains //helpers as submodule

    Directory structure:
    cmamp/
    |-- .git/
    |-- ck.infra/
    `-- helpers_root/
        `-- .git (points to ../.git/modules/helpers_root)
    """

    def _helper_find_git_root(self, working_dir_attr: str) -> None:
        self.set_up_test()
        working_dir = getattr(self, working_dir_attr)
        _check_find_git_root(self, working_dir, self.repo_dir)

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create `cmamp` repo.
        self.repo_dir = os.path.join(temp_dir, "cmamp")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create `helpers_root` submodule under `cmamp`.
        self.submodule_dir = os.path.join(self.repo_dir, "helpers_root")
        hio.create_dir(self.submodule_dir, incremental=False)
        submodule_git_file = os.path.join(self.submodule_dir, ".git")
        txt = "gitdir: ../.git/modules/helpers_root"
        hio.to_file(submodule_git_file, txt)
        submodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "helpers_root"
        )
        hio.create_dir(submodule_git_file_dir, incremental=False)
        # Create `ck.infra` runnable dir under `cmamp`.
        self.runnable_dir = os.path.join(self.repo_dir, "ck.infra")
        hio.create_dir(self.runnable_dir, incremental=False)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in the super repo (e.g. //cmamp)
        """
        self._helper_find_git_root("repo_dir")

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the submodule (e.g. //helpers)
        """
        self._helper_find_git_root("submodule_dir")

    def test3(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in a runnable dir (e.g. ck.infra)
        """
        self._helper_find_git_root("runnable_dir")


# #############################################################################
# Test_find_git_root3
# #############################################################################


class Test_find_git_root3(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is //helpers

    Directory structure:
    helpers/
    |-- .git/
    `-- arbitrary1/
        `-- arbitrary1a/
    """

    def _helper_find_git_root(self, working_dir_attr: str) -> None:
        self.set_up_test()
        working_dir = getattr(self, working_dir_attr)
        _check_find_git_root(self, working_dir, self.repo_dir)

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create `helpers` repo.
        self.repo_dir = os.path.join(temp_dir, "helpers")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create arbitrary directory under `helpers`.
        self.arbitrary_dir = os.path.join(
            self.repo_dir, "arbitrary1", "arbitrary1a"
        )
        hio.create_dir(self.arbitrary_dir, incremental=False)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the root of repo
        """
        self._helper_find_git_root("repo_dir")

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in an arbitrary directory under the repo
        """
        self._helper_find_git_root("arbitrary_dir")


# #############################################################################
# Test_find_git_root4
# #############################################################################


class Test_find_git_root4(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a linked repo

    Directory structure:
    repo/
    `-- .git/
    linked_repo/
    `-- .git (points to /repo/.git)
    """

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create repo.
        self.repo_dir = os.path.join(temp_dir, "repo")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create linked repo.
        self.linked_repo_dir = os.path.join(temp_dir, "linked_repo")
        hio.create_dir(self.linked_repo_dir, incremental=False)
        # Create pointer from linked repo to the actual repo.
        linked_git_file = os.path.join(self.linked_repo_dir, ".git")
        txt = f"gitdir: {self.git_dir}\n"
        hio.to_file(linked_git_file, txt)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the linked repo
        """
        self.set_up_test()
        with hsystem.cd(self.linked_repo_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)


# #############################################################################
# Test_find_git_root5
# #############################################################################


# TODO(ai_gp): Factor out common code.
class Test_find_git_root5(hunitest.TestCase):
    """
    Check that the error is raised when no .git directory is found.

    Directory structure:
    arbitrary_dir/
    broken_repo/
    `-- .git (points to /nonexistent/path/to/gitdir)
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        # `self.get_scratch_space()` does not work in the case as it creates
        # a temp directory within the repo where `.git` exists by default
        # (e.g. /app/helpers/test/outcomes/Test_find_git_root5.test1/tmp.scratch)
        # This preventing the exception from being raised.
        # We need a structure without `.git` for this test.
        self.temp_dir = tempfile.TemporaryDirectory()
        # Create arbitrary directory that is not a git repo.
        self.arbitrary_dir = os.path.join(self.temp_dir.name, "arbitrary_dir")
        hio.create_dir(self.arbitrary_dir, incremental=False)
        # Create arbitrary directory that is a submodule or linked repo that
        #   point to non existing super repo.
        self.repo_dir = os.path.join(self.temp_dir.name, "broken_repo")
        hio.create_dir(self.repo_dir, incremental=False)
        # Create an invalid `.git` file with a non-existent `gitdir`.
        invalid_git_file = os.path.join(self.repo_dir, ".git")
        txt = "gitdir: /nonexistent/path/to/gitdir"
        hio.to_file(invalid_git_file, txt)

    def tear_down_test(self) -> None:
        self.temp_dir.cleanup()

    def test1(self) -> None:
        """
        Check that the error is raised when the caller is in a directory that
        is not either a git repo or a submodule.
        """
        with (
            hsystem.cd(self.arbitrary_dir),
            self.assertRaises(AssertionError) as cm,
        ):
            _ = hgit.find_git_root(".")
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '/'
        !=
        '/'
        No .git directory or file found in any parent directory.
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)

    def test2(self) -> None:
        """
        Check that the error is raised when the caller is in a submodule or
        linked repo that points to non existing super repo.
        """
        with hsystem.cd(self.repo_dir), self.assertRaises(AssertionError) as cm:
            _ = hgit.find_git_root(".")
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '/'
        !=
        '/'
        Top-level .git directory not found.
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)


# #############################################################################
# Test_get_files_to_process_files
# #############################################################################


# TODO(ai_gp): Factor out common code.
class Test_get_files_to_process_files(hunitest.TestCase):
    """
    Test get_files_to_process with --files argument (space-separated list).
    """

    def test1(self) -> None:
        """
        Test with a single file in the space-separated list.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        actual = _call_get_files_to_process(files=file1, dir_name=temp_dir)
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test2(self) -> None:
        """
        Test with multiple files in the space-separated list.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        file3 = os.path.join(temp_dir, "file3.txt")
        hio.to_file(file1, "content1")
        hio.to_file(file2, "content2")
        hio.to_file(file3, "content3")
        files = f"{file1} {file2} {file3}"
        actual = _call_get_files_to_process(files=files, dir_name=temp_dir)
        self.assertEqual(len(actual), 3)
        for expected_file in ["file1.txt", "file2.txt", "file3.txt"]:
            self.assertTrue(
                any(expected_file in f for f in actual),
                f"{expected_file} not found in {actual}",
            )

    def test3(self) -> None:
        """
        Test that non-existent files are filtered out.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        nonexistent = os.path.join(temp_dir, "nonexistent.txt")
        hio.to_file(file1, "content1")
        files = f"{file1} {nonexistent}"
        actual = _call_get_files_to_process(files=files, dir_name=temp_dir)
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test4(self) -> None:
        """
        Test that empty string is handled correctly when mutually_exclusive=False.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        actual = _call_get_files_to_process(
            modified=True,
            mutually_exclusive=False,
            dir_name=temp_dir,
        )
        self.assertIsInstance(actual, list)

    def test5(self) -> None:
        """
        Test that --files is mutually exclusive with --modified when mutually_exclusive=True.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        with self.assertRaises(AssertionError):
            _call_get_files_to_process(
                files=file1,
                modified=True,
                dir_name=temp_dir,
            )

    def test6(self) -> None:
        """
        Test with a directory in the file list and remove_dirs=True.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        dir1 = os.path.join(temp_dir, "dir1")
        hio.to_file(file1, "content1")
        hio.create_dir(dir1, incremental=False)
        files = f"{file1} {dir1}"
        actual = _call_get_files_to_process(
            files=files,
            remove_dirs=True,
            dir_name=temp_dir,
        )
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test7(self) -> None:
        """
        Test that 'amp' directory is filtered out.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        files = f"{file1} amp"
        actual = _call_get_files_to_process(
            files=files,
            dir_name=temp_dir,
        )
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])


# #############################################################################
# Test_get_files_to_process_git
# #############################################################################


class Test_get_files_to_process_git(hunitest.TestCase):
    """
    Test get_files_to_process with git flags (--modified, --branch, --last_commit).
    """

    def test_modified1(self) -> None:
        """
        Retrieve files modified in this client.
        """
        _ = _call_get_files_to_process(
            modified=True,
            remove_dirs=True,
        )

    @pytest.mark.skipif(
        hgit.get_branch_name() == "master",
        reason="This test makes sense for a branch",
    )
    def test_branch1(self) -> None:
        """
        Retrieved files modified in this client.
        """
        hgit.fetch_origin_master_if_needed()
        _ = _call_get_files_to_process(
            branch=True,
            remove_dirs=True,
        )

    def test_last_commit1(self) -> None:
        """
        Retrieved files modified in the last commit.
        """
        _ = _call_get_files_to_process(
            last_commit=True,
            remove_dirs=True,
        )


# #############################################################################
# Test_get_files_to_process_from_file
# #############################################################################


# TODO(ai_gp): Factor out common code.
class Test_get_files_to_process_from_file(hunitest.TestCase):
    """
    Test get_files_to_process with --from_file argument.
    """

    def test_files1(self) -> None:
        """
        Pass through files from user.
        """
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_files1.txt")
        hio.to_file(from_file_path, __file__)
        files = _call_get_files_to_process(
            from_file=from_file_path,
            remove_dirs=True,
        )
        self.assertEqual(files, [__file__])

    def test_files2(self) -> None:
        """
        Pass through files from user.

        Use two types of paths we don't want to process:
          - non-existent python file
          - pattern "/*" that matches no files
        """
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_files2.txt")
        file_list_content = "testfile1.py testfiles1/*"
        hio.to_file(from_file_path, file_list_content)
        files = _call_get_files_to_process(
            from_file=from_file_path,
            remove_dirs=True,
        )
        self.assertEqual(files, [])


# #############################################################################
# Test_get_files_to_process_assert
# #############################################################################


# TODO(ai_gp): Factor out common code, if possible.
class Test_get_files_to_process_assert(hunitest.TestCase):
    """
    Test get_files_to_process mutual exclusivity assertions.
    """

    def test_assert1(self) -> None:
        """
        Test that --modified and --branch together cause an assertion.
        """
        with self.assertRaises(AssertionError) as cm:
            _call_get_files_to_process(
                modified=True,
                branch=True,
                all_=True,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        '3'
        ==
        '1'
        You can pick only one option to select files. Selected: --modified, --branch, --all_files
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_assert2(self) -> None:
        """
        Test that --modified and --files together cause an assertion if
        `mutually_exclusive=True`.
        """
        with self.assertRaises(AssertionError) as cm:
            _call_get_files_to_process(
                from_file=__file__,
                modified=True,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        '2'
        ==
        '1'
        You can pick only one option to select files. Selected: --from_file, --modified
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_assert3(self) -> None:
        """
        Test that --modified and --files together don't cause an assertion if
        `mutually_exclusive=False`.
        """
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_assert3.txt")
        hio.to_file(from_file_path, __file__)
        files = _call_get_files_to_process(
            from_file=from_file_path,
            modified=True,
            mutually_exclusive=False,
            remove_dirs=True,
        )
        self.assertIn(__file__, files)


# #############################################################################
# Test_find_git_root6
# #############################################################################


class Test_find_git_root6(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a worktree

    Directory structure:
    main_repo/
    `-- .git/
        |-- config
        `-- worktrees/
            `-- csfy2/
                |-- HEAD
                `-- config
    csfy2/ (worktree)
    `-- .git (points to /main_repo/.git/worktrees/csfy2)
    """

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create main repo with a .git directory.
        self.main_repo_dir = os.path.join(temp_dir, "main_repo")
        hio.create_dir(self.main_repo_dir, incremental=False)
        self.git_dir = os.path.join(self.main_repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create worktree git metadata directory.
        self.worktree_git_dir = os.path.join(self.git_dir, "worktrees", "csfy2")
        hio.create_dir(self.worktree_git_dir, incremental=False)
        # Create worktree directory.
        self.worktree_dir = os.path.join(temp_dir, "csfy2")
        hio.create_dir(self.worktree_dir, incremental=False)
        # Create pointer from worktree to the git directory.
        worktree_git_file = os.path.join(self.worktree_dir, ".git")
        txt = f"gitdir: {self.worktree_git_dir}\n"
        hio.to_file(worktree_git_file, txt)

    def test1(self) -> None:
        """
        Check that the function returns the worktree root when called from a worktree.
        """
        self.set_up_test()
        with hsystem.cd(self.worktree_dir):
            git_root = hgit.find_git_root(".")
            # For worktrees, the function should return the worktree root,
            # not the main repository root.
            self.assert_equal(git_root, self.worktree_dir)


# #############################################################################
# Test_find_git_root_in_active_worktree
# #############################################################################


@pytest.mark.skipif(not hgit.is_git_worktree(), reason="Not in a Git worktree")
class Test_find_git_root_in_active_worktree(hunitest.TestCase):
    """
    Tests for find_git_root() behavior in an active Git worktree.

    These tests only run when the code is in a Git worktree.
    """

    def test1(self) -> None:
        """
        Test that find_git_root() returns worktree root, not parent repo root.
        """
        git_root = hgit.find_git_root()
        # Verify it's the worktree root, not a parent directory
        git_file = os.path.join(git_root, ".git")
        self.assertTrue(os.path.isfile(git_file))
        # Read the .git file and verify it's a worktree
        git_content = hio.from_file(git_file)
        self.assertIn(".git/worktrees/", git_content)


# #############################################################################
# Test_git_add_file
# #############################################################################


class Test_git_add_file(hunitest.TestCase):
    def _setup_git_repo_helper(self, repo_name: str) -> str:
        """
        Create and initialize a git repo.

        :param repo_name: name of the repo directory
        :return: path to the git repo
        """
        scratch_dir = self.get_scratch_space()
        git_repo = os.path.join(scratch_dir, repo_name)
        hio.create_dir(git_repo, incremental=False)
        # Initialize git repo.
        with hsystem.cd(git_repo):
            hsystem.system("git init", suppress_output=True)
            hsystem.system(
                "git config user.email 'test@test.com'", suppress_output=True
            )
            hsystem.system(
                "git config user.name 'Test User'", suppress_output=True
            )
        return git_repo

    def helper(
        self,
        file_content: str,
        expect_added: bool,
        file_layout: str,
    ) -> None:
        """
        Test helper for git_add_file.

        :param file_content: content to write to test file
        :param expect_added: whether file should be in added list
        :param file_layout: file layout type - "single_file" for root level, "nested_dir" for nested directory
        """
        # Prepare inputs: create a temporary git repo with a file.
        git_repo = self._setup_git_repo_helper("test_repo")
        # File layout determines directory structure.
        if file_layout == "single_file":
            # Single file at root level.
            test_file = os.path.join(git_repo, "test.txt")
        elif file_layout == "nested_dir":
            # File in nested directory.
            nested_dir = os.path.join(git_repo, "subdir", "nested")
            hio.create_dir(nested_dir, incremental=False)
            test_file = os.path.join(nested_dir, "test.txt")
        else:
            raise ValueError(f"Unknown file_layout: {file_layout}")
        # Create and add a file.
        hio.to_file(test_file, file_content)
        # Run test: call git_add_file.
        with hsystem.cd(git_repo):
            added_files = hgit.git_add_file(test_file)
        # Check outputs.
        if expect_added:
            self.assertTrue(len(added_files) > 0, "Expected files to be added")
            self.assertIn(test_file, added_files)
        else:
            self.assertEqual(
                len(added_files), 0, "Expected no files to be added"
            )

    def test1(self) -> None:
        """
        Test git_add_file adds a new untracked file.
        """
        # Prepare inputs.
        file_content = "test content"
        file_layout = "single_file"
        # Prepare outputs.
        expect_added = True
        # Run test.
        self.helper(file_content, expect_added, file_layout)

    def test2(self) -> None:
        """
        Test git_add_file with empty file.
        """
        # Prepare inputs.
        file_content = ""
        file_layout = "single_file"
        # Prepare outputs.
        expect_added = True
        # Run test.
        self.helper(file_content, expect_added, file_layout)

    def test3(self) -> None:
        """
        Test git_add_file with file in nested directory.
        """
        # Prepare inputs.
        file_content = "nested content"
        file_layout = "nested_dir"
        # Prepare outputs.
        expect_added = True
        # Run test.
        self.helper(file_content, expect_added, file_layout)


# #############################################################################
# Test_is_git_worktree
# #############################################################################


class Test_is_git_worktree(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that is_git_worktree() returns a boolean.
        """
        result = hgit.is_git_worktree()
        self.assertIsInstance(result, bool)

    def test2(self) -> None:
        """
        Test that is_git_worktree() returns consistent value.
        """
        result1 = hgit.is_git_worktree()
        result2 = hgit.is_git_worktree()
        self.assertEqual(result1, result2)

    def test3(self) -> None:
        """
        Test that is_git_worktree() returns same value for subdirectories.
        """
        scratch_dir = self.get_scratch_space()
        root_result = hgit.is_git_worktree()
        subdir_result = hgit.is_git_worktree(scratch_dir)
        self.assertEqual(root_result, subdir_result)


# #############################################################################
# Test_parse_worktree_list
# #############################################################################


class Test_parse_worktree_list(hunitest.TestCase):
    def helper(self, branch: str, expected: object) -> None:
        # Prepare inputs.
        txt = """
        worktree /src/repo
        HEAD 1111111111111111111111111111111111111111
        branch refs/heads/master

        worktree /src/repo_788
        HEAD 2222222222222222222222222222222222222222
        branch refs/heads/UmdTask788_Racket_sports

        worktree /src/repo_detached
        HEAD 3333333333333333333333333333333333333333
        detached
        """
        txt = "\n".join(line.strip() for line in txt.split("\n"))
        # Run test.
        actual = hgit.parse_worktree_list(txt, branch)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that the worktree of a branch is found.
        """
        self.helper("UmdTask788_Racket_sports", "/src/repo_788")

    def test2(self) -> None:
        """
        Test that the main client is found as the worktree of its branch.
        """
        self.helper("master", "/src/repo")

    def test3(self) -> None:
        """
        Test that a branch without worktree returns `None`.
        """
        self.helper("UmdTask999_Other", None)

    def test4(self) -> None:
        """
        Test that a branch name that is a prefix of another one is not matched.
        """
        self.helper("UmdTask788", None)


# #############################################################################
# Test_get_default_worktree_dir
# #############################################################################


class Test_get_default_worktree_dir(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the dir is `<repo>_<issue_id>`.
        """
        # Prepare inputs.
        branch = "UmdTask788_Racket_sports_Change_color_of_heatmaps"
        git_root = "/src/umd_classes1"
        # Run test.
        actual = hgit.get_default_worktree_dir(branch, git_root=git_root)
        # Check outputs.
        expected = "/src/umd_classes1_788"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a branch without issue number uses the branch name.
        """
        # Prepare inputs.
        branch = "feature/fix_bug"
        git_root = "/src/umd_classes1"
        # Run test.
        actual = hgit.get_default_worktree_dir(branch, git_root=git_root)
        # Check outputs.
        expected = "/src/umd_classes1_feature_fix_bug"
        self.assert_equal(actual, expected)


# #############################################################################
# Git repos with a remote
# #############################################################################


def _git(git_dir: str, args: str) -> str:
    """
    Run a git command in a dir and return its output.

    :param git_dir: dir of the git repo
    :param args: arguments of the git command
    :return: output of the command, without trailing newline
    """
    cmd = (
        f"git -C {git_dir} -c user.name=test -c user.email=test@example.com "
        f"{args}"
    )
    _, txt = hsystem.system_to_string(cmd)
    return txt.strip()


class _GitRepoWithRemoteTestCase(hunitest.TestCase):
    """
    Create a client cloned from a bare `origin`, with `master` pushed.
    """

    def set_up_test(self) -> None:
        scratch_dir = self.get_scratch_space()
        self.origin_dir = os.path.join(scratch_dir, "origin.git")
        self.client_dir = os.path.join(scratch_dir, "client")
        hsystem.system(f"git init --bare -b master {self.origin_dir}")
        hsystem.system(f"git clone {self.origin_dir} {self.client_dir}")
        _git(self.client_dir, "checkout -b master")
        _git(self.client_dir, "commit --allow-empty -m init")
        _git(self.client_dir, "push origin master")

    def push_branch(self, branch: str) -> str:
        """
        Create a branch with one commit, push it, and return to master.

        :param branch: name of the branch
        :return: hash of the tip of the branch
        """
        _git(self.client_dir, f"checkout -b {branch}")
        _git(self.client_dir, f"commit --allow-empty -m {branch}")
        _git(self.client_dir, f"push origin {branch}")
        tip = _git(self.client_dir, "rev-parse HEAD")
        _git(self.client_dir, "checkout master")
        return tip

    def get_worktree_dir(self, suffix: str) -> str:
        worktree_dir = os.path.join(self.get_scratch_space(), f"client_{suffix}")
        return worktree_dir


# #############################################################################
# Test_exists_on_ref
# #############################################################################


class Test_exists_on_ref(_GitRepoWithRemoteTestCase):
    def test1(self) -> None:
        """
        Test that a path tracked on the ref exists.
        """
        # Prepare inputs.
        self.set_up_test()
        hio.to_file(os.path.join(self.client_dir, "a.txt"), "a")
        _git(self.client_dir, "add a.txt")
        _git(self.client_dir, "commit -m add_a")
        # Run test.
        actual = hgit.exists_on_ref("master", "a.txt", git_root=self.client_dir)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Test that a path not in the tree of the ref does not exist.
        """
        # Prepare inputs.
        self.set_up_test()
        # Run test.
        actual = hgit.exists_on_ref("master", "a.txt", git_root=self.client_dir)
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test that a path is looked up on the passed ref, not on the checkout.
        """
        # Prepare inputs.
        self.set_up_test()
        hio.to_file(os.path.join(self.client_dir, "a.txt"), "a")
        _git(self.client_dir, "add a.txt")
        _git(self.client_dir, "commit -m add_a")
        # Run test.
        actual = hgit.exists_on_ref(
            "origin/master", "a.txt", git_root=self.client_dir
        )
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_create_worktree
# #############################################################################


class Test_create_worktree(_GitRepoWithRemoteTestCase):
    def test1(self) -> None:
        """
        Test creating the worktree of a branch that exists only on the remote.
        """
        # Prepare inputs.
        self.set_up_test()
        branch = "UmdTask1_Remote_only"
        tip = self.push_branch(branch)
        _git(self.client_dir, f"branch -D {branch}")
        worktree_dir = self.get_worktree_dir("1")
        # Run test.
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=self.client_dir,
            submodule_paths=[],
        )
        # Check outputs.
        self.assert_equal(hgit.get_branch_name(worktree_dir), branch)
        self.assert_equal(_git(worktree_dir, "rev-parse HEAD"), tip)
        # The local branch tracks the remote one.
        actual = _git(worktree_dir, "rev-parse --abbrev-ref @{upstream}")
        self.assert_equal(actual, f"origin/{branch}")

    def test2(self) -> None:
        """
        Test creating the worktree of a branch that exists locally and on the
        remote.
        """
        # Prepare inputs.
        self.set_up_test()
        branch = "UmdTask2_Local_and_remote"
        tip = self.push_branch(branch)
        worktree_dir = self.get_worktree_dir("2")
        # Run test.
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=self.client_dir,
            submodule_paths=[],
        )
        # Check outputs.
        self.assert_equal(hgit.get_branch_name(worktree_dir), branch)
        self.assert_equal(_git(worktree_dir, "rev-parse HEAD"), tip)

    def test3(self) -> None:
        """
        Test that a local branch behind the remote one is fast-forwarded.
        """
        # Prepare inputs.
        self.set_up_test()
        branch = "UmdTask3_Behind"
        old_tip = self.push_branch(branch)
        _git(self.client_dir, f"checkout {branch}")
        _git(self.client_dir, "commit --allow-empty -m new_commit")
        _git(self.client_dir, f"push origin {branch}")
        new_tip = _git(self.client_dir, "rev-parse HEAD")
        _git(self.client_dir, "checkout master")
        _git(self.client_dir, f"branch -f {branch} {old_tip}")
        worktree_dir = self.get_worktree_dir("3")
        # Run test.
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=self.client_dir,
            submodule_paths=[],
        )
        # Check outputs.
        self.assert_equal(_git(worktree_dir, "rev-parse HEAD"), new_tip)

    def test4(self) -> None:
        """
        Test creating the worktree of a branch that was not pushed yet.
        """
        # Prepare inputs.
        self.set_up_test()
        branch = "UmdTask4_Not_pushed"
        _git(self.client_dir, f"checkout -b {branch}")
        _git(self.client_dir, "commit --allow-empty -m local_commit")
        tip = _git(self.client_dir, "rev-parse HEAD")
        _git(self.client_dir, "checkout master")
        worktree_dir = self.get_worktree_dir("4")
        # Run test.
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=self.client_dir,
            submodule_paths=[],
        )
        # Check outputs.
        self.assert_equal(hgit.get_branch_name(worktree_dir), branch)
        self.assert_equal(_git(worktree_dir, "rev-parse HEAD"), tip)

    def test5(self) -> None:
        """
        Test that a dry run does not create the worktree.
        """
        # Prepare inputs.
        self.set_up_test()
        branch = "UmdTask5_Dry_run"
        self.push_branch(branch)
        worktree_dir = self.get_worktree_dir("5")
        # Run test.
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=self.client_dir,
            submodule_paths=[],
            dry_run=True,
        )
        # Check outputs.
        self.assertFalse(os.path.exists(worktree_dir))

    def test6(self) -> None:
        """
        Test that a branch that exists neither locally nor on the remote
        asserts.
        """
        # Prepare inputs.
        self.set_up_test()
        worktree_dir = self.get_worktree_dir("6")
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            hgit.create_worktree(
                "UmdTask6_Missing",
                worktree_dir,
                git_root=self.client_dir,
                submodule_paths=[],
            )
        # Check outputs.
        self.assertIn("doesn't exist locally or on 'origin'", str(cm.exception))


# #############################################################################
# Test_sync_worktree
# #############################################################################


class Test_sync_worktree(_GitRepoWithRemoteTestCase):
    def helper(self, *, is_dirty: bool) -> str:
        """
        Make a worktree fall behind its remote branch, then sync it.

        :param is_dirty: whether the worktree has uncommitted changes
        :return: hash of the tip of the remote branch
        """
        # Prepare inputs.
        self.set_up_test()
        branch = "UmdTask7_Sync"
        self.push_branch(branch)
        worktree_dir = self.get_worktree_dir("7")
        hgit.create_worktree(
            branch,
            worktree_dir,
            git_root=self.client_dir,
            submodule_paths=[],
        )
        # Push a new commit to the remote branch from another clone.
        other_dir = os.path.join(self.get_scratch_space(), "other")
        hsystem.system(f"git clone {self.origin_dir} {other_dir}")
        _git(other_dir, f"checkout {branch}")
        _git(other_dir, "commit --allow-empty -m new_commit")
        _git(other_dir, f"push origin {branch}")
        new_tip = _git(other_dir, "rev-parse HEAD")
        _git(worktree_dir, "fetch origin")
        if is_dirty:
            hio.to_file(os.path.join(worktree_dir, "dirty.txt"), "dirty")
            _git(worktree_dir, "add dirty.txt")
        # Run test.
        hgit.sync_worktree(branch, worktree_dir)
        self.worktree_dir = worktree_dir
        return new_tip

    def test1(self) -> None:
        """
        Test that a clean worktree is fast-forwarded to the remote branch.
        """
        # Run test.
        new_tip = self.helper(is_dirty=False)
        # Check outputs.
        self.assert_equal(_git(self.worktree_dir, "rev-parse HEAD"), new_tip)

    def test2(self) -> None:
        """
        Test that a worktree with local changes is left as it is.
        """
        # Run test.
        new_tip = self.helper(is_dirty=True)
        # Check outputs.
        self.assertNotEqual(_git(self.worktree_dir, "rev-parse HEAD"), new_tip)
