#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "google",
#   "googleapi",
#   "gspread",
#   "pandas",
#   "pyyaml",
#   "tqdm",
# ]
# ///

r"""
Load a CSV file to a Google Sheets document.

Tab Selection:
- By default, the gid in the URL is ignored. Use --tabname to specify which tab
  to write to (default: 'new_data').
- With --use_gid flag, the tab name is extracted from the gid in the URL and the
  --tabname argument is ignored. The URL must contain a gid for this to work.
- Use --tabname _ALL_ to upload many CSV files, one tab for each file (see
  All Tabs).

All Tabs:
- --input_file is the prefix of the files `<input_file without .csv>.<ID>.<tab_name>.csv`,
  e.g., the files saved by `from_gsheet.py --tabname _ALL_`, so that
  `from_gsheet.py` and `to_gsheet.py` do a roundtrip
  - E.g., `--input_file data.csv` finds `data.0.Sheet1.csv` and
    `data.1.My Data.csv` in the dir of `data.csv` and ignores the other files
  - The tab name is the `<tab_name>` of the file, where `%XX` is decoded to the
    character with the hex code `XX`
  - The files are written in the order of `<ID>`
- An empty file gives a tab with no cells. A file with only the header gives a tab
  with only the header
- With --url, the script fails before writing anything if a tab already exists and
  --overwrite is not specified. The tabs that are not in the files are not changed
  and the new tabs are added after them
- Without --url, the new temporary Google Sheet has the tabs of the files, in the
  order of `<ID>`. The script deletes its empty first tab if no file uses its name
- The CSV files store only the values, so formulas and formatting of the original
  Google Sheet are not restored
- --use_gid cannot be used

Temporary Sheet:
- If --url is not specified, a new Google Sheet named `tmp_file_<timestamp>` is
  created in the temporary Google Drive folder and the CSV is written to its
  first tab (unless --tabname is specified).

Formatting:
- By default the header row is frozen (--freeze_header) and bold (--bold_header).
  Use --no_freeze_header and --no_bold_header to skip them. Skipping a format
  leaves the tab as it is: it does not remove a freeze or a bold already there.
- --cell_style controls the style of the text in the cells:
  - `clip` (default): cut the text at the cell border
  - `wrap`: wrap the text in multiple lines and fit the row height to the text
  - `overflow`: let the text spill over the empty neighbor cells

# Usage Example

- Load CSV to a new temporary Google Sheet and open it in the browser:
> to_gsheet.py --input_file data.csv --open

- Load CSV to a new tab (default tab name: 'new_data'):
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit"

- Load CSV to a specific tab:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data"

- Overwrite an existing tab:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --overwrite

- Extract tab name from gid in URL (ignores --tabname):
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --use_gid

- Open the tab in the browser after the upload:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --open

- Wrap the long text in the cells, instead of clipping it:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --cell_style wrap

- Do not freeze nor bold the header row:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --no_freeze_header \
    --no_bold_header

- Roundtrip of all the tabs: download them to `data.<ID>.<tab_name>.csv` and upload
  them to a new temporary Google Sheet:
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname _ALL_ \
    --output_file data.csv
> to_gsheet.py \
    --input_file data.csv \
    --tabname _ALL_ \
    --open

Import as:

import dev_scripts_helpers.google.to_gsheet as dshgotgs
"""

import argparse
import logging
import os
import webbrowser
from typing import Any, Dict, List

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)

# Value of `--tabname` to upload all the tabs.
_ALL_TABS = "_ALL_"

# #############################################################################


def _read_csv(file_name: str) -> pd.DataFrame:
    """
    Read a CSV file.

    :param file_name: path to the CSV file
    :return: DataFrame with the content of the file
        - An empty file (i.e., a tab with no cells) gives a DataFrame with no
          columns, instead of the error raised by `pd.read_csv()`
    """
    _LOG.debug(hprint.to_str("file_name"))
    if os.path.getsize(file_name) == 0:
        df = pd.DataFrame()
    else:
        df = pd.read_csv(file_name)
    return df


def _read_all_tab_files(input_file: str) -> Dict[str, pd.DataFrame]:
    """
    Read the CSV files that store the tabs of a Google Sheet.

    :param input_file: prefix of the CSV files, as in
        `hgodrapi.get_tab_csv_files()`
    :return: map from the tab name to its DataFrame, in the order of the tab IDs
    """
    _LOG.debug(hprint.to_str("input_file"))
    tab_name_to_df = {}
    for tab_id, tab_name, tab_file in hgodrapi.get_tab_csv_files(input_file):
        _LOG.info(
            "Reading tab '%s' with ID '%d' from CSV file '%s'",
            tab_name,
            tab_id,
            tab_file,
        )
        tab_name_to_df[tab_name] = _read_csv(tab_file)
    return tab_name_to_df


def _write_tab(
    df: pd.DataFrame,
    url: str,
    tab_name: str,
    *,
    freeze_header: bool,
    bold_header: bool,
    cell_style: str,
    credentials: Any,
) -> None:
    """
    Write a DataFrame to a tab of a Google Sheet.

    :param df: data to write
    :param url: URL of the Google Sheets document
    :param tab_name: name of the tab to write to
    :param freeze_header: whether to freeze the header row
    :param bold_header: whether to make the header row bold
    :param cell_style: style of the cells, as in `hgodrapi.to_gsheet()`
    :param credentials: Google credentials object
    """
    _LOG.debug(
        hprint.to_str("url tab_name freeze_header bold_header cell_style")
    )
    _LOG.info(
        "Writing %d rows and %d columns to tab '%s' in Google Sheet",
        len(df),
        len(df.columns),
        tab_name,
    )
    with htimer.TimedScope(logging.INFO, f"Writing tab '{tab_name}'"):
        hgodrapi.to_gsheet(
            df,
            url,
            tab_name=tab_name,
            freeze_rows=freeze_header,
            bold_header=bold_header,
            cell_style=cell_style,
            credentials=credentials,
        )


def _write_all_tabs(
    tab_name_to_df: Dict[str, pd.DataFrame],
    url: str,
    existing_tabs: List[str],
    *,
    is_tmp_gsheet: bool,
    overwrite: bool,
    freeze_header: bool,
    bold_header: bool,
    cell_style: str,
    credentials: Any,
) -> None:
    """
    Write each DataFrame to the tab with the same name in a Google Sheet.

    :param tab_name_to_df: map from the tab name to its DataFrame, in the order
        of the tabs
    :param url: URL of the Google Sheets document
    :param existing_tabs: names of the tabs that are in the Google Sheet
    :param is_tmp_gsheet: whether the Google Sheet is a new temporary one
        - Its tabs become exactly the passed tabs, in order: the script deletes
          the empty first tab, if no tab uses its name, and orders the tabs
    :param overwrite: whether to overwrite the tabs that already exist
    :param freeze_header: whether to freeze the header row of each tab
    :param bold_header: whether to make the header row bold in each tab
    :param cell_style: style of the cells, as in `hgodrapi.to_gsheet()`
    :param credentials: Google credentials object
    """
    _LOG.debug(hprint.to_str("url existing_tabs is_tmp_gsheet overwrite"))
    tab_names = list(tab_name_to_df.keys())
    # Fail early, before writing any tab. A new temporary Google Sheet has
    # nothing to lose, so its first tab can always be written.
    if not (overwrite or is_tmp_gsheet):
        existing_tabs_to_write = [
            tab_name for tab_name in tab_names if tab_name in existing_tabs
        ]
        hdbg.dassert_eq(
            existing_tabs_to_write,
            [],
            "Tabs already exist in the Google Sheet: use --overwrite to replace "
            "them",
        )
    for tab_name, df in tab_name_to_df.items():
        _LOG.info(
            "Writing %d rows and %d columns to tab '%s' in Google Sheet",
            len(df),
            len(df.columns),
            tab_name,
        )
    # Write the tabs in order. The tabs that do not exist are added at the end.
    # The Google Sheet is opened only once for all the tabs.
    hgodrapi.to_gsheet_tabs(
        tab_name_to_df,
        url,
        freeze_rows=freeze_header,
        bold_header=bold_header,
        cell_style=cell_style,
        credentials=credentials,
    )
    # Make the tabs of the new Google Sheet match the passed tabs.
    if is_tmp_gsheet:
        with htimer.TimedScope(logging.INFO, "Cleaning up the tabs"):
            default_tab = existing_tabs[0]
            if default_tab not in tab_names:
                hgodrapi.delete_tab_from_gsheet(
                    url, default_tab, credentials=credentials
                )
            hgodrapi.reorder_tabs_in_gsheet(
                url, tab_names, credentials=credentials
            )


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--input_file",
        action="store",
        required=True,
        help="Path to input CSV file (with `--tabname %s`, the prefix of the "
        "input CSV files)" % _ALL_TABS,
    )
    parser.add_argument(
        "--url",
        action="store",
        default="",
        help="URL of the Google Sheets document (default: create a new "
        "temporary Google Sheet)",
    )
    parser.add_argument(
        "--tabname",
        action="store",
        default="",
        help="Name of the tab to write to, or `%s` to write all the CSV files, "
        "one tab for each (default: 'new_data' for an existing Google Sheet, "
        "the first tab for a new temporary Google Sheet)" % _ALL_TABS,
    )
    parser.add_argument(
        "--use_gid",
        action="store_true",
        default=False,
        help="Extract tab name from gid in the URL instead of using --tabname",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the tab(s) if they already exist",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the tab in the browser after writing the data",
    )
    hparser.add_bool_arg(
        parser,
        "freeze_header",
        default_value=True,
        help_="Freeze the header row (the option does not unfreeze a tab that "
        "is already frozen)",
    )
    hparser.add_bool_arg(
        parser,
        "bold_header",
        default_value=True,
        help_="Make the header row bold (the option does not remove the bold "
        "from a header that is already bold)",
    )
    parser.add_argument(
        "--cell_style",
        action="store",
        choices=list(hgodrapi.CELL_STYLE_TO_WRAP_STRATEGY),
        default="clip",
        help="Style of the text in the cells: cut at the cell border (clip), "
        "wrapped in multiple lines (wrap), or spilled over the empty neighbor "
        "cells (overflow)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Measure the total time, to see which phase is slow.
    total_timer = htimer.Timer()
    write_all_tabs = args.tabname == _ALL_TABS
    hdbg.dassert_imply(
        write_all_tabs,
        not args.use_gid,
        "Cannot use --use_gid flag with --tabname %s",
        _ALL_TABS,
    )
    # Read the CSV files, before using the Google Sheet, so that a wrong file
    # does not leave a new temporary Google Sheet behind.
    tab_name_to_df: Dict[str, pd.DataFrame] = {}
    df = pd.DataFrame()
    if write_all_tabs:
        with htimer.TimedScope(logging.INFO, "Reading the CSV files"):
            tab_name_to_df = _read_all_tab_files(args.input_file)
    else:
        # Validate input file exists.
        hdbg.dassert_path_exists(args.input_file)
        _LOG.info("Reading CSV file: '%s'", args.input_file)
        # Read CSV file.
        df = _read_csv(args.input_file)
        _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    # Get credentials.
    with htimer.TimedScope(logging.INFO, "Loading Google API credentials"):
        credentials = hgodrapi.get_credentials()
    # Without a URL, create a new temporary Google Sheet.
    url = args.url
    is_tmp_gsheet = url == ""
    hdbg.dassert_imply(
        args.use_gid,
        not is_tmp_gsheet,
        "Cannot use --use_gid flag without --url",
    )
    if is_tmp_gsheet:
        with htimer.TimedScope(logging.INFO, "Creating temporary Google Sheet"):
            url = hgodrapi.create_tmp_gsheet(credentials=credentials)
        _LOG.info("Created temporary Google Sheet: '%s'", url)
    # Print information about the Google Sheet.
    with htimer.TimedScope(logging.INFO, "Getting Google Sheet information"):
        hgodrapi.print_info_about_google_url(url, credentials=credentials)
        existing_tabs = hgodrapi.get_tabs_from_gsheet(
            url, credentials=credentials
        )
    if write_all_tabs:
        # Write one tab for each file.
        with htimer.TimedScope(logging.INFO, "Writing all the tabs"):
            _write_all_tabs(
                tab_name_to_df,
                url,
                existing_tabs,
                is_tmp_gsheet=is_tmp_gsheet,
                overwrite=args.overwrite,
                freeze_header=args.freeze_header,
                bold_header=args.bold_header,
                cell_style=args.cell_style,
                credentials=credentials,
            )
        # Open the first tab, if requested.
        tab_name = next(iter(tab_name_to_df))
    else:
        # Determine tab name: if --use_gid is provided, extract from URL.
        tab_name = args.tabname
        if args.use_gid:
            gid = hgodrapi._extract_gid_from_url(url)
            hdbg.dassert_is_not(
                gid,
                None,
                "No gid found in URL. Cannot use --use_gid flag without gid in URL: %s",
                url,
            )
            spreadsheet_id = hgodrapi._extract_file_id_from_url(url)
            tab_name = hgodrapi.get_tab_name_from_gid(
                spreadsheet_id, gid, credentials=credentials
            )
            _LOG.info(
                "Using --use_gid flag, extracted tab name '%s' from gid '%s'",
                tab_name,
                gid,
            )
        elif tab_name == "":
            if is_tmp_gsheet:
                # Use the empty first tab of the new Google Sheet.
                tab_name = existing_tabs[0]
            else:
                tab_name = "new_data"
        # Check if the tab already exists. A new temporary Google Sheet has
        # nothing to lose, so its first tab can always be written.
        overwrite = args.overwrite or is_tmp_gsheet
        tab_exists = tab_name in existing_tabs
        hdbg.dassert_imply(
            tab_exists,
            overwrite,
            f"Tab '{tab_name}' already exists in the Google Sheet. Use --overwrite to replace it.",
        )
        # Write data to Google Sheet.
        _write_tab(
            df,
            url,
            tab_name,
            freeze_header=args.freeze_header,
            bold_header=args.bold_header,
            cell_style=args.cell_style,
            credentials=credentials,
        )
    _LOG.info("Successfully wrote data to Google Sheet")
    _LOG.info("Total time: %s", htimer.stop_timer(total_timer))
    if args.open:
        tab_url = hgodrapi.get_gsheet_tab_url(
            url, tab_name, credentials=credentials
        )
        _LOG.info("Opening '%s' in the browser", tab_url)
        webbrowser.open(tab_url)


if __name__ == "__main__":
    _main(_parse())
