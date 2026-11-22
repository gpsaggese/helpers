I want to extend the flow of dev_scripts_helpers/download by downloading the latest
links from raindrop, update the data structures, download the articles and the
comments, generating the summaries, and uploading them to icloud so that obsidian can
read them

It should be a single command that pulls the phases and scripts together

Propose a plan on how to use the current scripts to achieve this

## Findings

- Existing scripts already cover every phase. Only the glue is missing
  - `update_bookmarks.sh` is a draft of the glue, with phases toggled by hand
    (`if [[ 0 == 1 ]]`) and hardcoded paths
- Phase to script mapping (all on the local CSV
  `/Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv`)
  - Phase 1, fetch new links from Raindrop and merge them into the CSV
    - `update_bookmarks_from_raindrop.py --target local_csv --local_csv CSV`
      `--action download_raindrop_data --action combine_data`
    - Needs `RAINDROP_API_TOKEN`
    - Takes the cutoff from the newest `Timestamp` in the CSV and prepends new rows
  - Phase 2, update data structures (`Article_url`, `Article_tag`,
    `Article_cluster`)
    - `pre_process_bookmarks.py --target local_csv --local_csv CSV --all_actions`
    - Only fills rows with empty target columns, so it is incremental
    - Costs LLM money. Needs `OPENROUTER_KEY`
  - Phase 3, download articles and HN comments, summarize, merge
    - `process_bookmarks.py -i CSV --limit N`
    - Calls `download_hn_article_to_md.py` per row, merges the two summaries into
      `<date>.hn_<id>.<title>.summary.md`, sets `Done=yes`, saves the CSV after each
      row (resumable)
  - Phase 4, upload to iCloud for Obsidian
    - Same `process_bookmarks.py` call with `--dest_type obsidian`
    - Default dir is `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/GP/`
      (exists, holds 44 summaries now)
    - Reconciliation copies every `Done=yes` row missing from the destination, with
      no re-download and no LLM cost
    - It always backs up to the git dir `/Users/saggese/src/notes1/bookmarks`
  - Status report (CSV vs iCloud)
    - Same call with `--dry_run`. It writes nothing
- `download_link_articles.py` is **not** needed
  - `process_bookmarks.py` shells out to `download_hn_article_to_md.py` itself
  - Step 2 of "CSV-Based Bookmark Processing Workflow" in the README downloads and
    summarizes twice. Fix the README
- Current state of the CSV
  - 1834 rows. 56 `Done=yes`. 1778 not done
    - 1379 have a real HN URL. They are processable
    - 399 have no HN URL. `process_bookmarks.py` marks them `Done=skipped`
  - 65 rows have empty `Article_tag` and `Article_url`
  - At `--limit 10` the backlog takes ~138 runs. Cost is printed per run
- Gaps
  - `update_bookmarks_from_raindrop.py` and `pre_process_bookmarks.py` have no
    `--dry_run`
  - Only one viewing destination per call. Fine: iCloud only is what we need
  - Non-HN bookmarks are skipped. They are in the backlog of `todos.md`

## Plan

- [x] Add one Python driver `dev_scripts_helpers/download/sync_bookmarks.py`
  - It chains the three existing scripts with `hsystem.system()`
    - No logic is duplicated. This is the same pattern `process_bookmarks.py` uses
      for `download_hn_article_to_md.py`
  - Actions, via `hselacti` (same style as the other scripts)
    - `update_raindrop` runs phase 1
    - `tag` runs phase 2
    - `report` runs `process_bookmarks.py --dry_run` (CSV vs iCloud status)
    - `process` runs phases 3 and 4
  - Default actions: `update_raindrop`, `tag`, `process`
    - So `sync_bookmarks.py` alone does the whole flow
  - Options
    - `--csv`, default the `notes1` path above
    - `--limit`, default 10. Passed to `process_bookmarks.py`
    - `--dest_type`, default `obsidian`. `--dest_dir` is passed through
    - `--model`, passed to `pre_process_bookmarks.py` and `process_bookmarks.py`
    - `--dry_run`: print the commands. Run only the `report` action
  - Fail fast, before any phase runs
    - `RAINDROP_API_TOKEN` and `OPENROUTER_KEY` are set (only when needed)
    - The CSV exists
    - Stop the chain when a phase returns non-zero
  - Log a final summary
    - New rows added, rows tagged, rows processed, rows skipped, run cost, rows
      copied to iCloud
- [x] Add unit tests `test/test_sync_bookmarks.py`
  - No mocks. Run the driver with `--dry_run` and check the generated commands with
    `check_string()`
  - Test the argument parsing and the action selection
  - Test the env var pre-check
- [x] Replace `update_bookmarks.sh`
  - Remove it, or make it a one-line call to `sync_bookmarks.py`
- [x] Update `dev_scripts_helpers/download/README.md`
  - Add `sync_bookmarks.py` to the file table
  - Add a section "Description of Executables" with examples
  - Add the new single-command workflow to "Description of Workflows"
  - Remove the redundant `download_link_articles.py` step from the CSV workflow
- [x] Update `dev_scripts_helpers/download/todos.md`
  - Mark the "Improve Bookmark flow" and the "Save the results on Apple Cloud" items
- [.] First real run, by hand, with the user watching
  - `sync_bookmarks.py --dry_run` to see the status
  - `sync_bookmarks.py --limit 3` to check Obsidian shows the new files
- [x] Run the commit gates: `pre-commit.py`. Fix all errors
- [x] `git add` the new files. Do not commit

## Decisions

- Q1. Non-HN bookmarks: not now. A note is in `todos.md`
- Q2. New Python driver: yes
- Q3. Default `--limit` 10: yes
- Q4. iCloud only, with the git backup always on: yes
- Focus on the CSV flow, not on the gsheet. The driver only uses `--target local_csv`

## Result

### Done
- Added `dev_scripts_helpers/download/sync_bookmarks.py`
  - Chains `update_bookmarks_from_raindrop.py`, `pre_process_bookmarks.py`, and
    `process_bookmarks.py` on the CSV, with the actions `update_raindrop`, `tag`,
    `report`, and `process`
  - Default: `sync_bookmarks.py` runs `update_raindrop`, `tag`, and `process`
    with `--limit 10` and `--dest_type obsidian` (iCloud)
  - Checks the tokens first, forwards `-v`, and logs how the CSV changed
- Added `test/test_sync_bookmarks.py` with 21 tests. They pass, with
  `process_bookmarks` tests (45 in total)
  - They capture the commands, so no Raindrop or LLM call is made
- Ran `sync_bookmarks.py --dry_run` on the real CSV. It changed nothing
- Removed `update_bookmarks.sh`, replaced by the driver
- Updated `README.md` (table, executable section, new workflow, removed the
  redundant `download_link_articles.py` step) and `todos.md`
- Commit gates pass (`pre-commit.py`). New files are `git add`ed, not committed

### Not done
- A real run that calls Raindrop and the LLM. It needs the tokens and spends money
  - Run `sync_bookmarks.py --limit 3` by hand to check Obsidian
- Non-HN bookmarks (399 rows now). They stay `Done=skipped`. See `todos.md`
- `--dry_run` does not run the Raindrop update and the tagging, since those
  scripts have no `--dry_run`. Their commands are only printed
- No cost total in the final log. `process_bookmarks.py` logs it in its own output
- The raw download cache is relative to the current dir
  (`--output_dir` of `process_bookmarks.py`). Run from the same dir or pass
  `--output_dir`
