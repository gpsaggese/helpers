import pytest

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

# #############################################################################
# Test_sync_google_group_py
# #############################################################################


@pytest.mark.slow(reason="Greater than 5s")
class Test_sync_google_group_py(hunitest.TestCase):
    """
    End-to-end test of the `uv run` script `sync_google_group.py`.

    This is not skipped when the script dependencies are missing, since `uv`
    installs them on the fly.
    """

    def test_help(self) -> None:
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("sync_google_group.py")
        cmd = f"uv run {exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
