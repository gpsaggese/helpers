import logging
import os
import unittest.mock as umock

import dev_scripts_helpers.thin_client.thin_client_utils as dshtctcut
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_get_python_version
# #############################################################################


class Test_get_python_version(hunitest.TestCase):
    """
    Test reading the Python version from `.python-version`.
    """

    def helper(self, file_content: str) -> str:
        """
        Run `get_python_version()` on a `helpers` root with a given file.

        :param file_content: content of `.python-version`
        :return: version returned by the function
        """
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, ".python-version")
        hio.to_file(file_name, file_content)
        with umock.patch.object(
            hgit, "find_helpers_root", return_value=scratch_dir
        ):
            actual = dshtctcut.get_python_version()
        return actual

    def test1(self) -> None:
        """
        Test that the `.python-version` of `helpers` has a valid version.
        """
        # Run test.
        actual = dshtctcut.get_python_version()
        # Check outputs.
        version_parts = actual.split(".")
        self.assertIn(len(version_parts), [2, 3])
        self.assertTrue(all(part.isdigit() for part in version_parts))

    def test2(self) -> None:
        """
        Test that the trailing new line is removed.
        """
        # Prepare inputs.
        file_content = "3.14\n"
        # Prepare outputs.
        expected = "3.14"
        # Run test.
        actual = self.helper(file_content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test a version with the patch number.
        """
        # Prepare inputs.
        file_content = "3.14.7\n"
        # Prepare outputs.
        expected = "3.14.7"
        # Run test.
        actual = self.helper(file_content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that a version with a wrong format is rejected.
        """
        # Prepare inputs.
        file_content = "python3.14\n"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            self.helper(file_content)
        # Check outputs.
        self.assertIn("Invalid version 'python3.14'", str(cm.exception))

    def test5(self) -> None:
        """
        Test that an empty file is rejected.
        """
        # Prepare inputs.
        file_content = ""
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            self.helper(file_content)
        # Check outputs.
        self.assertIn("Invalid version ''", str(cm.exception))


# #############################################################################
# Test_get_python_exec
# #############################################################################


class Test_get_python_exec(hunitest.TestCase):
    """
    Test the name of the interpreter for a version.
    """

    def helper(self, version: str, expected: str) -> None:
        """
        Check the interpreter name for a version.

        :param version: Python version
        :param expected: expected name of the interpreter
        """
        actual = dshtctcut.get_python_exec(version)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a version with major and minor numbers.
        """
        self.helper("3.14", "python3.14")

    def test2(self) -> None:
        """
        Test that the patch number is ignored.
        """
        self.helper("3.14.7", "python3.14")


# #############################################################################
# Test_python_version_matches
# #############################################################################


class Test_python_version_matches(hunitest.TestCase):
    """
    Test the check of an interpreter version against the required one.
    """

    def helper(self, required: str, actual: str, expected: bool) -> None:
        """
        Check the result of the comparison.

        :param required: version from `.python-version`
        :param actual: version of the interpreter
        :param expected: expected result of the comparison
        """
        actual_result = dshtctcut.python_version_matches(required, actual)
        self.assertEqual(actual_result, expected)

    def test1(self) -> None:
        """
        Test that a minor version is satisfied by any patch version.
        """
        self.helper("3.14", "3.14.7", True)

    def test2(self) -> None:
        """
        Test that a different minor version is rejected.
        """
        self.helper("3.14", "3.13.2", False)

    def test3(self) -> None:
        """
        Test that the same version is accepted.
        """
        self.helper("3.14.7", "3.14.7", True)

    def test4(self) -> None:
        """
        Test that a different patch version is rejected when it is required.
        """
        self.helper("3.14.7", "3.14.6", False)

    def test5(self) -> None:
        """
        Test that `3.1` does not match `3.14` (compare numbers, not prefixes).
        """
        self.helper("3.1", "3.14.7", False)
