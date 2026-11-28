import os
from typing import List
from unittest import mock

import pandas as pd

import helpers.hio as hio
import helpers.hpandas_utils as hpanutil
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import dev_scripts_helpers.coding_tools.diff_csv as dscdicsv

# #############################################################################
# Test__render_cell
# #############################################################################


class Test__render_cell(hunitest.TestCase):
    def helper(self, val: str, expected: str, *, precision: int = 3) -> None:
        """
        Test rendering a cell.

        :param val: content of the cell
        :param expected: expected rendered cell
        :param precision: max number of decimal digits kept for floats
        """
        # Run test.
        actual = dscdicsv._render_cell(val, precision=precision)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test that integers and floats with the same value render the same.
        """
        for val in ["1", "1.0", "1.000", " 1 ", "+1", "01", "1e0"]:
            self.helper(val, "1")

    def test2(self) -> None:
        """
        Test that the trailing zeros are removed and the float is rounded.
        """
        self.helper("2.50000", "2.5")
        self.helper("0.123456", "0.123")

    def test3(self) -> None:
        """
        Test that a number rounded to zero does not keep the sign.
        """
        self.helper("-0.00001", "0")
        self.helper("0.00001", "0")

    def test4(self) -> None:
        """
        Test that `nan` and empty cells render as empty cells.
        """
        self.helper("NaN", "")
        self.helper("nan", "")
        self.helper("  ", "")

    def test5(self) -> None:
        """
        Test that text is only stripped.
        """
        self.helper("  foo bar ", "foo bar")
        self.helper("1_000", "1_000")
        self.helper("2024-01-01", "2024-01-01")

    def test6(self) -> None:
        """
        Test that big integers do not lose precision.
        """
        self.helper("12345678901234567890", "12345678901234567890")


# #############################################################################
# Test__align_dfs
# #############################################################################


class Test__align_dfs(hunitest.TestCase):
    def helper(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        key_columns: List[str],
        expected1: str,
        expected2: str,
    ) -> None:
        """
        Test aligning two dataframes.

        :param df1: first dataframe
        :param df2: second dataframe
        :param key_columns: columns identifying a row
        :param expected1: expected first dataframe, as string
        :param expected2: expected second dataframe, as string
        """
        # Run test.
        actual1, actual2 = dscdicsv._align_dfs(df1, df2, key_columns=key_columns)
        # Check outputs.
        for actual, expected in [(actual1, expected1), (actual2, expected2)]:
            actual = hpanutil.df_to_str(actual, num_rows=None)
            self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test aligning by position.
        """
        # Prepare inputs.
        df1 = pd.DataFrame({"a": ["1", "2", "3"], "b": ["x", "y", "z"]})
        df2 = pd.DataFrame({"b": ["x", "w"], "c": ["7", "8"]})
        # Prepare outputs.
        expected1 = """
           a  b  c
        0  1  x
        1  2  y
        2  3  z
        """
        expected2 = """
           a  b  c
        0     x  7
        1     w  8
        2
        """
        # Run test.
        self.helper(df1, df2, [], expected1, expected2)

    def test2(self) -> None:
        """
        Test aligning by key, with rows and columns only in one dataframe.
        """
        # Prepare inputs.
        df1 = pd.DataFrame({"k": ["a", "b"], "v": ["1", "2"]})
        df2 = pd.DataFrame({"k": ["c", "a"], "w": ["3", "4"]})
        # Prepare outputs.
        expected1 = """
           k  v  w
        0  a  1
        1  b  2
        2  c
        """
        expected2 = """
           k  v  w
        0  a     4
        1  b
        2  c     3
        """
        # Run test.
        self.helper(df1, df2, ["k"], expected1, expected2)

    def test3(self) -> None:
        """
        Test aligning by two key columns.
        """
        # Prepare inputs.
        df1 = pd.DataFrame({"k1": ["a", "a"], "k2": ["1", "2"], "v": ["x", "y"]})
        df2 = pd.DataFrame({"k1": ["a", "a"], "k2": ["2", "3"], "v": ["y", "z"]})
        # Prepare outputs.
        expected1 = """
          k1 k2  v
        0  a  1  x
        1  a  2  y
        2  a  3
        """
        expected2 = """
          k1 k2  v
        0  a  1
        1  a  2  y
        2  a  3  z
        """
        # Run test.
        self.helper(df1, df2, ["k1", "k2"], expected1, expected2)


# #############################################################################
# Test__remove_same
# #############################################################################


class Test__remove_same(hunitest.TestCase):
    def helper(
        self,
        key_columns: List[str],
        remove_same_columns: bool,
        remove_same_rows: bool,
        expected1: str,
        expected2: str,
    ) -> None:
        """
        Test finding and removing what is the same in two dataframes.

        The dataframes have a column named `index`, which must not clash with
        the columns added by `compare_dataframe_rows()`.

        :param key_columns: columns identifying a row
        :param remove_same_columns: remove the columns that are the same
        :param remove_same_rows: remove the rows that are the same
        :param expected1: expected first dataframe, as string
        :param expected2: expected second dataframe, as string
        """
        # Prepare inputs.
        df1 = pd.DataFrame(
            {
                "id": ["1", "2", "3"],
                "index": ["a", "b", "c"],
                "val": ["x", "y", "z"],
                "same": ["s", "s", "s"],
            }
        )
        df2 = df1.copy()
        df2.loc[1, "val"] = "Y"
        df2.loc[2, "index"] = "C"
        # Run test.
        diff_rows, diff_cols = dscdicsv._get_diff(df1, df2)
        self.assertEqual(list(diff_rows), [1, 2])
        self.assertEqual(diff_cols, ["index", "val"])
        actual1, actual2 = dscdicsv._remove_same(
            df1,
            df2,
            diff_rows,
            diff_cols,
            key_columns=key_columns,
            remove_same_columns=remove_same_columns,
            remove_same_rows=remove_same_rows,
        )
        # Check outputs.
        for actual, expected in [(actual1, expected1), (actual2, expected2)]:
            actual = hpanutil.df_to_str(actual, num_rows=None)
            self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test removing nothing.
        """
        # Prepare outputs.
        expected1 = """
          id index val same
        0  1     a   x    s
        1  2     b   y    s
        2  3     c   z    s
        """
        expected2 = """
          id index val same
        0  1     a   x    s
        1  2     b   Y    s
        2  3     C   z    s
        """
        # Run test.
        self.helper([], False, False, expected1, expected2)

    def test2(self) -> None:
        """
        Test removing the columns that are the same, keeping the key.
        """
        # Prepare outputs.
        expected1 = """
          id index val
        0  1     a   x
        1  2     b   y
        2  3     c   z
        """
        expected2 = """
          id index val
        0  1     a   x
        1  2     b   Y
        2  3     C   z
        """
        # Run test.
        self.helper(["id"], True, False, expected1, expected2)

    def test3(self) -> None:
        """
        Test removing the rows that are the same.
        """
        # Prepare outputs.
        expected1 = """
          id index val same
        1  2     b   y    s
        2  3     c   z    s
        """
        expected2 = """
          id index val same
        1  2     b   Y    s
        2  3     C   z    s
        """
        # Run test.
        self.helper([], False, True, expected1, expected2)

    def test4(self) -> None:
        """
        Test removing both the rows and the columns that are the same.
        """
        # Prepare outputs.
        expected1 = """
          index val
        1     b   y
        2     c   z
        """
        expected2 = """
          index val
        1     b   Y
        2     C   z
        """
        # Run test.
        self.helper([], True, True, expected1, expected2)

    def test5(self) -> None:
        """
        Test that identical dataframes have no difference.
        """
        # Prepare inputs.
        df = pd.DataFrame({"a": ["1", "2"], "b": ["x", "y"]})
        # Run test.
        diff_rows, diff_cols = dscdicsv._get_diff(df, df.copy())
        # Check outputs.
        self.assertEqual(len(diff_rows), 0)
        self.assertEqual(diff_cols, [])


# #############################################################################
# Test_diff_csv_py
# #############################################################################


class Test_diff_csv_py(hunitest.TestCase):
    """
    End-to-end tests for the `diff_csv.py` executable.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `diff_csv._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dscdicsv._parse()
        with mock.patch("sys.argv", argv):
            dscdicsv._main(parser)

    def test1(self) -> None:
        """
        Test rendering, aligning by key, and removing what is the same.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "a.csv")
        file2 = os.path.join(scratch_dir, "b.csv")
        txt1 = """
        id,price,qty,name
        1,1.0,5,foo
        2,2.50000,6,bar
        3,NaN,7,baz
        """
        hio.to_file(file1, hprint.dedent(txt1))
        txt2 = """
        id,price,qty,name
        1,1,5,foo
        2,2.5,60,bar
        4,3,1,new
        """
        hio.to_file(file2, hprint.dedent(txt2))
        dst_dir = os.path.join(scratch_dir, "out")
        argv = [
            "diff_csv.py",
            "--file1",
            file1,
            "--file2",
            file2,
            "--key_columns",
            "id",
            "--remove_same_rows",
            "--remove_same_columns",
            "--no_run_vimdiff",
            "--dst_dir",
            dst_dir,
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual1 = hio.from_file(os.path.join(dst_dir, "tmp.diff_csv.1.a.csv"))
        expected1 = """
        id,price,qty,name
        2,2.5,6,bar
        3,,7,baz
        4,,,
        """
        self.assert_equal(
            actual1,
            expected1,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )
        actual2 = hio.from_file(os.path.join(dst_dir, "tmp.diff_csv.2.b.csv"))
        expected2 = """
        id,price,qty,name
        2,2.5,60,bar
        3,,,
        4,3,1,new
        """
        self.assert_equal(
            actual2,
            expected2,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )

    def test2(self) -> None:
        """
        Test that nothing is written when the files are the same after
        rendering.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "a.csv")
        file2 = os.path.join(scratch_dir, "b.csv")
        hio.to_file(file1, "id,price\n1,1.0\n2,NaN\n")
        hio.to_file(file2, "id,price\n1,1\n2,\n")
        dst_dir = os.path.join(scratch_dir, "out")
        argv = [
            "diff_csv.py",
            "--file1",
            file1,
            "--file2",
            file2,
            "--no_run_vimdiff",
            "--dst_dir",
            dst_dir,
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        self.assertFalse(os.path.exists(dst_dir))

    def test3(self) -> None:
        """
        Test that nothing is written with `--dry_run`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "a.csv")
        file2 = os.path.join(scratch_dir, "b.csv")
        hio.to_file(file1, "id,price\n1,1\n")
        hio.to_file(file2, "id,price\n1,2\n")
        dst_dir = os.path.join(scratch_dir, "out")
        argv = [
            "diff_csv.py",
            "--file1",
            file1,
            "--file2",
            file2,
            "--dry_run",
            "--dst_dir",
            dst_dir,
        ]
        # Run test.
        self._run_main(argv)
        # Check outputs.
        self.assertFalse(os.path.exists(dst_dir))
