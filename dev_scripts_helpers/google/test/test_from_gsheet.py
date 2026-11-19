import logging
import os
from typing import Any, List
from unittest import mock

import pandas as pd
import pytest

import dev_scripts_helpers.google.from_gsheet as dshgofrgs
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# The tests that use a Google account are disabled by default, since they need
# credentials and network and they create files on Google Drive. To run them:
# > RUN_GSHEET_TESTS=1 pytest dev_scripts_helpers/google/test/test_from_gsheet.py
_SKIP_GSHEET_TESTS = pytest.mark.skipif(
    os.environ.get("RUN_GSHEET_TESTS", "0") == "0",
    reason="Needs Google credentials and network: set RUN_GSHEET_TESTS=1",
)


# #############################################################################
# Test_from_gsheet_py
# #############################################################################


@_SKIP_GSHEET_TESTS
class Test_from_gsheet_py(hunitest.TestCase):
    """
    Test the `from_gsheet.py` executable on a temporary Google Sheet.

    The Google Sheet is created once for the class, in a temporary Google Drive
    folder that is deleted at the end. It has the tabs:
    - `Sheet1`: no cells
    - `data`: header and 2 rows
    - `My Data`: header and 2 rows
    - `header_only`: only the header
    """

    _credentials: Any
    _folder_id: str
    _url: str

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary Google Sheet with 4 tabs, 2 of them with no rows.
        """
        pytest.importorskip("gspread")
        cls._credentials = hgodrapi.get_credentials()
        # Create the temporary folder and the Google Sheet inside it.
        cls._folder_id = hgodrapi.create_tmp_gdrive_folder(
            "tmp_test_from_gsheet", credentials=cls._credentials
        )
        cls._url = hgodrapi.create_tmp_gsheet(
            folder_id=cls._folder_id, credentials=cls._credentials
        )
        # Fill the tabs. A new Google Sheet has the empty tab `Sheet1`.
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        hgodrapi.to_gsheet(
            df, cls._url, tab_name="data", credentials=cls._credentials
        )
        hgodrapi.to_gsheet(
            df, cls._url, tab_name="My Data", credentials=cls._credentials
        )
        df_header_only = pd.DataFrame(columns=pd.Index(["col1", "col2"]))
        hgodrapi.to_gsheet(
            df_header_only,
            cls._url,
            tab_name="header_only",
            credentials=cls._credentials,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete the temporary folder with the Google Sheet, even when a test
        fails.
        """
        hgodrapi.delete_gdrive_file(cls._folder_id, credentials=cls._credentials)

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `from_gsheet._main()` with a mocked `sys.argv`.

        :param argv: command-line arguments, including the script name
        """
        parser = dshgofrgs._parse()
        with mock.patch("sys.argv", argv):
            dshgofrgs._main(parser)

    def _get_files_content(self, dir_name: str) -> str:
        """
        Get the name and the content of all the files in a dir.

        :param dir_name: dir to list
        :return: one line for each file, sorted by name
            ```
            data.1.data.csv: 'col1,col2\\n1,a\\n2,b\\n'
            ```
        """
        lines = []
        for file_name in sorted(os.listdir(dir_name)):
            content = hio.from_file(os.path.join(dir_name, file_name))
            lines.append(f"{file_name}: {content!r}")
        return "\n".join(lines)

    def test1(self) -> None:
        """
        Test downloading one tab by name.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "data.csv")
        argv = [
            "from_gsheet.py",
            "--url",
            self._url,
            "--tabname",
            "data",
            "--output_file",
            output_file,
        ]
        # Prepare outputs.
        expected = r"""
        data.csv: 'col1,col2\n1,a\n2,b\n'
        """
        expected = hprint.dedent(expected)
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = self._get_files_content(scratch_dir)
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test downloading all the tabs, including the empty ones.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "data.csv")
        argv = [
            "from_gsheet.py",
            "--url",
            self._url,
            "--tabname",
            "_ALL_",
            "--output_file",
            output_file,
        ]
        # Prepare outputs.
        expected = r"""
        data.0.Sheet1.csv: ''
        data.1.data.csv: 'col1,col2\n1,a\n2,b\n'
        data.2.My Data.csv: 'col1,col2\n1,a\n2,b\n'
        data.3.header_only.csv: 'col1,col2\n'
        """
        expected = hprint.dedent(expected)
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = self._get_files_content(scratch_dir)
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that downloading all the tabs ignores the `gid` in the URL.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "data.csv")
        spreadsheet_id = hgodrapi._extract_file_id_from_url(self._url)
        gid = hgodrapi._get_gsheet_id(
            self._credentials, spreadsheet_id, tab_name="data"
        )
        url = f"{self._url}?gid={gid}#gid={gid}"
        argv = [
            "from_gsheet.py",
            "--url",
            url,
            "--tabname",
            "_ALL_",
            "--output_file",
            output_file,
        ]
        # Prepare outputs.
        expected = """
        ['data.0.Sheet1.csv', 'data.1.data.csv', 'data.2.My Data.csv', 'data.3.header_only.csv']
        """
        expected = hprint.dedent(expected)
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = str(sorted(os.listdir(scratch_dir)))
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that an existing file stops the download of all the tabs without
        writing any file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "data.csv")
        existing_file = os.path.join(scratch_dir, "data.1.data.csv")
        hio.to_file(existing_file, "old content")
        argv = [
            "from_gsheet.py",
            "--url",
            self._url,
            "--tabname",
            "_ALL_",
            "--output_file",
            output_file,
        ]
        # Prepare outputs.
        expected = """
        data.1.data.csv: 'old content'
        """
        expected = hprint.dedent(expected)
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            self._run_main(argv)
        # Check outputs.
        self.assertIn("use --overwrite", str(cm.exception))
        actual = self._get_files_content(scratch_dir)
        self.assert_equal(actual, expected)
