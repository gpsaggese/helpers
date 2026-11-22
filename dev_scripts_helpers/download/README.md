# Download Tools
- Scripts to download, convert, and summarize content (web pages, academic papers,
  Hacker News submissions, podcast transcripts) to Markdown
- A pipeline for managing a CSV / Google Sheets-based link database

## Structure of the Dir
- `test/`
  - Unit tests for the download and bookmark-processing scripts

## Description of Files
| File                                   | Description                                                                  | Cluster             |
| -------------------------------------- | ---------------------------------------------------------------------------- | ------------------- |
| `bookmark_utils.py`                    | Shared helpers for downloading/uploading Google Sheets data and CSV files    | Shared Utilities    |
| `download_academic_paper_to_md.py`     | Download an academic paper (arXiv/DOI/SSRN/PDF), convert, summarize          | Content Downloaders |
| `download_hn_article_to_md.py`         | Download a Hacker News submission (comments and article), convert, summarize | Content Downloaders |
| `download_html_to_md.py`               | Download a generic web page and convert it to Markdown, summarize            | Content Downloaders |
| `download_link_articles.py`            | Download/summarize article content and HN comments for rows from a local CSV or a Gsheet | Bookmark Pipelines  |
| `download_to_md.py`                    | Detect input type and dispatch to the matching `download_*_to_md.py` script  | Content Downloaders |
| `download_utils.py`                    | Shared helpers for article titles, LLM summaries, and block-page detection   | Shared Utilities    |
| `download_with_chrome.py`              | Download a page or file (e.g., an SSRN PDF) with a real Chrome over CDP      | Content Downloaders |
| `podcast_dl.py`                        | Download and format a podcast transcript from various sources                | Podcast Tools       |
| `podcast_dl_example.sh`                | Example invocations of `podcast_dl.py` for each supported source type        | Podcast Tools       |
| `pre_process_bookmarks.py`             | Pipeline to extract HN article URLs and classify articles by topic/cluster, for a local CSV or a Gsheet | Bookmark Pipelines  |
| `process_bookmarks.py`                 | Download, summarize, and archive HN bookmarks from a local CSV to a destination | Bookmark Pipelines  |
| `process_one_off_gsheet_links.py`      | One-off pipeline to rename topic tags in the Gsheet (data migration, Gsheet only) | Gsheet Pipelines    |
| `sync_bookmarks.py`                    | Run the whole CSV bookmark flow (Raindrop, tag, summarize, iCloud) in one command | Bookmark Pipelines  |
| `update_bookmarks_from_raindrop.py`    | Sync new bookmarks from `Raindrop.io` into a local CSV or the Gsheet         | Bookmark Pipelines  |

## Link Database Schema
- The links are stored in a local CSV, the main data store of the bookmark flow
  - E.g., the default of `sync_bookmarks.py` is
    `/Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv`
  - The scripts update it in place, so a run can resume
- The same schema is used by the Google Sheets document, an alternative store
  supported by `update_bookmarks_from_raindrop.py`, `pre_process_bookmarks.py`, and
  `download_link_articles.py`
  - E.g.,
    ```bash
    > export LINKS_GSHEET="<your-google-sheets-url>"

    > export LINKS_GSHEET=https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M/edit?gid=2008094999#gid=2008094999
    ```

- The CSV (and the Google Sheets document) contains the following columns:
  - `Title`: Article title
    - _Example_: "Rust is not a good C replacement"
  - `Article_url`: URL of the actual article (extracted from the HN submission if
    applicable)
    - _Example_:
      https://medium.com/airbnb-engineering/chronon-airbnbs-ml-feature-platform-is-now-open-source-d9c4dba859e8
    - It is empty for a new row, until `pre_process_bookmarks.py` fills it
  - `Hn_url`: Source URL of the bookmark, normally a Hacker News submission URL
    - _Example_: https://news.ycombinator.com/item?id=40212490
    - `Raindrop.io` puts the URL of any bookmark here, so it can also be a plain
      article link: `process_bookmarks.py` marks such a row `Done=skipped`
  - `Timestamp`: Date and time when added
    - Format: YYYY-MM-DD HH:MM:SS
    - _Example_: 2024-04-30 22:23:54
  - `Article_tag`: Categorized topic/tag for the article
    - _Example_: "Automated Theorem Proving", "AI Infrastructure", "Python Ecosystem"
  - `Article_cluster`: High-level cluster grouping topics
    - _Example_: "AI", "Data/Infra", "Dev tools", "Finance", "Math", "Business",
      "CyberSec", "SwEng"
  - `Interesting (1 to 5)`: Relevance rating
  - `Notes`: Additional notes and comments
  - `Done`: Processing state set by `process_bookmarks.py`
    - Empty: not processed yet
    - `yes`: downloaded, summarized, and merged
    - `skipped`: the row has no real HN item URL, so it is not processed

## LLM Model
- All the tools that summarize or tag with an LLM use the same default model, an
  OpenRouter one (`DEFAULT_MODEL` in `helpers/hllm_cli.py`)
  - It needs the `OPENROUTER_KEY` env var
  - `llm_cli.py` installs the `llm-openrouter` plugin on the fly, so no setup is
    needed besides the key
- Every such tool has a `--model` option to use another model
  - Use the `openrouter/<provider>/<model>` prefix, e.g.,
    `openrouter/anthropic/claude-haiku-4.5`
  - A direct name like `gpt-4o-mini` is not routed through OpenRouter: it goes to its
    provider, e.g., OpenAI, and needs the key and the credits of that provider
- Tools with `--model`: `download_to_md.py`, `download_academic_paper_to_md.py`,
  `download_html_to_md.py`, `download_hn_article_to_md.py`,
  `download_link_articles.py`, `pre_process_bookmarks.py`, `process_bookmarks.py`,
  `sync_bookmarks.py`
- `download_to_md.py` forwards `--model` to the script it dispatches to

## Description of Executables

### `download_to_md.py`

#### What It Does
- Detects the type of `--input` and dispatches to the matching converter:
  - **hn**: HN submission URL (`news.ycombinator.com/item?id=...`) ->
    `download_hn_article_to_md.py`
  - **academic_paper**: arXiv URL, DOI (URL or bare), SSRN URL, generic `.pdf` URL,
    or path to a local `.pdf` file -> `download_academic_paper_to_md.py`
  - **html**: anything else (generic web page) -> `download_html_to_md.py`
- `--output` is only forwarded to the dispatched script when specified; otherwise the
  dispatched script derives its own output name
- `--email` is only forwarded to `download_academic_paper_to_md.py`, which uses it
  for the Unpaywall lookup (see below)

#### Examples
- Download a generic web page (auto-detected as html):
  ```bash
  > download_to_md.py --input "https://example.com/article"
  ```

- Download an arXiv paper (auto-detected as academic_paper):
  ```bash
  > download_to_md.py --input "https://arxiv.org/abs/1706.03762"
  ```

- Use a PDF already saved locally (auto-detected as academic_paper):
  ```bash
  > download_to_md.py --input ~/Downloads/ssrn_5277078.pdf
  ```

- Download a DOI, looking up an open-access PDF with Unpaywall:
  ```bash
  > download_to_md.py --input "10.1038/nature12373" --email me@example.org
  ```

- Download an HN submission with an explicit output base name:
  ```bash
  > download_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --output ./links/my_article
  ```

### `download_academic_paper_to_md.py`

#### What It Does
- Downloads academic papers from arXiv, DOI, SSRN, or a generic PDF URL, or takes a
  PDF already saved locally
- Saves the paper with a standardized base name, e.g.,
  `2016.Ribeiro_et_al.Why_Should_I_Trust_You...`, shared across the `.pdf`, `.md`,
  and summary outputs (`.short.md`, `.structured.md`, `.up_to_l<N>.md`, or
  `.all.md`)
- Converts the PDF to Markdown and summarizes it
  - The summary uses the default LLM model, an OpenRouter one: use `--model` to
    change it (see "LLM Model")
  - `--summary_type short` (default) writes 7-10 bullet points with no structure,
    to `<base>.short.md`
  - `--summary_type structured` writes a level-1 header for each main section of the
    paper, with bullet points under it, to `<base>.structured.md`
    - The sections are inferred from the content, since the headers of a markdown
      converted from a PDF are unreliable
  - `--summary_type up_to_l1` is the same as `structured`: it is saved to
    `<base>.structured.md`
  - `--summary_type up_to_l2` and `up_to_l3` keep the headers of the paper up to
    level 2 or 3, with bullet points under each header, and write them to
    `<base>.up_to_l2.md` and `<base>.up_to_l3.md`
  - `--summary_type all` writes `short` and `structured` to the single file
    `<base>.all.md`, a `// Short` section followed by a `// Structured` section,
    with one LLM call per type
  - A run always generates a single summary file (and its `.stat.json` file),
    whatever the `--summary_type`
- For a DOI, queries CrossRef for the metadata and Unpaywall for an open-access PDF
  - Unpaywall requires a real contact email, passed with `--email`
  - Without `--email`, the Unpaywall lookup is skipped: the paper can still be named
    from CrossRef, but there is no PDF to download
  - Only a direct PDF link (`url_for_pdf`) is used: a landing page, e.g., an SSRN
    abstract page, is not a PDF and is ignored
  - If no direct PDF link is found, download the PDF manually and pass it as a local
    file
- For a local PDF, the `download` action copies the file to the standardized path
  (it does nothing if the PDF is already there)
  - The base name comes from the metadata embedded in the PDF
  - If the PDF has no embedded title, the file name is used instead
  - Use `--output` to set the base name explicitly
- For an SSRN paper (abstract URL, delivery URL, or DOI `10.2139/ssrn.<id>`), the PDF
  is downloaded through a real Chrome with `download_with_chrome.py`, since SSRN
  blocks scripted clients (HTTP `403`)
  - The paper is named from CrossRef, which can differ from the title of the latest
    PDF version
  - Chrome is started if it is not running, and closed after the download: a Chrome
    that was already running is left open
  - If a check needs a person (e.g., a CAPTCHA), complete it in the Chrome window
- The opt-in `save_to_papers_dir` action copies the PDF and the summary of the paper
  to the papers dir (`--papers_dir`, default `/Users/saggese/src/notes1/papers`)
  - Enable it with `--action save_to_papers_dir`: it runs after `summarize`
  - The converted markdown `<base>.md` is not copied
  - Only the PDF is required: a summary that does not exist (e.g., `.all.md` without
    `--summary_type all`, or any summary if `summarize` was skipped) is not copied
  - The PDF is always copied, replacing an old PDF in the papers dir
  - The margins of the PDF in the papers dir are cropped with `pdfCropMargins -p 0`
    (a tight bounding box of the content of each page), as `pdfCropMargins -mo -p 0`
    does, but without leaving a `<name>_uncropped.pdf` backup
    - It is on by default: turn it off with `--no_crop_pdf`
    - The PDF in the output dir is left uncropped
    - `pdfCropMargins` is installed by `uv run` through the inline dependencies of
      the script
  - The existing summaries in the papers dir are skipped (they can have been edited
    there) unless `--no_incremental` is passed
  - Figures extracted with `--extract_figures` are not copied

#### Examples
- Download from an arXiv URL (runs download, convert, summarize by default):
  ```bash
  > download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762"
  ```

- Download from a DOI URL or bare DOI, looking up an open-access PDF with Unpaywall:
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --email me@example.org
  ```

- Download an SSRN paper through Chrome, then convert and summarize it:
  ```bash
  > download_academic_paper_to_md.py \
      --input "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
  ```

- Use a PDF already saved locally, e.g., saved from a browser: copy it under the standardized
  name, convert it, and summarize it:
  ```bash
  > download_academic_paper_to_md.py --input ~/Downloads/ssrn_5277078.pdf
  ```

- Use a local PDF with an explicit base name (produces `mypaper.pdf`, `mypaper.md`,
  `mypaper.short.md`):
  ```bash
  > download_academic_paper_to_md.py \
      --input ~/Downloads/ssrn_5277078.pdf \
      --output ./my_papers/mypaper
  ```

- Save under a custom directory when `--output` is not passed:
  ```bash
  > PAPERS_DIR=./my_papers download_academic_paper_to_md.py \
      --input "https://arxiv.org/abs/1706.03762"
  ```

- Summarize keeping the structure of the paper (level-1 headers with bullet points):
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --summary_type structured
  ```

- Keep the headers of the paper up to level 2 (`up_to_l1` is `structured`), saved to
  `<base>.up_to_l2.md`:
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --summary_type up_to_l2
  ```

- Generate both the short and the structured summary in the single file
  `mypaper.all.md`, with a `// Short` and a `// Structured` section:
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --output ./my_papers/mypaper \
      --summary_type all
  ```

- Only download and convert, skip summarization:
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --skip_action summarize
  ```

- Summarize with a specific model:
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --model openrouter/anthropic/claude-haiku-4.5
  ```

- Only summarize an already converted paper (e.g., after a failed LLM call):
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --clear_actions \
      --action summarize
  ```

- Also copy the PDF (cropped margins) and the summary to the papers dir, without
  the converted markdown:
  ```bash
  > download_academic_paper_to_md.py \
      --input "https://arxiv.org/abs/1706.03762" \
      --action save_to_papers_dir
  ```

- Copy the PDF and the summary to a custom papers dir:
  ```bash
  > download_academic_paper_to_md.py \
      --input "https://arxiv.org/abs/1706.03762" \
      --action save_to_papers_dir \
      --papers_dir ./my_papers
  ```

- Copy the PDF to the papers dir without cropping its margins:
  ```bash
  > download_academic_paper_to_md.py \
      --input "https://arxiv.org/abs/1706.03762" \
      --action save_to_papers_dir \
      --no_crop_pdf
  ```

- Show what would be done without downloading, converting, or summarizing:
  ```bash
  > download_academic_paper_to_md.py --input "10.1038/nature12373" --dry_run
  ```

### `download_hn_article_to_md.py`

#### What It Does
- Downloads a Hacker News link: both the comments and the article it points to
- Converts and summarizes both
- Output filenames share a base name (the sanitized submission title, unless
  `--output` is given)

#### Examples
- Download, convert, and summarize an HN submission:
  ```bash
  > download_hn_article_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490"
  ```

- Only download the article and comments, skip summarization:
  ```bash
  > download_hn_article_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --action download_hn_url \
      --action download_article_url
  ```

- Overwrite existing output files:
  ```bash
  > download_hn_article_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --no_incremental
  ```

### `download_html_to_md.py`

#### What It Does
- Downloads an HTML page (or reads a local HTML file) and converts it to Markdown
  using one of several converters: `auto` (BeautifulSoup, falling back to
  readability), `pandoc`, `bs`, or `readability`
- Summarizes the converted content
- Retries with a headless browser when the plain request is rejected (HTTP error)
- Fails with an error, and saves nothing, when the downloaded page is a
  bot-protection page (e.g., "Just a moment...") instead of the content
  - Some sites also block the headless browser (e.g., SSRN): use
    `download_with_chrome.py` for them

#### Examples
- Download a page and convert with the default `auto` converter:
  ```bash
  > download_html_to_md.py --input https://example.com --output output.md
  ```

- Convert with a specific converter:
  ```bash
  > download_html_to_md.py \
      --input https://example.com \
      --output output.md \
      --converter pandoc
  ```

- Skip the summarization step:
  ```bash
  > download_html_to_md.py \
      --input https://example.com \
      --output output.md \
      --skip_action summarize
  ```

### `download_with_chrome.py`

#### What It Does
- Downloads a URL with a real Chrome browser attached through the Chrome DevTools
  Protocol (CDP), for sites that block scripted clients, including the headless
  browser of `download_html_to_md.py`
  - The site sees an ordinary Chrome session, with its own profile and cookies
  - A check that needs a person (e.g., a CAPTCHA) is completed in the Chrome window,
    while the script waits (`--timeout_sec`)
- `--mode html` saves the rendered HTML of a page
- `--mode file` saves a file (e.g., a PDF): the referer page is opened first, then
  the file is fetched from inside that page, with the cookies of the site
- For an SSRN abstract URL, delivery URL, or DOI (`10.2139/ssrn.<id>`), the referer
  and the PDF URL are derived automatically
- Uses a Chrome with remote debugging on `--cdp_url` (default
  `http://127.0.0.1:9222`)
  - `--launch_chrome` starts one if none is listening, with a dedicated profile
    (`--chrome_profile_dir`, default `~/.cache/chrome_cdp_profile`) that keeps the
    cookies between runs
  - A Chrome started by `--launch_chrome` is closed when the download succeeds
    (pass `--keep_chrome` to keep it open, e.g., to reuse it in the next run)
  - A Chrome that was already running is never closed
  - On a failure the Chrome window is left open, to see what the page shows
- Saves nothing and fails if the result is still a bot-protection page, or if a
  `.pdf` output is not a PDF

#### Examples
- Download the PDF of an SSRN paper, starting Chrome if it is not running:
  ```bash
  > download_with_chrome.py \
      --launch_chrome \
      --mode file \
      --input "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078" \
      --output ssrn_5277078.pdf
  ```

- Download the PDF from the DOI, with a Chrome already running with
  `--remote-debugging-port=9222`:
  ```bash
  > download_with_chrome.py \
      --mode file \
      --input "10.2139/ssrn.5277078" \
      --output ssrn_5277078.pdf
  ```

- Download a file from any site, opening a referer page first:
  ```bash
  > download_with_chrome.py \
      --mode file \
      --input "https://example.com/files/paper.pdf" \
      --referer "https://example.com/paper" \
      --output paper.pdf
  ```

- Save the rendered HTML of a page:
  ```bash
  > download_with_chrome.py \
      --launch_chrome \
      --input "https://example.com/page" \
      --output page.html
  ```

- Keep the Chrome started by the script open after the download:
  ```bash
  > download_with_chrome.py \
      --launch_chrome \
      --keep_chrome \
      --input "https://example.com/page" \
      --output page.html
  ```

- Show what would be done without starting Chrome or downloading:
  ```bash
  > download_with_chrome.py \
      --mode file \
      --input "10.2139/ssrn.5277078" \
      --output ssrn_5277078.pdf \
      --dry_run
  ```

### `podcast_dl.py`

#### What It Does
- Downloads and formats a podcast transcript from `lexfridman`, `dwarkesh`,
  `podcasttranscript_ai`, or `podscripts_co`
- Default behavior runs `download`, `format`, and `lint` in sequence
- Each step writes a numbered file to `<OUTPUT>.md.tmp/`, and the final result is
  copied to `<OUTPUT>.md`

#### Examples
- Default: download, format, and lint a Lex Fridman episode:
  ```bash
  > podcast_dl.py \
      --type lexfridman \
      --title lars-brownworth \
      --output ./podcasts/lars-brownworth.md
  ```

- Download only:
  ```bash
  > podcast_dl.py \
      -a download \
      --type lexfridman \
      --title lars-brownworth \
      --output ./podcasts/lars-brownworth.md
  ```

- Download and format (skip linting):
  ```bash
  > podcast_dl.py \
      -a download -a format \
      --type dwarkesh \
      --title andrej-karpathy \
      --output ./podcasts/andrej-karpathy.md
  ```

- Run the example script covering all source types:
  ```bash
  > ./podcast_dl_example.sh
  ```

### `update_bookmarks_from_raindrop.py`

#### What It Does
- Synchronizes new bookmarks from `Raindrop.io` into either a live Google
  Sheet or a local CSV file, selected via the required `--target
  {gsheet,local_csv}` (no default)
- Requires the `RAINDROP_API_TOKEN` environment variable
- **`--target gsheet`**: a four-action pipeline
  - **download_gsheet_links**: Downloads current data from Google Sheets to CSV
  - **download_raindrop_data**: Fetches new bookmarks from the `Raindrop.io` API
    (only items created after the latest timestamp in the gsheet)
  - **combine_data**: Transforms and combines `Raindrop.io` data into the gsheet
    schema, writing a new combined tmp CSV
  - **upload_gsheet_links**: Uploads combined data back to Google Sheets in a new
    timestamped tab
- **`--target local_csv`** (requires `--local_csv <path>`): only
  `download_raindrop_data` and `combine_data` apply (no gsheet
  download/upload: `download_gsheet_links`/`upload_gsheet_links`); the
  latest-`Timestamp` cutoff is read directly from `--local_csv`, and `combine_data`
  prepends newly-fetched rows into that same file in place, leaving every existing
  row (`Done` included) untouched
- `--dry_run` logs what each selected action would do, with its input and output
  files, and runs nothing: no `Raindrop.io` call, no file or gsheet change, and no
  `RAINDROP_API_TOKEN` needed

#### Examples
- Sync all new bookmarks from `Raindrop.io` to Google Sheets:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --all_actions
  ```

- Just download from Google Sheets:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_gsheet_links
  ```

- Just fetch from `Raindrop.io` (requires `RAINDROP_API_TOKEN`):
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_raindrop_data
  ```

- Combine data without uploading:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_gsheet_links \
      --action download_raindrop_data \
      --action combine_data
  ```

- Sync new bookmarks directly into a local CSV instead of a Google Sheet:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target local_csv \
      --local_csv /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
      --action download_raindrop_data --action combine_data
  ```

- Show what each selected action would do, without calling `Raindrop.io` or changing
  any file or gsheet:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target local_csv --local_csv bookmarks.csv \
      --all_actions --dry_run
  ```

### `pre_process_bookmarks.py`

#### What It Does
- Pipeline for enriching Hacker News articles, applied the same way to a
  Google Sheets document or a local CSV, selected via the required `--target
  {gsheet,local_csv}` (no default)
- **`--target gsheet`**: a five-action pipeline
  - **download_link_gsheet**: Downloads data from Google Sheets to CSV
  - **update_article_url**: Extracts article URLs from HN links via the HN API
  - **update_article_tag**: Classifies articles by topic using an LLM
  - **update_article_cluster**: Maps topics to higher-level cluster categories
  - **upload_link_gsheet**: Uploads the processed CSV back to Google Sheets
- **`--target local_csv`** (requires `--local_csv <path>`): only
  `update_article_url`, `update_article_tag`, and `update_article_cluster`
  apply (no gsheet download/upload); rows are read directly from
  `--local_csv`, and the final clustered result is written back into that
  same file in place
- Only processes rows with empty target columns (incremental, resumable)
- `--dry_run` logs what each selected action would do, with its input and output
  files, and runs nothing: no HN API call, no LLM call, and no file or gsheet change

#### Examples
- Run the complete pipeline on a Google Sheets document:
  ```bash
  > pre_process_bookmarks.py --target gsheet --url "$LINKS_GSHEET" --all_actions
  ```

- Just download data from Google Sheets:
  ```bash
  > pre_process_bookmarks.py \
      --target gsheet --url "$LINKS_GSHEET" \
      --action download_link_gsheet
  ```

- Extract article URLs only:
  ```bash
  > pre_process_bookmarks.py \
      --target gsheet --url "$LINKS_GSHEET" \
      --action update_article_url
  ```

- Tag articles using a specific LLM model:
  ```bash
  > pre_process_bookmarks.py \
      --target gsheet --url "$LINKS_GSHEET" \
      --action update_article_tag \
      --model openrouter/anthropic/claude-haiku-4.5
  ```

- Run the same enrichment pipeline directly against a local CSV instead of a
  Google Sheet, updating it in place:
  ```bash
  > pre_process_bookmarks.py \
      --target local_csv --local_csv bookmarks.csv \
      --all_actions
  ```

- Show what each action would do, without calling the HN API or an LLM and without
  changing any file or gsheet:
  ```bash
  > pre_process_bookmarks.py \
      --target local_csv --local_csv bookmarks.csv \
      --all_actions --dry_run
  ```

### `download_link_articles.py`

#### What It Does
- Downloads article content and HN comments; `--input` is the primary,
  gsheet-free way to run it, accepting either a single HN submission/article
  URL (bypassing Google Sheets, type auto-detected) or a path to a local
  bookmarks CSV (batch mode, all its rows); `--url` remains available for a
  live Google Sheets document
- Saves downloaded content to text files with bash-safe filenames derived from the
  `Title` column
- Actions: **download_hn_url**, **download_article_url**, **summarize_hn_url**,
  **summarize_article_url**

#### Examples
- Download a single HN submission directly, bypassing Google Sheets:
  ```bash
  > download_link_articles.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --all_actions
  ```

- Download and summarize all rows from a local bookmarks CSV:
  ```bash
  > download_link_articles.py --input bookmarks.csv --all_actions
  ```

- Download HN comments for rows 0-10 of a local bookmarks CSV where `Hn_url`
  is not empty:
  ```bash
  > download_link_articles.py \
      --input bookmarks.csv \
      --row_idx "0:10" \
      --action download_hn_url
  ```

- Download all (HN comments and article) for the first row of a Gsheet:
  ```bash
  > download_link_articles.py --url "$LINKS_GSHEET" --row_idx 1 --all_actions
  ```

- Summarize articles for all rows of a Gsheet:
  ```bash
  > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_article_url
  ```

### `process_bookmarks.py`

#### What It Does
- Processes unprocessed rows (no `Done` flag) from a local bookmarks CSV (columns:
  `Title`, `Article_url`, `Hn_url`, `Timestamp`, `Article_tag`, `Article_cluster`,
  `Done`), up to `--limit` rows
- For each row:
  1. Calls `download_hn_article_to_md.py` to download and summarize the submission
     (article + HN comments) under `--output_dir`
  2. Merges the article summary and HN comments summary into a single
     `<date>.hn_<item_id>.<title>.summary.md` file, with an `# Info` section
     (`Title`, `Article`, `HN`, `Timestamp`, `Article_tag`, `Article_cluster`, an
     empty manual `Score: ` placeholder) followed by `# Article Summary` (12-15
     bullet points) and `# HN Comments Summary` (10-15 comments) sections
  3. Sets `Done=yes` on the row and saves the CSV in place, so an interrupted run
     can resume
  - A row whose `Hn_url` isn't a real HN item URL (e.g., a plain article link
    `Raindrop.io` put in that column) is set to `Done=skipped` immediately
    instead, with no download, so it stops occupying `--limit` slots on every
    future run
- Always reads and writes a local CSV directly, unlike `pre_process_bookmarks.py`
  and `download_link_articles.py`, for which a local CSV is one of two supported
  data sources (selected via `--target`/`--input`, alongside a live Google Sheet)
- **Destination reconciliation**: separately from row processing, every invocation
  copies the cached merged summary for every `Done=yes` row that's missing from the
  selected destination (`--dest_type {gdrive,obsidian,none}`, default `gdrive`;
  `--dest_dir <path>` overrides the built-in path) -- no re-download, no
  re-summarize. This runs over *all* `Done=yes` rows, not bounded by `--limit`
  (`--limit 0` runs reconciliation only), and is what makes destinations
  independent: switching `--dest_type` later backfills the new one for free
  - Every invocation also always backs up merged summaries into a fixed,
    git-tracked dir, independent of `--dest_type` (a version-controlled copy,
    separate from the user-selectable viewing destination)
- `--dry_run` reports, without downloading, writing, or mutating the CSV: rows to be
  newly processed, rows to be marked `skipped`, and rows to be copied/repaired into
  the selected destination

#### Examples
- Process up to 10 unprocessed rows (default), copying to Google Drive:
  ```bash
  > process_bookmarks.py \
      -i /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
      --limit 10
  ```

- Preview what would be done without downloading or writing anything:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --dry_run
  ```

- Reprocess rows even if already marked `Done`, overwriting existing local output
  files:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --no_incremental
  ```

- Copy merged summaries to the Obsidian vault instead of Google Drive:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --dest_type obsidian
  ```

- Keep the merged summaries local (under `--output_dir`) only:
  ```bash
  > process_bookmarks.py \
      --input bookmarks.csv \
      -o ./tmp.hn_downloads \
      --dest_type none
  ```

- Backfill a destination for rows already processed, without downloading anything
  new:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --dest_type obsidian --limit 0
  ```

### `sync_bookmarks.py`

#### What It Does
- Runs the whole CSV-based bookmark flow with a single command, by chaining the
  scripts above on a local bookmarks CSV (`--csv`, default
  `/Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv`)
- It has one action per phase, always executed in this order:
  - **update_raindrop**: adds the new `Raindrop.io` bookmarks to the CSV, with
    `update_bookmarks_from_raindrop.py --target local_csv`
    - Needs `RAINDROP_API_TOKEN`
  - **tag**: fills `Article_url`, `Article_tag`, and `Article_cluster` where they are
    empty, with `pre_process_bookmarks.py --target local_csv`
    - Costs LLM money. Needs `OPENROUTER_KEY`
  - **report**: shows the situation of the CSV vs the destination (rows to process,
    to skip, to copy), with `process_bookmarks.py --dry_run`
    - Changes nothing
  - **process**: downloads and summarizes the next `--limit` unprocessed rows (article
    and HN comments), marks them `Done`, and copies every merged summary missing
    from the destination, with `process_bookmarks.py`
    - Costs LLM money. Needs `OPENROUTER_KEY`
- The default actions are `update_raindrop`, `tag`, and `process`. `report` is
  opt-in
- The destination is the iCloud vault of Obsidian (`--dest_type obsidian`)
  - `process_bookmarks.py` always backs up the summaries to its git dir too
  - Use `--dest_type gdrive` or `--dest_dir` for another destination
- Checks the tokens before running any action, and stops at the first failing phase
- At the end, logs how the CSV changed (rows, untagged, done, skipped, to do)
- It can be re-run at any time, since every phase is incremental
- Each phase starts with a framed header
- With `--dry_run`, the command of every selected phase is printed and none is run, so
  no token is needed and there is no Raindrop.io or LLM call
  - To see the situation of the CSV vs the destination, use the `report` action
- The raw downloaded files are cached in `--output_dir`, by default the dir of
  `process_bookmarks.py`, which is relative to the current dir
  - Run from the same dir every time, or pass `--output_dir`
- Rows without an HN URL are marked `Done=skipped` by `process_bookmarks.py`: bookmarks
  of plain articles are not processed yet

#### Examples
- Run the whole flow, processing the next 10 rows:
  ```bash
  > sync_bookmarks.py
  ```

- Show the situation of the CSV vs iCloud, without changing anything:
  ```bash
  > sync_bookmarks.py --clear_actions --action report
  ```

- Print the commands of the whole flow, without running them:
  ```bash
  > sync_bookmarks.py --dry_run
  ```

- Process the next 50 rows:
  ```bash
  > sync_bookmarks.py --limit 50
  ```

- Skip the update from Raindrop and the tagging, and only process the rows:
  ```bash
  > sync_bookmarks.py --clear_actions --action process
  ```

- Only copy the rows already processed to iCloud, without downloading anything:
  ```bash
  > sync_bookmarks.py --clear_actions --action process --limit 0
  ```

- Use another CSV and another LLM model:
  ```bash
  > sync_bookmarks.py \
      --csv bookmarks.csv \
      --model openrouter/anthropic/claude-haiku-4.5
  ```

### `process_one_off_gsheet_links.py`

#### What It Does
- One-off migration pipeline that renames old topic tags to their simplified names in
  the Gsheet
- Steps: download from Google Sheets, replace tags in the local CSV, upload the
  result back

#### Examples
- Run the complete tag-renaming pipeline:
  ```bash
  > process_one_off_gsheet_links.py --url "$LINKS_GSHEET"
  ```

## Description of Workflows

### Paper From a Site That Blocks Scripts (e.g., SSRN)
- **Purpose**: get the Markdown and the summary of a paper that cannot be downloaded
  by a plain script or by a headless browser

- **Steps**:
  1. Run the pipeline on the SSRN URL (or DOI), which downloads the PDF through a
     real Chrome, converts it, and summarizes it:
     ```bash
     > download_academic_paper_to_md.py \
         --input "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
     ```
  2. Find `<base>.pdf`, `<base>.md`, and `<base>.short.md` under `$PAPERS_DIR` (or
     the current directory)

- **Notes**:
  - A Chrome window opens during the download and closes by itself when it is done
  - If the site shows a check that needs a person, complete it in that window: the
    script continues by itself
  - The CrossRef title of an SSRN paper can differ from the title of its latest
    PDF version, so check the name chosen for the files
  - To download only the PDF, run `download_with_chrome.py` (see above), then pass the
    file to `download_academic_paper_to_md.py --input`
  - If the Chrome download does not work, save the PDF from your browser and pass it
    as a local file with `--input`; use `--output` to choose the base name, since many
    SSRN PDFs have no embedded title

### Single-Command CSV Bookmark Workflow

- **Purpose**: pull the latest `Raindrop.io` links, update the CSV, download and
  summarize the articles and the HN comments, and copy the summaries to iCloud so
  that Obsidian can read them, with a single command
- **Steps**:
  1. Optionally, see the situation of the CSV vs iCloud:
     ```bash
     > sync_bookmarks.py --clear_actions --action report
     ```
  2. Run the flow. It processes the next 10 rows, and it costs LLM money:
     ```bash
     > sync_bookmarks.py
     ```
  3. Open Obsidian. iCloud syncs the new `<date>.hn_<id>.<title>.summary.md` files
     by itself
- **Notes**:
  - It chains `update_bookmarks_from_raindrop.py`, `pre_process_bookmarks.py`, and
    `process_bookmarks.py` (see `sync_bookmarks.py` above): the stages of the
    CSV-Based Bookmark Processing Workflow below, preceded by the Raindrop update
  - Rerun it any time. Raise `--limit` to work through the backlog faster

### CSV-Based Bookmark Processing Workflow

- **Purpose**: run the enrichment, download, and summarization stages one at a
  time, tracked in a local CSV (e.g., the `combined_data.csv` produced by
  `update_bookmarks_from_raindrop.py`'s `combine_data` action)
- **Steps**:
  1. Extract article URLs and classify by topic/cluster, updating the CSV in
     place:
     ```bash
     > pre_process_bookmarks.py \
         --target local_csv --local_csv bookmarks.csv \
         --all_actions
     ```
  2. Download HN comments and article content, summarize them using an LLM, merge
     the summaries into per-item files, and mark rows `Done`:
     ```bash
     > process_bookmarks.py -i bookmarks.csv --limit 3
     ```
- `download_link_articles.py` is not needed in this workflow: `process_bookmarks.py`
  downloads and summarizes each row itself, through `download_hn_article_to_md.py`
- See `process_bookmarks.py`'s own module docstring for the full row-processing,
  skip, and destination-reconciliation flow, and `download_hn_article_to_md.py`'s
  docstring for the per-item output filename convention (`<base>.1.article_url.md`,
  `<base>.2.article_url.summary.md`, etc.)
- **Notes**:
  - Rerunning `process_bookmarks.py` later only processes the next unprocessed rows
    (`Done` still unset), since the CSV is updated in place after each row
  - Use `--dry_run` first to see which rows would be picked up without downloading or
    writing anything
  - Use `--no_incremental` to force re-download and re-summarize rows already marked
    `Done`

### Gsheet-Based Link-Processing Workflow
- **Purpose**: Ingest new bookmarks, classify them, and archive their content and
  summaries, tracked in a live Google Sheet
  - Use it only if the links live in a Google Sheet: the CSV workflows above are
    the main flow

- **Steps**:
  1. Download links from `Raindrop.io` and merge with the existing gsheet:
     ```bash
     > update_bookmarks_from_raindrop.py --target gsheet --url "$LINKS_GSHEET" --all_actions
     ```
  2. Extract article URLs and classify by topic/cluster:
     ```bash
     > pre_process_bookmarks.py --target gsheet --url "$LINKS_GSHEET" --all_actions
     ```
  3. Download HN comments and article content:
     ```bash
     > download_link_articles.py --url "$LINKS_GSHEET" --all_actions
     ```
  4. Summarize articles and HN comments using an LLM:
     ```bash
     > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_article_url
     > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_hn_url
     ```
  5. Review the results in the new timestamped tabs in Google Sheets and the
     downloaded files (articles, comments, summaries) in the local directory

### Data Sources and Destinations of the Bookmark Scripts
- `update_bookmarks_from_raindrop.py` and `pre_process_bookmarks.py` select their
  data source with `--target {gsheet,local_csv}` (required, no default)
  - `--target local_csv` (requires `--local_csv <path>`) works on the CSV in place,
    with no gsheet download/upload actions
  - `--target gsheet` works on a live Google Sheet, with `--url`
- `process_bookmarks.py` always reads the CSV and selects where the merged summaries
  are copied with `--dest_type {gdrive,obsidian,none}` (default: `gdrive`), with
  `--dest_dir <path>` to override the built-in path
- A fixed git-tracked dir is always backed up into, whatever `--dest_type`
- The 3 scripts share their core logic across modes and destinations. Only the small
  input/output-path logic differs
- Any of the 3 scripts can be run at any time, independently of the others
- See the per-script sections above for the actions, the options, and the examples

- **Notes**:
  - Same incremental/resume behavior as the CSV-Based Bookmark Processing Workflow
    above: rerun any time, only the outstanding batch is processed
  - `--dest_type gdrive` and `--dest_type obsidian` can both be run against the
    same CSV over time, since the destination reconciliation backfills the new one
    from the local cache with no re-download and no LLM cost
