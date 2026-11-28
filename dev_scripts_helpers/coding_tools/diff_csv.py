#!/usr/bin/env python

"""
Diff two CSV files with vimdiff, after making the files comparable.

The script:
- Reads the two CSV files
- Renders every cell in the same way, so that only real differences show up,
  e.g.,
  - `1`, `1.0`, and `1.000000` become `1`
  - `nan` and an empty cell become an empty cell
  - leading and trailing spaces are removed
- Aligns the two files on the union of their rows and columns
  - Rows are matched by position, or by `--key_columns`
- Optionally removes the columns and the rows that are the same in both files
- Writes the two resulting CSV files (`tmp.diff_csv.1.*` and `tmp.diff_csv.2.*`)
  in `--dst_dir`
- Diffs them with vimdiff

# Usage Example

- Diff two CSV files after rendering the cells in the same way:
> diff_csv.py --file1 a.csv --file2 b.csv

- Match the rows by key and keep only the rows and columns that differ:
> diff_csv.py --file1 a.csv --file2 b.csv --key_columns id,date \
    --remove_same_rows --remove_same_columns

- Compare floats up to 3 decimal digits:
> diff_csv.py --file1 a.csv --file2 b.csv --precision 3

- Write the files to diff without running vimdiff:
> diff_csv.py --file1 a.csv --file2 b.csv --no_run_vimdiff

Import as:

import dev_scripts_helpers.coding_tools.diff_csv as dscdicsv
"""

import argparse
import logging
import os
import re
from typing import List, Tuple

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hpandas_compare as hpancomp
import helpers.hpandas_io as hpanio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


# Regex matching an integer, e.g., `-12`.
_INT_REGEX = re.compile(r"^[+-]?\d+$")

# Regex matching a decimal number, e.g., `1.5`, `.5`, `-1e-3`.
_FLOAT_REGEX = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


# #############################################################################
# Rendering and alignment
# #############################################################################


def _render_cell(val: str, *, precision: int) -> str:
    """
    Render a cell in a canonical way.

    E.g., with `precision=3`:
    - `" 1.0 "` -> `"1"`
    - `"2.50000"` -> `"2.5"`
    - `"0.00001"` -> `"0"`
    - `"NaN"` -> `""`
    - `"abc"` -> `"abc"`

    :param val: content of the cell as read from the CSV file
    :param precision: max number of decimal digits kept for floats
    :return: rendered cell
    """
    val = val.strip()
    if val.lower() == "nan":
        out = ""
    elif _INT_REGEX.match(val):
        out = str(int(val))
    elif _FLOAT_REGEX.match(val):
        out = f"{float(val):.{precision}f}"
        # Remove the trailing zeros, e.g., `2.500` -> `2.5`.
        if "." in out:
            out = out.rstrip("0").rstrip(".")
        # Avoid a negative zero after rounding, e.g., `-0.0001` -> `-0`.
        if out == "-0":
            out = "0"
    else:
        out = val
    return out


def _read_csv(file_name: str, *, precision: int) -> pd.DataFrame:
    """
    Read a CSV file and render all its cells in a canonical way.

    :param file_name: path of the CSV file
    :param precision: max number of decimal digits kept for floats
    :return: dataframe of strings
    """
    hdbg.dassert_file_exists(file_name)
    # Read all the cells as strings to avoid type inference (e.g., `1` vs `1.0`).
    df = hpanio.read_csv_to_df(file_name, dtype=str, keep_default_na=False)
    # Rows shorter than the header are read as NaN.
    df = df.fillna("")
    for col in df.columns:
        df[col] = df[col].map(lambda x: _render_cell(x, precision=precision))
    return df


def _align_dfs(
    df1: pd.DataFrame, df2: pd.DataFrame, *, key_columns: List[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align two dataframes on the union of their rows and columns.

    - Rows or columns missing in one dataframe are filled with empty cells
    - Order is: rows / columns of `df1` first, then those only in `df2`
    - Rows are matched by position if `key_columns` is empty

    :param df1: first dataframe
    :param df2: second dataframe
    :param key_columns: columns identifying a row
    :return: the two dataframes with the same index and columns, and a default
        integer index (the key columns are regular columns, placed first)
    """
    if key_columns:
        for df in (df1, df2):
            hdbg.dassert_is_subset(key_columns, df.columns)
        df1 = df1.set_index(key_columns)
        df2 = df2.set_index(key_columns)
        for df in (df1, df2):
            hdbg.dassert(
                df.index.is_unique,
                "Duplicated keys: %s",
                df.index[df.index.duplicated()].tolist()[:5],
            )
        index = df1.index.append(df2.index.difference(df1.index, sort=False))
    else:
        index = pd.RangeIndex(max(len(df1), len(df2)))
    columns = df1.columns.append(df2.columns.difference(df1.columns, sort=False))
    df1 = df1.reindex(index=index, columns=columns, fill_value="")
    df2 = df2.reindex(index=index, columns=columns, fill_value="")
    if key_columns:
        df1 = df1.reset_index()
        df2 = df2.reset_index()
    return df1, df2


# #############################################################################
# Removing what is the same
# #############################################################################


def _get_diff(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> Tuple[pd.Index, List[str]]:
    """
    Find the rows and columns where two aligned dataframes differ.

    :param df1: first dataframe
    :param df2: second dataframe, with the same index and columns as `df1`
    :return: positions of the rows with at least one different cell and names of
        the columns with at least one different cell
    """
    # Use positional names for the columns, since `compare_dataframe_rows()`
    # adds a column named `index`, which can clash with the CSV columns.
    col_names = list(df1.columns)
    tmp_names = [f"c{i}" for i in range(len(col_names))]
    diff = hpancomp.compare_dataframe_rows(
        df1.set_axis(tmp_names, axis=1), df2.set_axis(tmp_names, axis=1)
    )
    # The columns of the diff are (column, "self" | "other").
    diff_tmp_names = set(diff.columns.get_level_values(0))
    diff_cols = [
        col for col, tmp in zip(col_names, tmp_names) if tmp in diff_tmp_names
    ]
    return diff.index, diff_cols


def _remove_same(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    diff_rows: pd.Index,
    diff_cols: List[str],
    *,
    key_columns: List[str],
    remove_same_columns: bool,
    remove_same_rows: bool,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove the rows and the columns that are the same in the two dataframes.

    The key columns are always kept, since they identify the rows.

    :param df1: first dataframe
    :param df2: second dataframe, with the same index and columns as `df1`
    :param diff_rows: positions of the rows that differ, see `_get_diff()`
    :param diff_cols: names of the columns that differ, see `_get_diff()`
    :param key_columns: columns identifying a row
    :param remove_same_columns: remove the columns that are the same
    :param remove_same_rows: remove the rows that are the same
    :return: the two reduced dataframes
    """
    if remove_same_rows:
        df1 = df1.loc[diff_rows]
        df2 = df2.loc[diff_rows]
    if remove_same_columns:
        cols_to_keep = [
            col for col in df1.columns if col in key_columns or col in diff_cols
        ]
        df1 = df1.filter(items=cols_to_keep)
        df2 = df2.filter(items=cols_to_keep)
    return df1, df2


# #############################################################################
# Diffing
# #############################################################################


def _diff_dfs(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    file1: str,
    file2: str,
    *,
    dst_dir: str,
    run_vimdiff: bool,
    dry_run: bool,
) -> None:
    """
    Write the dataframes to CSV files and diff them with vimdiff.

    :param df1: first dataframe
    :param df2: second dataframe
    :param file1: path of the original first CSV file, used to name the output
    :param file2: path of the original second CSV file, used to name the output
    :param dst_dir: directory where to write the CSV files to diff
    :param run_vimdiff: run vimdiff or only write the files
    :param dry_run: do not write the files nor run vimdiff
    """
    out_file1 = os.path.join(
        dst_dir, f"tmp.diff_csv.1.{os.path.basename(file1)}"
    )
    out_file2 = os.path.join(
        dst_dir, f"tmp.diff_csv.2.{os.path.basename(file2)}"
    )
    cmd = []
    cmd.append("vimdiff")
    cmd.append(f"'{out_file1}'")
    cmd.append(f"'{out_file2}'")
    cmd = " ".join(cmd)
    if dry_run:
        _LOG.warning("[DRY_RUN] Would write '%s' and '%s'", out_file1, out_file2)
        if run_vimdiff:
            _LOG.warning("[DRY_RUN] Would run: %s", cmd)
    else:
        hio.create_dir(dst_dir, incremental=True)
        # Do not infer the compression from the extension of the original file.
        df1.to_csv(out_file1, index=False, compression=None)
        df2.to_csv(out_file2, index=False, compression=None)
        _LOG.info("Diff the files with:\n> %s", cmd)
        if run_vimdiff:
            # `hsystem.system()` captures the output, but vimdiff needs a
            # terminal.
            os.system(cmd)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--file1", action="store", required=True, help="First CSV file"
    )
    parser.add_argument(
        "--file2", action="store", required=True, help="Second CSV file"
    )
    parser.add_argument(
        "--key_columns",
        action="store",
        type=str,
        default="",
        help="Comma-separated columns to match the rows, instead of the position",
    )
    hparser.add_bool_arg(
        parser,
        "remove_same_columns",
        default_value=False,
        help_="Remove the columns that are the same in the two files",
    )
    hparser.add_bool_arg(
        parser,
        "remove_same_rows",
        default_value=False,
        help_="Remove the rows that are the same in the two files",
    )
    parser.add_argument(
        "--dst_dir",
        action="store",
        type=str,
        default=".",
        help="Directory storing the CSV files to diff",
    )
    parser.add_argument(
        "--precision",
        action="store",
        type=int,
        default=6,
        help="Max number of decimal digits kept when rendering floats",
    )
    hparser.add_bool_arg(
        parser,
        "run_vimdiff",
        default_value=True,
        help_="Run vimdiff on the resulting files",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    key_columns = [col.strip() for col in args.key_columns.split(",") if col]
    # Read the files rendering the cells in the same way, and align them.
    df1 = _read_csv(args.file1, precision=args.precision)
    df2 = _read_csv(args.file2, precision=args.precision)
    df1, df2 = _align_dfs(df1, df2, key_columns=key_columns)
    # Find what is different.
    diff_rows, diff_cols = _get_diff(df1, df2)
    _LOG.info(
        "rows=%d (different=%d), columns=%d (different=%d)",
        df1.shape[0],
        len(diff_rows),
        df1.shape[1],
        len(diff_cols),
    )
    if len(diff_rows) == 0:
        _LOG.warning(
            "The files '%s' and '%s' are the same after rendering the cells",
            args.file1,
            args.file2,
        )
    else:
        df1, df2 = _remove_same(
            df1,
            df2,
            diff_rows,
            diff_cols,
            key_columns=key_columns,
            remove_same_columns=args.remove_same_columns,
            remove_same_rows=args.remove_same_rows,
        )
        _diff_dfs(
            df1,
            df2,
            args.file1,
            args.file2,
            dst_dir=args.dst_dir,
            run_vimdiff=args.run_vimdiff,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    _main(_parse())
