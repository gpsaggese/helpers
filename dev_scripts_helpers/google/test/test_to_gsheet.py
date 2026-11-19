import logging
import os
import time
from typing import Any, List
from unittest import mock

import pandas as pd
import pytest

import helpers.hgoogle_drive_api as hgodrapi
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import dev_scripts_helpers.google.from_gsheet as dshgofrgs
import dev_scripts_helpers.google.to_gsheet as dshgotgs

_LOG = logging.getLogger(__name__)

# The tests that use a Google account are disabled by default, since they need
# credentials and network and they create files on Google Drive. To run them:
# > RUN_GSHEET_TESTS=1 pytest dev_scripts_helpers/google/test/test_to_gsheet.py
# Note that each run of the executable sends several write requests to the
# Google Sheets API, which limits them per minute.
_SKIP_GSHEET_TESTS = pytest.mark.skipif(
    os.environ.get("RUN_GSHEET_TESTS", "0") == "0",
    reason="Needs Google credentials and network: set RUN_GSHEET_TESTS=1",
)


def _wait_for_quota() -> None:
    """
    Wait to stay under the Google Sheets API quota.

    The API limits the read requests per minute and each run of the executables
    sends many of them, so the tests would fail with a `429` error when run one
    after the other.
    """
    time.sleep(30)


# #############################################################################
# Test__parse
# #############################################################################


class Test__parse(hunitest.TestCase):
    """
    Test the `dshgotgs._parse()` parser of the `to_gsheet.py` executable.
    """

    def helper(self, argv: List[str], expected: str) -> None:
        """
        Test helper for the formatting options.

        :param argv: command-line arguments, without the script name
        :param expected: expected `(freeze_header, bold_header, cell_style)`
        """
        # Run test.
        parser = dshgotgs._parse()
        args = parser.parse_args(argv)
        # Check outputs.
        actual = (args.freeze_header, args.bold_header, args.cell_style)
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test that the header is frozen and bold and the cells are clipped by
        default.
        """
        # Prepare inputs.
        argv = ["--input_file", "data.csv"]
        # Prepare outputs.
        expected = "(True, True, 'clip')"
        # Run test.
        self.helper(argv, expected)

    def test2(self) -> None:
        """
        Test turning off the freeze and the bold and wrapping the cells.
        """
        # Prepare inputs.
        argv = [
            "--input_file",
            "data.csv",
            "--no_freeze_header",
            "--no_bold_header",
            "--cell_style",
            "wrap",
        ]
        # Prepare outputs.
        expected = "(False, False, 'wrap')"
        # Run test.
        self.helper(argv, expected)


# #############################################################################
# Test__read_csv
# #############################################################################


class Test__read_csv(hunitest.TestCase):
    """
    Test `dshgotgs._read_csv()`.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `_read_csv()`.

        :param content: content of the CSV file
        :param expected: expected `(shape, columns)` of the DataFrame
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        csv_file = os.path.join(scratch_dir, "data.csv")
        hio.to_file(csv_file, content)
        # Run test.
        df = dshgotgs._read_csv(csv_file)
        # Check outputs.
        actual = str((df.shape, list(df.columns)))
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a file with the header and one row.
        """
        # Prepare inputs.
        content = "col1,col2\n1,a\n"
        # Prepare outputs.
        expected = "((1, 2), ['col1', 'col2'])"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test a file with only the header.
        """
        # Prepare inputs.
        content = "col1,col2\n"
        # Prepare outputs.
        expected = "((0, 2), ['col1', 'col2'])"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test an empty file, i.e., a tab with no cells.
        """
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = "((0, 0), [])"
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_to_gsheet_py
# #############################################################################


@_SKIP_GSHEET_TESTS
class Test_to_gsheet_py(hunitest.TestCase):
    """
    Test the `to_gsheet.py` executable on a temporary Google Sheet.

    The Google Sheet is created once for the class, in a temporary Google Drive
    folder that is deleted at the end. Each test writes in its own tab.
    """

    _credentials: Any
    _folder_id: str
    _url: str

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary Google Sheet.
        """
        pytest.importorskip("gspread")
        cls._credentials = hgodrapi.get_credentials()
        # Create the temporary folder and the Google Sheet inside it.
        cls._folder_id = hgodrapi.create_tmp_gdrive_folder(
            "tmp_test_to_gsheet", credentials=cls._credentials
        )
        cls._url = hgodrapi.create_tmp_gsheet(
            folder_id=cls._folder_id, credentials=cls._credentials
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete the temporary folder with the Google Sheet, even when a test
        fails.
        """
        hgodrapi.delete_gdrive_file(cls._folder_id, credentials=cls._credentials)

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):  # type: ignore[no-untyped-def]
        """
        Setup and teardown for each test.
        """
        # Run before each test.
        self.set_up_test()
        yield

    def set_up_test(self) -> None:
        """
        Wait before each test to stay under the Google Sheets API quota.
        """
        _wait_for_quota()

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `to_gsheet._main()` with a mocked `sys.argv`.

        :param argv: command-line arguments, including the script name
        """
        parser = dshgotgs._parse()
        with mock.patch("sys.argv", argv):
            dshgotgs._main(parser)

    def _create_input_file(self) -> str:
        """
        Create a CSV file with a short and a long text in the scratch space.

        :return: path to the CSV file
        """
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "data.csv")
        long_text = "a long text that does not fit in a cell " * 8
        df = pd.DataFrame({"col1": [1, 2], "col2": ["short", long_text]})
        df.to_csv(input_file, index=False)
        return input_file

    def _get_tab_format(self, tab_name: str) -> Any:
        """
        Get the formatting of the first rows of a tab from the Sheets API.

        :param tab_name: name of the tab
        :return: the Sheets API response with the number of frozen rows, the
            height of the rows, and the format of the cells `A1` and `A2`
        """
        spreadsheet_id = hgodrapi._extract_file_id_from_url(self._url)
        sheets_service = hgodrapi.get_sheets_service(self._credentials)
        fields = (
            "sheets(properties(gridProperties(frozenRowCount)),"
            "data(rowMetadata(pixelSize),"
            "rowData(values(userEnteredFormat(textFormat(bold),wrapStrategy)))))"
        )
        response = (
            sheets_service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                ranges=[f"'{tab_name}'!A1:A2"],
                includeGridData=True,
                fields=fields,
            )
            .execute()
        )
        return response["sheets"][0]

    def helper(
        self, tab_name: str, extra_args: List[str], expected: str
    ) -> None:
        """
        Upload a CSV file to a new tab and check how the tab is formatted.

        :param tab_name: name of the new tab
        :param extra_args: command-line arguments with the formatting options
        :param expected: expected formatting of the tab
            ```
            frozen_rows=1, header_bold=True, data_bold=False, wrap_strategy=CLIP
            ```
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        argv = [
            "to_gsheet.py",
            "--input_file",
            input_file,
            "--url",
            self._url,
            "--tabname",
            tab_name,
        ]
        argv.extend(extra_args)
        expected = hprint.dedent(expected)
        # Run test.
        self._run_main(argv)
        # Check outputs.
        sheet = self._get_tab_format(tab_name)
        frozen_rows = sheet["properties"]["gridProperties"].get(
            "frozenRowCount", 0
        )
        rows = sheet["data"][0]["rowData"]
        header_format = rows[0]["values"][0].get("userEnteredFormat", {})
        data_format = rows[1]["values"][0].get("userEnteredFormat", {})
        header_bold = header_format.get("textFormat", {}).get("bold", False)
        data_bold = data_format.get("textFormat", {}).get("bold", False)
        wrap_strategy = data_format.get("wrapStrategy", "")
        actual = (
            f"frozen_rows={frozen_rows}, header_bold={header_bold}, "
            f"data_bold={data_bold}, wrap_strategy={wrap_strategy}"
        )
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test that the data written to the Google Sheet is the CSV data.
        """
        # Prepare inputs.
        tab_name = "tab_data"
        input_file = self._create_input_file()
        argv = [
            "to_gsheet.py",
            "--input_file",
            input_file,
            "--url",
            self._url,
            "--tabname",
            tab_name,
        ]
        # Prepare outputs.
        expected = pd.read_csv(input_file).to_csv(index=False)
        # Run test.
        self._run_main(argv)
        # Check outputs.
        df = hgodrapi.from_gsheet(
            self._url, tab_name=tab_name, credentials=self._credentials
        )
        actual = df.to_csv(index=False)
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that the header is frozen and bold and the cells are clipped by
        default.
        """
        # Prepare inputs.
        tab_name = "tab_default"
        extra_args: List[str] = []
        # Prepare outputs.
        expected = """
        frozen_rows=1, header_bold=True, data_bold=False, wrap_strategy=CLIP
        """
        # Run test.
        self.helper(tab_name, extra_args, expected)

    def test3(self) -> None:
        """
        Test that `--no_freeze_header` makes the header bold and not frozen.
        """
        # Prepare inputs.
        tab_name = "tab_no_freeze"
        extra_args = ["--no_freeze_header"]
        # Prepare outputs.
        expected = """
        frozen_rows=0, header_bold=True, data_bold=False, wrap_strategy=CLIP
        """
        # Run test.
        self.helper(tab_name, extra_args, expected)

    def test4(self) -> None:
        """
        Test that `--no_bold_header` freezes the header and does not make it
        bold.
        """
        # Prepare inputs.
        tab_name = "tab_no_bold"
        extra_args = ["--no_bold_header"]
        # Prepare outputs.
        expected = """
        frozen_rows=1, header_bold=False, data_bold=False, wrap_strategy=CLIP
        """
        # Run test.
        self.helper(tab_name, extra_args, expected)

    def test5(self) -> None:
        """
        Test `--cell_style overflow`.
        """
        # Prepare inputs.
        tab_name = "tab_overflow"
        extra_args = ["--cell_style", "overflow"]
        # Prepare outputs.
        expected = """
        frozen_rows=1, header_bold=True, data_bold=False, wrap_strategy=OVERFLOW_CELL
        """
        # Run test.
        self.helper(tab_name, extra_args, expected)

    def test6(self) -> None:
        """
        Test `--cell_style wrap`, including that the row height fits the text.
        """
        # Prepare inputs.
        tab_name = "tab_wrap"
        extra_args = ["--cell_style", "wrap"]
        # Prepare outputs.
        expected = """
        frozen_rows=1, header_bold=True, data_bold=False, wrap_strategy=WRAP
        """
        # Run test.
        self.helper(tab_name, extra_args, expected)
        # Check outputs: the row with the long text is taller than the fixed
        # 20 px height set when freezing the header.
        sheet = self._get_tab_format(tab_name)
        row_height = sheet["data"][0]["rowMetadata"][1]["pixelSize"]
        self.assertGreater(row_height, 20)

    def test7(self) -> None:
        """
        Test that writing to an existing tab without `--overwrite` fails.
        """
        # Prepare inputs.
        tab_name = "tab_existing"
        input_file = self._create_input_file()
        argv = [
            "to_gsheet.py",
            "--input_file",
            input_file,
            "--url",
            self._url,
            "--tabname",
            tab_name,
        ]
        # Run test: the first run creates the tab, the second one must fail.
        self._run_main(argv)
        with self.assertRaises(AssertionError) as cm:
            self._run_main(argv)
        # Check outputs.
        self.assertIn("Use --overwrite to replace it", str(cm.exception))


# #############################################################################
# Test_to_gsheet_py_all_tabs
# #############################################################################


@_SKIP_GSHEET_TESTS
class Test_to_gsheet_py_all_tabs(hunitest.TestCase):
    """
    Test the `to_gsheet.py` executable with `--tabname _ALL_`, including the
    roundtrip with `from_gsheet.py`.

    The class creates a source Google Sheet with the tabs:
    - `Sheet1`: no cells
    - `data`: header and 2 rows
    - `My Data`: header and 2 rows
    - `header_only`: only the header
    - `a/b`: header and 2 rows

    All the Google Sheets are in a temporary Google Drive folder that is deleted
    at the end. The tests turn off the header formatting to send fewer requests
    to the Google Sheets API.
    """

    _credentials: Any
    _folder_id: str
    _source_url: str

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create a temporary Google Sheet with 5 tabs, 2 of them with no rows.
        """
        pytest.importorskip("gspread")
        cls._credentials = hgodrapi.get_credentials()
        # Create the temporary folder and the source Google Sheet inside it.
        cls._folder_id = hgodrapi.create_tmp_gdrive_folder(
            "tmp_test_to_gsheet_all_tabs", credentials=cls._credentials
        )
        cls._source_url = hgodrapi.create_tmp_gsheet(
            folder_id=cls._folder_id, credentials=cls._credentials
        )
        # Fill the tabs. A new Google Sheet has the empty tab `Sheet1`.
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        for tab_name in ["data", "My Data"]:
            hgodrapi.to_gsheet(
                df,
                cls._source_url,
                tab_name=tab_name,
                credentials=cls._credentials,
            )
        df_header_only = pd.DataFrame(columns=pd.Index(["col1", "col2"]))
        hgodrapi.to_gsheet(
            df_header_only,
            cls._source_url,
            tab_name="header_only",
            credentials=cls._credentials,
        )
        hgodrapi.to_gsheet(
            df, cls._source_url, tab_name="a/b", credentials=cls._credentials
        )

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Delete the temporary folder with the Google Sheets, even when a test
        fails.
        """
        hgodrapi.delete_gdrive_file(cls._folder_id, credentials=cls._credentials)

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):  # type: ignore[no-untyped-def]
        """
        Setup and teardown for each test.
        """
        # Run before each test.
        self.set_up_test()
        yield

    def set_up_test(self) -> None:
        """
        Wait before each test to stay under the Google Sheets API quota.
        """
        _wait_for_quota()

    def _run_main(self, module: Any, argv: List[str]) -> None:
        """
        Run the `_main()` of an executable with a mocked `sys.argv`.

        :param module: module of the executable
        :param argv: command-line arguments, including the script name
        """
        parser = module._parse()
        with mock.patch("sys.argv", argv):
            module._main(parser)

    def _run_to_gsheet_without_url(self, argv: List[str]) -> str:
        """
        Run `to_gsheet._main()` that creates a new temporary Google Sheet.

        The temporary Google Sheet is created in the test folder, instead of the
        shared temporary folder, so that it is deleted at the end of the tests.

        :param argv: command-line arguments, including the script name
        :return: URL of the new temporary Google Sheet
        """
        urls: List[str] = []
        create_tmp_gsheet = hgodrapi.create_tmp_gsheet

        def create_tmp_gsheet_in_test_folder(**kwargs: Any) -> str:
            url = create_tmp_gsheet(folder_id=self._folder_id, **kwargs)
            urls.append(url)
            return url

        with mock.patch.object(
            hgodrapi,
            "create_tmp_gsheet",
            side_effect=create_tmp_gsheet_in_test_folder,
        ):
            self._run_main(dshgotgs, argv)
        self.assertEqual(len(urls), 1)
        return urls[0]

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
        Test the roundtrip: download all the tabs, upload them to a new
        temporary Google Sheet and download them again.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dir_a = os.path.join(scratch_dir, "a")
        dir_b = os.path.join(scratch_dir, "b")
        hio.create_dir(dir_a, incremental=True)
        hio.create_dir(dir_b, incremental=True)
        file_a = os.path.join(dir_a, "data.csv")
        file_b = os.path.join(dir_b, "data.csv")
        # Prepare outputs.
        expected_tabs = "['Sheet1', 'data', 'My Data', 'header_only', 'a/b']"
        expected_files = r"""
        data.0.Sheet1.csv: ''
        data.1.data.csv: 'col1,col2\n1,a\n2,b\n'
        data.2.My Data.csv: 'col1,col2\n1,a\n2,b\n'
        data.3.header_only.csv: 'col1,col2\n'
        data.4.a%2Fb.csv: 'col1,col2\n1,a\n2,b\n'
        """
        expected_files = hprint.dedent(expected_files)
        # Run test: download, upload to a new Google Sheet, download again.
        argv = [
            "from_gsheet.py",
            "--url",
            self._source_url,
            "--tabname",
            "_ALL_",
            "--output_file",
            file_a,
        ]
        self._run_main(dshgofrgs, argv)
        argv = [
            "to_gsheet.py",
            "--input_file",
            file_a,
            "--tabname",
            "_ALL_",
            "--no_freeze_header",
            "--no_bold_header",
        ]
        dest_url = self._run_to_gsheet_without_url(argv)
        argv = [
            "from_gsheet.py",
            "--url",
            dest_url,
            "--tabname",
            "_ALL_",
            "--output_file",
            file_b,
        ]
        self._run_main(dshgofrgs, argv)
        # Check outputs: same tabs and same files.
        actual_tabs = hgodrapi.get_tabs_from_gsheet(
            dest_url, credentials=self._credentials
        )
        self.assert_equal(str(actual_tabs), expected_tabs)
        actual_files_a = self._get_files_content(dir_a)
        self.assert_equal(actual_files_a, expected_files)
        actual_files_b = self._get_files_content(dir_b)
        self.assert_equal(actual_files_b, expected_files)

    def test2(self) -> None:
        """
        Test that a new temporary Google Sheet has only the tabs of the files,
        without the empty first tab.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        hio.to_file(os.path.join(scratch_dir, "data.1.data.csv"), "col1\n1\n")
        hio.to_file(os.path.join(scratch_dir, "data.2.My Data.csv"), "col1\n2\n")
        argv = [
            "to_gsheet.py",
            "--input_file",
            os.path.join(scratch_dir, "data.csv"),
            "--tabname",
            "_ALL_",
            "--no_freeze_header",
            "--no_bold_header",
        ]
        # Prepare outputs.
        expected = "['data', 'My Data']"
        # Run test.
        dest_url = self._run_to_gsheet_without_url(argv)
        # Check outputs.
        actual = hgodrapi.get_tabs_from_gsheet(
            dest_url, credentials=self._credentials
        )
        self.assert_equal(str(actual), expected)

    def test3(self) -> None:
        """
        Test that a tab that already exists stops the upload before writing any
        tab, if `--overwrite` is not specified.
        """
        # Prepare inputs.
        url = hgodrapi.create_tmp_gsheet(
            folder_id=self._folder_id, credentials=self._credentials
        )
        df = pd.DataFrame({"col1": [1]})
        hgodrapi.to_gsheet(
            df, url, tab_name="data", credentials=self._credentials
        )
        scratch_dir = self.get_scratch_space()
        hio.to_file(os.path.join(scratch_dir, "data.0.data.csv"), "col1\n5\n")
        hio.to_file(os.path.join(scratch_dir, "data.1.other.csv"), "col1\n6\n")
        argv = [
            "to_gsheet.py",
            "--input_file",
            os.path.join(scratch_dir, "data.csv"),
            "--url",
            url,
            "--tabname",
            "_ALL_",
            "--no_freeze_header",
            "--no_bold_header",
        ]
        # Prepare outputs.
        expected = "['Sheet1', 'data']"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            self._run_main(dshgotgs, argv)
        # Check outputs.
        self.assertIn("use --overwrite", str(cm.exception))
        actual = hgodrapi.get_tabs_from_gsheet(
            url, credentials=self._credentials
        )
        self.assert_equal(str(actual), expected)

    def test4(self) -> None:
        """
        Test that with `--overwrite` the existing tabs are replaced, the tabs
        that are not in the files do not change, and the new tabs are added at
        the end.
        """
        # Prepare inputs.
        url = hgodrapi.create_tmp_gsheet(
            folder_id=self._folder_id, credentials=self._credentials
        )
        df = pd.DataFrame({"col1": [1], "col2": ["old"]})
        hgodrapi.to_gsheet(
            df, url, tab_name="keep", credentials=self._credentials
        )
        scratch_dir = self.get_scratch_space()
        hio.to_file(
            os.path.join(scratch_dir, "data.0.keep.csv"), "col1,col2\n7,z\n"
        )
        hio.to_file(os.path.join(scratch_dir, "data.1.new.csv"), "col1\n8\n")
        argv = [
            "to_gsheet.py",
            "--input_file",
            os.path.join(scratch_dir, "data.csv"),
            "--url",
            url,
            "--tabname",
            "_ALL_",
            "--overwrite",
            "--no_freeze_header",
            "--no_bold_header",
        ]
        # Prepare outputs.
        expected_tabs = "['Sheet1', 'keep', 'new']"
        expected_keep = "col1,col2\n7,z\n"
        # Run test.
        self._run_main(dshgotgs, argv)
        # Check outputs.
        actual_tabs = hgodrapi.get_tabs_from_gsheet(
            url, credentials=self._credentials
        )
        self.assert_equal(str(actual_tabs), expected_tabs)
        df_keep = hgodrapi.from_gsheet(
            url, tab_name="keep", credentials=self._credentials
        )
        self.assert_equal(df_keep.to_csv(index=False), expected_keep)
