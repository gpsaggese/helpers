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
Download data from a Google Sheets document and save it as a CSV file.

Tab Selection:
- If the URL contains a gid (e.g., ?gid=123#gid=123), the script automatically
  downloads that specific tab, even if --tabname is not specified.
- Use --tabname to override the gid and download a different tab.
- Use --tabname _ALL_ to download all the tabs, one CSV file per tab. This also
  overrides the gid.
- If no gid is in the URL and no --tabname is provided, downloads the first tab.

All Tabs:
- Each tab is saved in a file named `<output_file without .csv>.<ID>.<tab_name>.csv`
  - `<ID>` is the position of the tab in the Google Sheet, starting from 0
  - `<tab_name>` is the tab name. Only the characters that are not safe in a file
    name (`/ \ : * ? " < > | %` and the control characters) are replaced with
    `%XX`, where `XX` is the hex code. So the tab name can be restored exactly
  - E.g., `--output_file data.csv` with the tabs `Sheet1` and `My Data` creates
    `data.0.Sheet1.csv` and `data.1.My Data.csv`
- There is one file for each tab, so there are files also for the empty tabs
  - A tab with only the header gives a CSV file with only the header
  - A tab with no cells gives an empty file
- The script fails before downloading anything if a file already exists and
  --overwrite is not specified
- `to_gsheet.py --tabname _ALL_` uploads these files back, to do a roundtrip

# Usage Example

- Download first tab to CSV:
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --output_file data.csv

- Download specific tab by name:
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --output_file data.csv

- Automatically download tab from gid in URL (no --tabname needed):
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --output_file data.csv

- Override gid with explicit tab name:
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --tabname "different_tab" \
    --output_file data.csv

- Download all the tabs, one CSV file per tab (e.g., `data.0.Sheet1.csv`):
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname _ALL_ \
    --output_file data.csv

Import as:

import dev_scripts_helpers.google.from_gsheet as dshgofrgs
"""

import argparse
import logging
import os
from typing import Any

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Value of `--tabname` to download all the tabs.
_ALL_TABS = "_ALL_"

# #############################################################################


def _save_one_tab(
    url: str,
    tab_name: str,
    output_file: str,
    *,
    credentials: Any,
) -> None:
    """
    Download one tab of a Google Sheet and save it as a CSV file.

    :param url: URL of the Google Sheets document
    :param tab_name: name of the tab to read
        - Empty string: use the tab with the `gid` in the URL, or the first
          tab if the URL has no `gid`
    :param output_file: path to the output CSV file
    :param credentials: Google credentials object
    """
    _LOG.debug(hprint.to_str("url tab_name output_file"))
    if not tab_name:
        # If not provided, check if URL has a gid.
        gid = hgodrapi._extract_gid_from_url(url)
        if gid:
            spreadsheet_id = hgodrapi._extract_file_id_from_url(url)
            tab_name = hgodrapi.get_tab_name_from_gid(
                spreadsheet_id, gid, credentials=credentials
            )
            _LOG.info(
                "Found gid '%s' in URL, using tab name '%s'", gid, tab_name
            )
    # Read data from Google Sheet.
    if tab_name:
        _LOG.info("Reading data from tab '%s'", tab_name)
    else:
        _LOG.warning("Reading data from first tab")
    df = hgodrapi.from_gsheet(
        url,
        tab_name=tab_name or None,
        credentials=credentials,
    )
    _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    # Save to CSV.
    _LOG.info("Writing data to CSV file: '%s'", output_file)
    df.to_csv(output_file, index=False)
    _LOG.info("Successfully saved data to CSV file")


def _save_all_tabs(
    url: str,
    output_file: str,
    *,
    overwrite: bool,
    credentials: Any,
) -> None:
    """
    Download all the tabs of a Google Sheet and save each one in a CSV file.

    There is one file for each tab, also for the empty tabs. See the module
    docstring for the file names.

    :param url: URL of the Google Sheets document
    :param output_file: prefix of the output CSV files
    :param overwrite: whether to overwrite the CSV files that already exist
    :param credentials: Google credentials object
    """
    _LOG.debug(hprint.to_str("url output_file overwrite"))
    gid = hgodrapi._extract_gid_from_url(url)
    if gid:
        _LOG.warning(
            "Ignoring gid '%s' in URL since all the tabs are downloaded", gid
        )
    # Compute the name of all the files before downloading any data.
    tab_names = hgodrapi.get_tabs_from_gsheet(url, credentials=credentials)
    tab_files = [
        hgodrapi.get_tab_csv_file_name(output_file, tab_id, tab_name)
        for tab_id, tab_name in enumerate(tab_names)
    ]
    # Fail early, instead of after downloading the data.
    if not overwrite:
        existing_files = [
            tab_file for tab_file in tab_files if os.path.exists(tab_file)
        ]
        hdbg.dassert_eq(
            existing_files,
            [],
            "Output files already exist: use --overwrite to replace them",
        )
    # Read all the tabs, including the empty ones.
    tab_name_to_df = hgodrapi.from_gsheet_all_tabs(url, credentials=credentials)
    hdbg.dassert_eq(
        list(tab_name_to_df.keys()),
        tab_names,
        "The tabs of the Google Sheet changed while downloading it",
    )
    # Write one file for each tab.
    for tab_name, tab_file in zip(tab_names, tab_files):
        df = tab_name_to_df[tab_name]
        if len(df.columns) == 0:
            # `df.to_csv()` writes a newline for a DataFrame with no columns,
            # while an empty tab must give an empty file.
            _LOG.warning("Tab '%s' is empty: writing an empty file", tab_name)
            hio.to_file(tab_file, "")
        else:
            if len(df) == 0:
                _LOG.warning("Tab '%s' has only the header", tab_name)
            df.to_csv(tab_file, index=False)
        _LOG.info(
            "Wrote %d rows and %d columns of tab '%s' to '%s'",
            len(df),
            len(df.columns),
            tab_name,
            tab_file,
        )
    _LOG.info("Successfully saved %d tabs to CSV files", len(tab_names))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        required=True,
        help="URL of the Google Sheets document",
    )
    parser.add_argument(
        "--tabname",
        action="store",
        default=None,
        help="Name of the tab to read from, or `%s` to read all the tabs, one "
        "CSV file per tab (default: first tab)" % _ALL_TABS,
    )
    parser.add_argument(
        "--output_file",
        action="store",
        required=True,
        help="Path to output CSV file (with `--tabname %s`, the prefix of the "
        "output CSV files)" % _ALL_TABS,
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the output file if it already exists",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    save_all_tabs = args.tabname == _ALL_TABS
    # Check if output file already exists. With all the tabs, the files to
    # check are computed from the tab names.
    if (
        not save_all_tabs
        and os.path.exists(args.output_file)
        and not args.overwrite
    ):
        hdbg.dfatal(
            f"Output file '{args.output_file}' already exists. Use --overwrite to replace it."
        )
    # Get credentials.
    _LOG.info("Loading Google API credentials")
    credentials = hgodrapi.get_credentials()
    # Print information about the Google Sheet.
    _LOG.info("Google Sheet information:")
    hgodrapi.print_info_about_google_url(args.url, credentials=credentials)
    # Save the tabs to CSV files.
    if save_all_tabs:
        _save_all_tabs(
            args.url,
            args.output_file,
            overwrite=args.overwrite,
            credentials=credentials,
        )
    else:
        _save_one_tab(
            args.url,
            args.tabname or "",
            args.output_file,
            credentials=credentials,
        )


if __name__ == "__main__":
    _main(_parse())
