## Bookmarks flow (IN PROGRESS)

### [.] Improve Bookmark flow

- PR: `HelpersTask1354_Improve_bookmarking_flow`
- Done: `sync_bookmarks.py` runs the whole CSV flow with a single command
  (Raindrop update, tagging, summaries, copy to iCloud), replacing the draft
  `update_bookmarks.sh`

dev_scripts_helpers/download/update_bookmarks.sh

Add the info

Update the CSV file in /Users/saggese/src/notes1/bookmarks/ with the latest
raindrop
Show the situation of the CSV vs the ones in iCloud Drive
Populate the iCloud Drive and /Users/saggese/src/notes1/bookmarks/

### [.] Knowledge base

- Have a system that updates the links from raindrop to the csv in
  /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv
  and create a list of bullet points for each topic so that it is easy to read
  offline

> process_bookmarks.py \
  -i /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
  -o bookmarks \
  --limit 10 --dry_run

- /Users/saggese/src/notes1
  - Update the links
  - ./helpers_root/dev_scripts_helpers/download/README.md
  - Start processing them to build KG

/Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv

head -20 /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv | csvlook

Loop
- Update the gsheet / CSV with the content of raindrop
- Scan the file CSV file to find the next one to update
- download_hn_article_to_md.py -i https://news.ycombinator.com/item?id=49323136
- Change the format to include date.hn_url.<title>...
- Add link to article and to hn to both files
- Download the material
- Copy the interesting files to gdocs
  - concat the files
  - /Users/saggese/Library/CloudStorage/GoogleDrive-saggese@gmail.com/My Drive/HN
  https://drive.google.com/drive/folders/1wT_q9seD3KBXQD-DrLp-C5D5hzaolXsg into a
  path
  vi Red_queen_hypothesis_A_new_way_forward_for_self_improving_AI.2.article_url.summary.md Red_queen_hypothesis_A_new_way_forward_for_self_improving_AI.4.hn_url.summary.md

```
export LINKS_GSHEET=https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M/edit?gid=2008094999#gid=2008094999

> download_link_articles.py --url "$LINKS_GSHEET" --row_idx 1
```

- To understand the structure
  ```
  > ./dev_scripts_helpers/coding_tools/build_call_graph.py --input dev_scripts_helpers/scraping/download_link_articles.py
  ```

# BACKLOG

## Bookmarks flow (BACKLOG)

### [ ] Rename the phase scripts with better names?

### [ ] Update the CSV instead of the gsheet

### [ ] Add score to the template

### [ ] Automatically generate many of them, if not all of them automatically

### [ ] Switch the order of HN and article
- Article_url is always present (even if we bookmark the url)
  - If url is not hackernews than propagate

### [ ] Check that the gsheet has all the expected columns in the expected order

### [x] Save the results on Apple Cloud
- So that Obsidian can pick it up instead of Google Drive
- Done: `sync_bookmarks.py` copies to the iCloud vault (`--dest_type obsidian`) by
  default
```
cd '/Users/saggese/Library/CloudStorage/GoogleDrive-saggese@gmail.com/My Drive/HN'
```

### [ ] Increase number of bullet points

### [ ] Process also non HN articles
- Not in `sync_bookmarks.py` for now
- Today `process_bookmarks.py` marks the rows without an HN URL as `Done=skipped`
  - On 2026-11-22: 399 of the 1778 unprocessed rows of the CSV (1379 have an HN URL)
- Idea: route them with `download_to_md.py`, which already handles html and papers,
  and use a summary template without the HN comments section
- Once done, add a phase to `sync_bookmarks.py`
