#!/usr/bin/env python

import logging
import os
import unittest.mock as umock
from typing import Any, Dict, List

import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

import dev_scripts_helpers.download.bookmark_utils as dshdbout
import dev_scripts_helpers.download.sync_bookmarks as dshdsybo

_LOG = logging.getLogger(__name__)

_COLUMNS = [
    "Title",
    "Article_url",
    "Hn_url",
    "Timestamp",
    "Article_tag",
    "Article_cluster",
    "Done",
]


def _get_rows() -> List[Dict[str, Any]]:
    """
    Get the rows of a CSV with one row per state.

    :return: rows with a done, a skipped, a tagged to do, and an untagged to do
        row
    """
    rows = [
        ("Done", "AI", "yes"),
        ("Skipped", "", "skipped"),
        ("Todo tagged", "Python", ""),
        ("Todo untagged", "", ""),
    ]
    ret = []
    for i, (title, tag, done) in enumerate(rows):
        ret.append(
            {
                "Title": title,
                "Article_url": f"https://example.com/{i}",
                "Hn_url": f"https://news.ycombinator.com/item?id={i}",
                "Timestamp": f"2024-01-0{i + 1} 00:00:00",
                "Article_tag": tag,
                "Article_cluster": "",
                "Done": done,
            }
        )
    return ret


# #############################################################################
# Test_get_csv_stats
# #############################################################################


class Test_get_csv_stats(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the rows are counted by state.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        csv_path = os.path.join(scratch_dir, "bookmarks.csv")
        dshdbout.write_csv(csv_path, _get_rows(), fieldnames=_COLUMNS)
        # Prepare outputs.
        expected = {
            "num_rows": 4,
            "num_untagged": 2,
            "num_done": 1,
            "num_skipped": 1,
            "num_todo": 2,
        }
        # Run test.
        actual = dshdsybo._get_csv_stats(csv_path)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that a CSV with only the header has no rows in any state.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        csv_path = os.path.join(scratch_dir, "empty.csv")
        dshdbout.write_csv(csv_path, [], fieldnames=_COLUMNS)
        # Prepare outputs.
        expected = {
            "num_rows": 0,
            "num_untagged": 0,
            "num_done": 0,
            "num_skipped": 0,
            "num_todo": 0,
        }
        # Run test.
        actual = dshdsybo._get_csv_stats(csv_path)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_stats_to_str
# #############################################################################


class Test_stats_to_str(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that each stat shows the value before, after, and the change.
        """
        # Prepare inputs.
        before = {"num_rows": 10, "num_done": 3, "num_todo": 7}
        after = {"num_rows": 12, "num_done": 5, "num_todo": 7}
        # Prepare outputs.
        expected = """
        num_rows: 10 -> 12 (+2)
        num_done: 3 -> 5 (+2)
        num_todo: 7 -> 7 (+0)
        """
        # Run test.
        actual = dshdsybo._stats_to_str(before, after)
        # Check outputs.
        self.assert_equal(actual, hprint.dedent(expected))

    def test2(self) -> None:
        """
        Test that a stat that decreases has a negative change.
        """
        # Prepare inputs.
        before = {"num_todo": 7}
        after = {"num_todo": 4}
        # Prepare outputs.
        expected = "num_todo: 7 -> 4 (-3)"
        # Run test.
        actual = dshdsybo._stats_to_str(before, after)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that stats with different keys are rejected.
        """
        # Prepare inputs.
        before = {"num_rows": 10}
        after = {"num_done": 3}
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdsybo._stats_to_str(before, after)


# #############################################################################
# Test_check_env_vars
# #############################################################################


class Test_check_env_vars(hunitest.TestCase):
    def helper(self, env_vars: List[str]) -> Dict[str, str]:
        """
        Get the env with only the passed tokens set.

        :param env_vars: names of the tokens to set
        :return: env without the two tokens, plus the passed ones
        """
        tokens = ["RAINDROP_API_TOKEN", "OPENROUTER_KEY"]
        env = {k: v for k, v in os.environ.items() if k not in tokens}
        for env_var in env_vars:
            env[env_var] = "value"
        return env

    def test1(self) -> None:
        """
        Test that no error is raised when all the tokens are set.
        """
        # Prepare inputs.
        actions = ["update_raindrop", "tag", "process"]
        env = self.helper(["RAINDROP_API_TOKEN", "OPENROUTER_KEY"])
        # Run test and check output.
        with umock.patch.dict(os.environ, env, clear=True):
            dshdsybo._check_env_vars(actions)

    def test2(self) -> None:
        """
        Test that a missing `RAINDROP_API_TOKEN` is reported.
        """
        # Prepare inputs.
        actions = ["update_raindrop"]
        env = self.helper(["OPENROUTER_KEY"])
        # Prepare outputs.
        expected = "The env var 'RAINDROP_API_TOKEN' is not set"
        # Run test.
        with (
            umock.patch.dict(os.environ, env, clear=True),
            self.assertRaises(AssertionError) as cm,
        ):
            dshdsybo._check_env_vars(actions)
        # Check outputs.
        self.assertIn(expected, str(cm.exception))

    def test3(self) -> None:
        """
        Test that `report` does not need any token.
        """
        # Prepare inputs.
        actions = ["report"]
        env = self.helper([])
        # Run test and check output.
        with umock.patch.dict(os.environ, env, clear=True):
            dshdsybo._check_env_vars(actions)

    def test4(self) -> None:
        """
        Test that a missing `OPENROUTER_KEY` is reported for `process`.
        """
        # Prepare inputs.
        actions = ["process"]
        env = self.helper(["RAINDROP_API_TOKEN"])
        # Run test and check output.
        with (
            umock.patch.dict(os.environ, env, clear=True),
            self.assertRaises(AssertionError),
        ):
            dshdsybo._check_env_vars(actions)


# #############################################################################
# Test_build_cmd
# #############################################################################


class Test_build_cmd(hunitest.TestCase):
    def helper(self, action: str, **kwargs: Any) -> str:
        """
        Build the command of an action, with the defaults overridden by
        `kwargs`.

        :param action: action to build the command for
        :param kwargs: arguments of `_build_cmd()` to override
        :return: command line
        """
        params = {
            "csv_path": "bookmarks.csv",
            "limit": 10,
            "dest_type": "obsidian",
            "dest_dir": "",
            "output_dir": "",
            "model": "",
            "dry_run": False,
            "log_level": "INFO",
        }
        params.update(kwargs)
        actual = dshdsybo._build_cmd(action, **params)
        return actual

    def test1(self) -> None:
        """
        Test the command of `update_raindrop`.
        """
        # Prepare inputs.
        action = "update_raindrop"
        script = hgit.find_file_in_git_tree("update_bookmarks_from_raindrop.py")
        # Prepare outputs.
        expected = (
            f"{script} --target local_csv --local_csv bookmarks.csv "
            "--action download_raindrop_data --action combine_data -v INFO"
        )
        # Run test.
        actual = self.helper(action)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test the command of `tag`, with a model.
        """
        # Prepare inputs.
        action = "tag"
        model = "openrouter/anthropic/claude-haiku-4.5"
        script = hgit.find_file_in_git_tree("pre_process_bookmarks.py")
        # Prepare outputs.
        expected = (
            f"{script} --target local_csv --local_csv bookmarks.csv "
            f"--all_actions --model {model} -v INFO"
        )
        # Run test.
        actual = self.helper(action, model=model)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test the command of `process` with the defaults.
        """
        # Prepare inputs.
        action = "process"
        script = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = (
            f"{script} --input bookmarks.csv --limit 10 --dest_type obsidian "
            "-v INFO"
        )
        # Run test.
        actual = self.helper(action)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test the command of `process` with all the options.
        """
        # Prepare inputs.
        action = "process"
        script = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = (
            f"{script} --input bookmarks.csv --limit 3 --dest_type gdrive "
            '--dest_dir "/tmp/my dir" --output_dir out '
            "--model my_model -v DEBUG"
        )
        # Run test.
        actual = self.helper(
            action,
            limit=3,
            dest_type="gdrive",
            dest_dir="/tmp/my dir",
            output_dir="out",
            model="my_model",
            log_level="DEBUG",
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test that `process` passes `--dry_run` in a dry run.
        """
        # Prepare inputs.
        action = "process"
        script = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = (
            f"{script} --input bookmarks.csv --limit 10 --dest_type obsidian "
            "--dry_run -v INFO"
        )
        # Run test.
        actual = self.helper(action, dry_run=True)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test that `report` always passes `--dry_run`, even without a dry run.
        """
        # Prepare inputs.
        action = "report"
        script = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = (
            f"{script} --input bookmarks.csv --limit 10 --dest_type obsidian "
            "--dry_run -v INFO"
        )
        # Run test.
        actual = self.helper(action, dry_run=False)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test7(self) -> None:
        """
        Test that an invalid action is rejected.
        """
        # Prepare inputs.
        action = "invalid_action"
        # Run test and check output.
        with self.assertRaises(ValueError):
            self.helper(action)


# #############################################################################
# Test_sync_bookmarks_py
# #############################################################################


class Test_sync_bookmarks_py(hunitest.TestCase):
    """
    End-to-end tests of `sync_bookmarks.py`, capturing the commands instead of
    running the scripts, since they call Raindrop and an LLM.
    """

    def _create_csv(self) -> str:
        """
        Create a bookmarks CSV in the scratch space.

        :return: path to the CSV
        """
        scratch_dir = self.get_scratch_space()
        csv_path = os.path.join(scratch_dir, "bookmarks.csv")
        dshdbout.write_csv(csv_path, _get_rows(), fieldnames=_COLUMNS)
        return csv_path

    def _run_main(
        self, argv: List[str], *, env_vars: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Run `sync_bookmarks._main()` with a mocked `sys.argv` and capture the
        system calls.

        :param argv: command-line argument list to inject
        :param env_vars: names of the tokens set during the run
        :return: the captured system calls
        """
        tokens = ["RAINDROP_API_TOKEN", "OPENROUTER_KEY"]
        env = {k: v for k, v in os.environ.items() if k not in tokens}
        for env_var in env_vars:
            env[env_var] = "value"
        parser = dshdsybo._parse()
        with (
            umock.patch.dict(os.environ, env, clear=True),
            umock.patch("sys.argv", argv),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            dshdsybo._main(parser)
        return sys_calls

    def test1(self) -> None:
        """
        Test that the default actions run `update_raindrop`, `tag`, and
        `process`, in this order.
        """
        # Prepare inputs.
        csv_path = self._create_csv()
        argv = ["sync_bookmarks.py", "--csv", csv_path]
        raindrop = hgit.find_file_in_git_tree(
            "update_bookmarks_from_raindrop.py"
        )
        pre_process = hgit.find_file_in_git_tree("pre_process_bookmarks.py")
        process = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = f"""[
        {{
        'function': hsystem.system,
        'args': ('{raindrop} --target local_csv --local_csv {csv_path} --action download_raindrop_data --action combine_data -v INFO',),
        'kwargs': {{'suppress_output': False, 'print_command': True}},
        }},
        {{
        'function': hsystem.system,
        'args': ('{pre_process} --target local_csv --local_csv {csv_path} --all_actions -v INFO',),
        'kwargs': {{'suppress_output': False, 'print_command': True}},
        }},
        {{
        'function': hsystem.system,
        'args': ('{process} --input {csv_path} --limit 10 --dest_type obsidian -v INFO',),
        'kwargs': {{'suppress_output': False, 'print_command': True}},
        }},
        ]"""
        # Run test.
        sys_calls = self._run_main(
            argv, env_vars=["RAINDROP_API_TOKEN", "OPENROUTER_KEY"]
        )
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test2(self) -> None:
        """
        Test that a dry run does not run `update_raindrop` and `tag`, and runs
        `process` with `--dry_run`.
        """
        # Prepare inputs.
        csv_path = self._create_csv()
        argv = ["sync_bookmarks.py", "--csv", csv_path, "--dry_run"]
        process = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = f"""[
        {{
        'function': hsystem.system,
        'args': ('{process} --input {csv_path} --limit 10 --dest_type obsidian --dry_run -v INFO',),
        'kwargs': {{'suppress_output': False, 'print_command': True}},
        }},
        ]"""
        # Run test. A dry run needs no token.
        sys_calls = self._run_main(argv, env_vars=[])
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test3(self) -> None:
        """
        Test that only the selected action runs, and it needs no token for
        `report`.
        """
        # Prepare inputs.
        csv_path = self._create_csv()
        argv = [
            "sync_bookmarks.py",
            "--csv",
            csv_path,
            "--clear_actions",
            "--action",
            "report",
            "--limit",
            "5",
        ]
        process = hgit.find_file_in_git_tree("process_bookmarks.py")
        # Prepare outputs.
        expected = f"""[
        {{
        'function': hsystem.system,
        'args': ('{process} --input {csv_path} --limit 5 --dest_type obsidian --dry_run -v INFO',),
        'kwargs': {{'suppress_output': False, 'print_command': True}},
        }},
        ]"""
        # Run test.
        sys_calls = self._run_main(argv, env_vars=[])
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected)

    def test4(self) -> None:
        """
        Test that a missing token stops the flow before running any command.
        """
        # Prepare inputs.
        csv_path = self._create_csv()
        argv = ["sync_bookmarks.py", "--csv", csv_path]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            self._run_main(argv, env_vars=["OPENROUTER_KEY"])

    def test5(self) -> None:
        """
        Test that a missing CSV is rejected.
        """
        # Prepare inputs.
        csv_path = os.path.join(self.get_scratch_space(), "missing.csv")
        argv = ["sync_bookmarks.py", "--csv", csv_path]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            self._run_main(argv, env_vars=[])
