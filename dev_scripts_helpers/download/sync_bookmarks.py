#!/usr/bin/env python

"""
Run the whole bookmarks flow on the local CSV with a single command: fetch the
latest `Raindrop.io` links, update the data structures, download and summarize
the articles and the comments, and copy the summaries to iCloud so that
Obsidian can read them.

The script only chains existing scripts, one per action, in this order:

- `update_raindrop`: add the new `Raindrop.io` bookmarks to the CSV, with
  `update_bookmarks_from_raindrop.py --target local_csv`
  - Needs the `RAINDROP_API_TOKEN` env var
- `tag`: fill `Article_url`, `Article_tag`, and `Article_cluster` of the rows
  where they are empty, with `pre_process_bookmarks.py --target local_csv`
  - It calls an LLM, so it costs money
  - Needs the `OPENROUTER_KEY` env var
- `report`: show the situation of the CSV vs the destination (rows to process, to
  skip, to copy), with `process_bookmarks.py --dry_run`
  - It changes nothing
- `process`: download the article and the HN comments of the next `--limit`
  unprocessed rows, summarize them, merge the summaries into one file per row,
  mark the rows `Done`, and copy all the merged summaries missing from the
  destination, with `process_bookmarks.py`
  - It calls an LLM, so it costs money
  - Needs the `OPENROUTER_KEY` env var
  - It always backs up the summaries to the git dir of `process_bookmarks.py`

The default actions are `update_raindrop`, `tag`, and `process`. Every phase is
incremental, so the command can be re-run at any time.

The destination is iCloud (the Obsidian vault) by default. A different one is
selected with `--dest_type`.

With `--dry_run`, the script prints the commands of `update_raindrop` and `tag`
without running them, since they have no dry run. It runs `process_bookmarks.py`
with `--dry_run`, which changes nothing.

# Usage Example

- Run the whole flow, processing the next 10 rows (default):
> sync_bookmarks.py

- Show the situation of the CSV vs iCloud, without changing anything:
> sync_bookmarks.py --clear_actions --action report

- Show what the whole flow would do:
> sync_bookmarks.py --dry_run

- Process the next 50 rows:
> sync_bookmarks.py --limit 50

- Skip the update from Raindrop and the tagging, and only process the rows:
> sync_bookmarks.py --clear_actions --action process

- Only copy the already processed rows to iCloud, without downloading anything:
> sync_bookmarks.py --clear_actions --action process --limit 0

- Use another CSV and another LLM model:
> sync_bookmarks.py \
    --csv bookmarks.csv \
    --model openrouter/anthropic/claude-haiku-4.5

Import as:

import dev_scripts_helpers.download.sync_bookmarks as dshdsybo
"""

import argparse
import logging
import os
from typing import Dict, List

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem

import dev_scripts_helpers.download.bookmark_utils as dshdbout

_LOG = logging.getLogger(__name__)


# #############################################################################
# Constants
# #############################################################################

# Default CSV tracking the bookmarks.
_DEFAULT_CSV = (
    "/Users/saggese/src/notes1/bookmarks/"
    "update_gsheet_links_from_raindrop.combined_data.csv"
)
_DEFAULT_LIMIT = 10
# Copy the summaries to the iCloud vault of Obsidian.
_DEFAULT_DEST_TYPE = "obsidian"

# The actions are executed in this order.
_VALID_ACTIONS = ["update_raindrop", "tag", "report", "process"]
_DEFAULT_ACTIONS = ["update_raindrop", "tag", "process"]
# The scripts of these actions have no `--dry_run`: in a dry run, their
# command is only printed.
_ACTIONS_WITHOUT_DRY_RUN = ["update_raindrop", "tag"]
# Env vars needed by the scripts of each action.
_ACTION_TO_ENV_VARS = {
    "update_raindrop": ["RAINDROP_API_TOKEN"],
    "tag": ["OPENROUTER_KEY"],
    "report": [],
    "process": ["OPENROUTER_KEY"],
}


# #############################################################################
# CSV stats
# #############################################################################


def _get_csv_stats(csv_path: str) -> Dict[str, int]:
    """
    Count the rows of the bookmarks CSV by state.

    :param csv_path: path to the bookmarks CSV
    :return: number of rows
        - `num_rows`: all the rows
        - `num_untagged`: rows with an empty `Article_tag`
        - `num_done`: rows with `Done=yes`
        - `num_skipped`: rows with `Done=skipped`
        - `num_todo`: rows with `Done` empty, i.e., still to process
    """
    _LOG.debug(hprint.to_str("csv_path"))
    rows = dshdbout.read_csv(csv_path)
    done_values = [(row.get("Done") or "").strip() for row in rows]
    stats = {
        "num_rows": len(rows),
        "num_untagged": sum(
            1 for row in rows if not (row.get("Article_tag") or "").strip()
        ),
        "num_done": done_values.count("yes"),
        "num_skipped": done_values.count("skipped"),
        "num_todo": done_values.count(""),
    }
    _LOG.debug(hprint.to_str("stats"))
    return stats


def _stats_to_str(before: Dict[str, int], after: Dict[str, int]) -> str:
    """
    Format the change of the CSV stats, one line per stat.

    E.g.,
    ```
    num_rows: 1834 -> 1850 (+16)
    num_done: 56 -> 66 (+10)
    ```

    :param before: stats before the run
    :param after: stats after the run, with the same keys as `before`
    :return: one line per stat
    """
    hdbg.dassert_eq(sorted(before.keys()), sorted(after.keys()))
    lines = []
    for key, value_before in before.items():
        value_after = after[key]
        lines.append(
            f"{key}: {value_before} -> {value_after} "
            f"({value_after - value_before:+d})"
        )
    return "\n".join(lines)


# #############################################################################
# Commands
# #############################################################################


def _check_env_vars(actions: List[str]) -> None:
    """
    Check that the env vars needed by the actions are set.

    Fail before running any action, so that a missing token does not stop the
    flow half way.

    :param actions: actions that will run for real
    """
    env_vars = []
    for action in actions:
        env_vars.extend(_ACTION_TO_ENV_VARS[action])
    for env_var in sorted(set(env_vars)):
        hdbg.dassert_in(
            env_var,
            os.environ,
            "The env var '%s' is not set but it is needed by the actions %s",
            env_var,
            actions,
        )


def _build_cmd(
    action: str,
    *,
    csv_path: str,
    limit: int,
    dest_type: str,
    dest_dir: str,
    output_dir: str,
    model: str,
    dry_run: bool,
    log_level: str,
) -> str:
    """
    Build the command line of an action.

    :param action: action to run
    :param csv_path: path to the bookmarks CSV
    :param limit: max number of rows to process, for `report` and `process`
    :param dest_type: destination of the merged summaries, for `report` and
        `process`
    :param dest_dir: override of the dir of `dest_type`, or `""` to use the
        default one
    :param output_dir: local dir caching the downloaded files, or `""` to use
        the default one of `process_bookmarks.py`
    :param model: LLM model, or `""` to use the default one of each script
    :param dry_run: pass `--dry_run` to `process_bookmarks.py`
    :param log_level: verbosity forwarded to the called script
    :return: command line
    """
    _LOG.debug(hprint.to_str("action csv_path limit dest_type dry_run"))
    if action == "update_raindrop":
        script = hgit.find_file_in_git_tree("update_bookmarks_from_raindrop.py")
        cmd = [
            script,
            "--target local_csv",
            f"--local_csv {csv_path}",
            "--action download_raindrop_data",
            "--action combine_data",
        ]
    elif action == "tag":
        script = hgit.find_file_in_git_tree("pre_process_bookmarks.py")
        cmd = [
            script,
            "--target local_csv",
            f"--local_csv {csv_path}",
            "--all_actions",
        ]
        if model:
            cmd.append(f"--model {model}")
    elif action in ("report", "process"):
        script = hgit.find_file_in_git_tree("process_bookmarks.py")
        cmd = [
            script,
            f"--input {csv_path}",
            f"--limit {limit}",
            f"--dest_type {dest_type}",
        ]
        if dest_dir:
            cmd.append(f'--dest_dir "{dest_dir}"')
        if output_dir:
            cmd.append(f"--output_dir {output_dir}")
        if model:
            cmd.append(f"--model {model}")
        if action == "report" or dry_run:
            cmd.append("--dry_run")
    else:
        raise ValueError(f"Invalid action='{action}'")
    # Forward the verbosity to the called script.
    cmd.append(f"-v {log_level}")
    cmd = " ".join(cmd)
    _LOG.debug(hprint.to_str("cmd"))
    return cmd


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--csv",
        action="store",
        default=_DEFAULT_CSV,
        help="Path to the bookmarks CSV, updated in place",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=_DEFAULT_LIMIT,
        help="Max number of unprocessed rows to download and summarize "
        "(0 to only copy the rows already processed)",
    )
    parser.add_argument(
        "--dest_type",
        action="store",
        choices=["obsidian", "gdrive", "none"],
        default=_DEFAULT_DEST_TYPE,
        help="Destination of the merged summaries: 'obsidian' is the iCloud "
        "vault of Obsidian, 'gdrive' is Google Drive, 'none' keeps them in "
        "the local output dir",
    )
    parser.add_argument(
        "--dest_dir",
        action="store",
        default="",
        help="Override the built-in dir of `--dest_type`",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        default="",
        help="Local dir caching the downloaded files. Empty uses the default "
        "of `process_bookmarks.py`, which is relative to the current dir",
    )
    parser.add_argument(
        "--model",
        action="store",
        default="",
        help="LLM model for tagging and summarizing (e.g., "
        "`openrouter/anthropic/claude-haiku-4.5`). Empty uses the default of "
        "each script",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the commands of `update_raindrop` and `tag` without "
        "running them, and run `process_bookmarks.py` with `--dry_run`",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True),
    )
    hdbg.dassert_file_exists(args.csv)
    hdbg.dassert_lte(0, args.limit)
    # Check the env vars before running any action. A dry run does not need
    # them, since no LLM or Raindrop call is made.
    if not args.dry_run:
        _check_env_vars(actions)
    stats_before = _get_csv_stats(args.csv)
    # Run the actions in order, stopping at the first one that fails.
    for action in _VALID_ACTIONS:
        to_execute, actions = hselacti.mark_action(action, actions)
        if not to_execute:
            continue
        cmd = _build_cmd(
            action,
            csv_path=args.csv,
            limit=args.limit,
            dest_type=args.dest_type,
            dest_dir=args.dest_dir,
            output_dir=args.output_dir,
            model=args.model,
            dry_run=args.dry_run,
            log_level=args.log_level,
        )
        if args.dry_run and action in _ACTIONS_WITHOUT_DRY_RUN:
            _LOG.warning("[DRY_RUN] Would run '%s'", cmd)
        else:
            hsystem.system(cmd, suppress_output=False, print_command=True)
    hdbg.dassert_eq(
        actions, [], "There are unprocessed actions: %s", str(actions)
    )
    # Report what changed in the CSV.
    stats_after = _get_csv_stats(args.csv)
    _LOG.info(
        "%s\n%s",
        hprint.frame("# Changes in the CSV"),
        _stats_to_str(stats_before, stats_after),
    )


if __name__ == "__main__":
    _main(_parse())
