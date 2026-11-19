import logging
import os
from typing import Any, List

import pandas as pd
import pytest

import helpers.hgoogle_drive_api as hgodrapi
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# The tests that use a Google account are disabled by default, since they need
# credentials and network and they create files on Google Drive. To run them:
# > RUN_GSHEET_TESTS=1 pytest helpers/test/test_hgoogle_drive_api.py
_SKIP_GSHEET_TESTS = pytest.mark.skipif(
    os.environ.get("RUN_GSHEET_TESTS", "0") == "0",
    reason="Needs Google credentials and network: set RUN_GSHEET_TESTS=1",
)


# #############################################################################
# Test_CELL_STYLE_TO_WRAP_STRATEGY
# #############################################################################


class Test_CELL_STYLE_TO_WRAP_STRATEGY(hunitest.TestCase):
    """
    Test `hgodrapi.CELL_STYLE_TO_WRAP_STRATEGY`.
    """

    def test1(self) -> None:
        """
        Test that the cell styles map to the Sheets API wrap strategies.
        """
        # Prepare outputs.
        expected = (
            "{'clip': 'CLIP', 'wrap': 'WRAP', 'overflow': 'OVERFLOW_CELL'}"
        )
        # Run test.
        actual = hgodrapi.CELL_STYLE_TO_WRAP_STRATEGY
        # Check outputs.
        self.assert_equal(str(actual), expected)


# #############################################################################
# Test_get_tab_csv_file_name
# #############################################################################


class Test_get_tab_csv_file_name(hunitest.TestCase):
    """
    Test `hgodrapi.get_tab_csv_file_name()`.
    """

    def helper(
        self, output_file: str, tab_id: int, tab_name: str, expected: str
    ) -> None:
        """
        Test helper for `get_tab_csv_file_name()`.

        :param output_file: output file passed by the user
        :param tab_id: position of the tab
        :param tab_name: name of the tab
        :param expected: expected name of the file storing the tab
        """
        # Run test.
        actual = hgodrapi.get_tab_csv_file_name(output_file, tab_id, tab_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a simple tab name.
        """
        # Prepare inputs.
        output_file = "data.csv"
        tab_id = 0
        tab_name = "Sheet1"
        # Prepare outputs.
        expected = "data.0.Sheet1.csv"
        # Run test.
        self.helper(output_file, tab_id, tab_name, expected)

    def test2(self) -> None:
        """
        Test that the spaces in the tab name are kept.
        """
        # Prepare inputs.
        output_file = "data.csv"
        tab_id = 1
        tab_name = "My Data"
        # Prepare outputs.
        expected = "data.1.My Data.csv"
        # Run test.
        self.helper(output_file, tab_id, tab_name, expected)

    def test3(self) -> None:
        """
        Test an output file without the `.csv` extension.
        """
        # Prepare inputs.
        output_file = "data"
        tab_id = 2
        tab_name = "tab"
        # Prepare outputs.
        expected = "data.2.tab.csv"
        # Run test.
        self.helper(output_file, tab_id, tab_name, expected)

    def test4(self) -> None:
        """
        Test that an output file with a dir and another extension is kept and
        that the characters that are not safe in a file name are encoded.
        """
        # Prepare inputs.
        output_file = "out_dir/data.v2"
        tab_id = 3
        tab_name = "a/b:c"
        # Prepare outputs.
        expected = "out_dir/data.v2.3.a%2Fb%3Ac.csv"
        # Run test.
        self.helper(output_file, tab_id, tab_name, expected)

    def test5(self) -> None:
        """
        Test that dots and dashes in the tab name are kept.
        """
        # Prepare inputs.
        output_file = "data.csv"
        tab_id = 4
        tab_name = "my-tab.v2"
        # Prepare outputs.
        expected = "data.4.my-tab.v2.csv"
        # Run test.
        self.helper(output_file, tab_id, tab_name, expected)

    def test6(self) -> None:
        """
        Test that the `%` in the tab name is encoded, to decode it without
        ambiguity.
        """
        # Prepare inputs.
        output_file = "data.csv"
        tab_id = 5
        tab_name = "100%"
        # Prepare outputs.
        expected = "data.5.100%25.csv"
        # Run test.
        self.helper(output_file, tab_id, tab_name, expected)


# #############################################################################
# Test_get_tab_csv_files
# #############################################################################


class Test_get_tab_csv_files(hunitest.TestCase):
    """
    Test `hgodrapi.get_tab_csv_files()`.
    """

    def helper(
        self, file_names: List[str], input_file: str, expected: str
    ) -> None:
        """
        Test helper for `get_tab_csv_files()`.

        :param file_names: names of the files to create in the scratch dir
        :param input_file: file passed by the user, in the scratch dir
        :param expected: expected `(tab_id, tab_name, file)` list, with the
            files relative to the scratch dir
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        for file_name in file_names:
            hio.to_file(os.path.join(scratch_dir, file_name), "")
        input_file = os.path.join(scratch_dir, input_file)
        # Run test.
        actual = hgodrapi.get_tab_csv_files(input_file)
        # Check outputs.
        actual = [
            (tab_id, tab_name, os.path.relpath(tab_file, scratch_dir))
            for tab_id, tab_name, tab_file in actual
        ]
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test that the files are sorted by the numeric tab ID and the files that
        do not match are ignored.
        """
        # Prepare inputs.
        file_names = [
            "data.2.b.csv",
            "data.10.c.csv",
            "data.0.a.csv",
            "data.csv",
            "data.x.d.csv",
            "other.0.e.csv",
        ]
        input_file = "data.csv"
        # Prepare outputs.
        expected = (
            "[(0, 'a', 'data.0.a.csv'), (2, 'b', 'data.2.b.csv'), "
            "(10, 'c', 'data.10.c.csv')]"
        )
        # Run test.
        self.helper(file_names, input_file, expected)

    def test2(self) -> None:
        """
        Test that the tab names are decoded and that the input file can have no
        extension.
        """
        # Prepare inputs.
        file_names = [
            "data.0.My Data.csv",
            "data.1.a%2Fb%3Ac.csv",
            "data.2.100%25.csv",
        ]
        input_file = "data"
        # Prepare outputs.
        expected = (
            "[(0, 'My Data', 'data.0.My Data.csv'), "
            "(1, 'a/b:c', 'data.1.a%2Fb%3Ac.csv'), "
            "(2, '100%', 'data.2.100%25.csv')]"
        )
        # Run test.
        self.helper(file_names, input_file, expected)

    def test3(self) -> None:
        """
        Test that the function is the inverse of `get_tab_csv_file_name()`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "data.csv")
        tab_names = [
            "Sheet1",
            "My Data",
            "a/b:c",
            "100%",
            "my-tab.v2",
            "x.csv",
            'q?"<>|\\*',
            "%2F",
        ]
        for tab_id, tab_name in enumerate(tab_names):
            tab_file = hgodrapi.get_tab_csv_file_name(
                input_file, tab_id, tab_name
            )
            hio.to_file(tab_file, "")
        # Prepare outputs.
        expected = tab_names
        # Run test.
        actual = hgodrapi.get_tab_csv_files(input_file)
        # Check outputs.
        actual_tab_names = [tab_name for _, tab_name, _ in actual]
        self.assert_equal(str(actual_tab_names), str(expected))
        actual_tab_ids = [tab_id for tab_id, _, _ in actual]
        self.assert_equal(str(actual_tab_ids), str(list(range(len(tab_names)))))

    def test4(self) -> None:
        """
        Test that two files with the same tab ID fail.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        for file_name in ["data.1.a.csv", "data.1.b.csv"]:
            hio.to_file(os.path.join(scratch_dir, file_name), "")
        input_file = os.path.join(scratch_dir, "data.csv")
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hgodrapi.get_tab_csv_files(input_file)
        self.assertIn("Duplicated tab IDs", str(cm.exception))


# #############################################################################
# Test_to_gsheet
# #############################################################################


class Test_to_gsheet(hunitest.TestCase):
    """
    Test `hgodrapi.to_gsheet()`.
    """

    def test1(self) -> None:
        """
        Test that an invalid cell style fails before using the Google Sheet.
        """
        # Prepare inputs.
        df = pd.DataFrame({"col1": [1]})
        url = "https://docs.google.com/spreadsheets/d/not_used/edit"
        cell_style = "invalid_style"
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hgodrapi.to_gsheet(df, url, cell_style=cell_style)
        self.assertIn("Invalid cell style", str(cm.exception))


# #############################################################################
# Test_delete_gdrive_file
# #############################################################################


@_SKIP_GSHEET_TESTS
class Test_delete_gdrive_file(hunitest.TestCase):
    """
    Test `hgodrapi.delete_gdrive_file()` on files in a temporary Google Drive
    folder.
    """

    _credentials: Any
    _folder_id: str

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary Google Drive folder holding the test files.
        """
        pytest.importorskip("gspread")
        pytest.importorskip("googleapiclient")
        cls._credentials = hgodrapi.get_credentials()
        cls._folder_id = hgodrapi.create_tmp_gdrive_folder(
            "tmp_test_delete_gdrive_file", credentials=cls._credentials
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete the temporary folder with all the test files, even when a test
        fails.
        """
        hgodrapi.delete_gdrive_file(cls._folder_id, credentials=cls._credentials)

    def helper(self, file_id: str) -> None:
        """
        Check that a file is not found on Google Drive.

        :param file_id: ID of the file that must not exist
        """
        # Import here, since the package is not always installed.
        import googleapiclient.errors as goerr

        gdrive_service = hgodrapi._get_gdrive_service(self._credentials)
        with self.assertRaises(goerr.HttpError) as cm:
            gdrive_service.files().get(
                fileId=file_id, supportsAllDrives=True
            ).execute()
        self.assertEqual(cm.exception.resp.status, 404)

    def test1(self) -> None:
        """
        Test deleting a Google Sheet.
        """
        # Prepare inputs.
        file_id = hgodrapi.create_or_overwrite_with_timestamp(
            "tmp_test_sheet",
            self._folder_id,
            file_type="sheets",
            credentials=self._credentials,
        )
        # Run test.
        hgodrapi.delete_gdrive_file(file_id, credentials=self._credentials)
        # Check outputs.
        self.helper(file_id)

    def test2(self) -> None:
        """
        Test that deleting a folder also deletes the files it contains.
        """
        # Prepare inputs.
        folder_id = hgodrapi.create_google_drive_folder(
            "tmp_test_folder", self._folder_id, credentials=self._credentials
        )
        file_id = hgodrapi.create_or_overwrite_with_timestamp(
            "tmp_test_sheet",
            folder_id,
            file_type="sheets",
            credentials=self._credentials,
        )
        # Run test.
        hgodrapi.delete_gdrive_file(folder_id, credentials=self._credentials)
        # Check outputs.
        self.helper(folder_id)
        self.helper(file_id)


# #############################################################################
# Test_delete_tab_from_gsheet
# #############################################################################


@_SKIP_GSHEET_TESTS
class Test_delete_tab_from_gsheet(hunitest.TestCase):
    """
    Test `hgodrapi.delete_tab_from_gsheet()` on a temporary Google Sheet.
    """

    _credentials: Any
    _folder_id: str

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary Google Drive folder holding the test Google Sheet.
        """
        pytest.importorskip("gspread")
        cls._credentials = hgodrapi.get_credentials()
        cls._folder_id = hgodrapi.create_tmp_gdrive_folder(
            "tmp_test_delete_tab", credentials=cls._credentials
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete the temporary folder with the Google Sheet, even when a test
        fails.
        """
        hgodrapi.delete_gdrive_file(cls._folder_id, credentials=cls._credentials)

    def test1(self) -> None:
        """
        Test deleting one of the tabs.
        """
        # Prepare inputs.
        url = hgodrapi.create_tmp_gsheet(
            folder_id=self._folder_id, credentials=self._credentials
        )
        df = pd.DataFrame({"col1": [1]})
        hgodrapi.to_gsheet(
            df, url, tab_name="extra", credentials=self._credentials
        )
        # Prepare outputs.
        expected = "['Sheet1']"
        # Run test.
        hgodrapi.delete_tab_from_gsheet(
            url, "extra", credentials=self._credentials
        )
        # Check outputs.
        actual = hgodrapi.get_tabs_from_gsheet(
            url, credentials=self._credentials
        )
        self.assert_equal(str(actual), expected)


# #############################################################################
# Test_reorder_tabs_in_gsheet
# #############################################################################


@_SKIP_GSHEET_TESTS
class Test_reorder_tabs_in_gsheet(hunitest.TestCase):
    """
    Test `hgodrapi.reorder_tabs_in_gsheet()` on a temporary Google Sheet.
    """

    _credentials: Any
    _folder_id: str

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary Google Drive folder holding the test Google Sheet.
        """
        pytest.importorskip("gspread")
        cls._credentials = hgodrapi.get_credentials()
        cls._folder_id = hgodrapi.create_tmp_gdrive_folder(
            "tmp_test_reorder_tabs", credentials=cls._credentials
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete the temporary folder with the Google Sheet, even when a test
        fails.
        """
        hgodrapi.delete_gdrive_file(cls._folder_id, credentials=cls._credentials)

    def test1(self) -> None:
        """
        Test that the passed tabs come first, in order, followed by the other
        tabs.
        """
        # Prepare inputs.
        url = hgodrapi.create_tmp_gsheet(
            folder_id=self._folder_id, credentials=self._credentials
        )
        df = pd.DataFrame({"col1": [1]})
        for tab_name in ["b", "c"]:
            hgodrapi.to_gsheet(
                df, url, tab_name=tab_name, credentials=self._credentials
            )
        tab_names = ["c", "Sheet1"]
        # Prepare outputs.
        expected = "['c', 'Sheet1', 'b']"
        # Run test.
        hgodrapi.reorder_tabs_in_gsheet(
            url, tab_names, credentials=self._credentials
        )
        # Check outputs.
        actual = hgodrapi.get_tabs_from_gsheet(
            url, credentials=self._credentials
        )
        self.assert_equal(str(actual), expected)
