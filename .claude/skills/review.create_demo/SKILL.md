---
description: Write code_demo.md, a short demo of a tool: what to run and what it generates
model: sonnet
---

# Goal

- Given a dir that holds a tool, write `code_demo.md` in that dir
- The file has four parts:
  - What the tool does, in a few lines
  - **What to run**: the command, its needs, its cost, and how long it takes
  - **What is generated**: each output file, what it holds, and the stage that
    writes it
  - What a past run gave, and how to check the output
- Keep it short: a reader must run the demo after reading it for 5 mins
- It is the source of the end-to-end demo in `code_tour.md`. The skill
  `.claude/skills/review.create_code_tour/SKILL.md` points to this file and does not
  repeat it

# Conventions

- Follow the template `.claude/templates/review_create_demo.template.md`
- Follow `.claude/skills/text.rules.md` and `.claude/skills/markdown.rules.md`
- Name each file in backticks, with its path from the repo root
- Put each command in a fenced `bash` block, with `>` before the command
- Take facts from the dir's README and from the files a run leaves. If a fact is
  not clear, write `unknown` and do not guess

# Workflow

## Get the Input

- Take the dir from the arguments. If none is given, use the current dir
  - If the dir does not exist, report the error and stop
- Write `code_demo.md` in the dir. The name is fixed, so it does not follow
  `## Generated File Naming` of `.claude/skills/skill.rules.md`
  - If the file exists, read it, then overwrite it
- Take the dir's `README.md`
  - If it does not exist, report the error and stop. Tell the user to run
    `.claude/skills/readme_dir.create/SKILL.md` on the dir first

## Find the Demo

- Find the runner: the executable that runs all stages, or the only executable
  - Take its path, flags, and example commands from the README of the dir and of the
    script
  - Check the flags with `--help`
- Find the small example input: the smallest input file that the README or the tests
  use, e.g., `paper_list.short.csv`
  - Skim the whole file, so the text says what the rows are
- Choose the output dir: take it from the README if it gives one. Else use
  `./run_demo`, a dir in the current dir
- Find the setup the command needs, e.g., `PYTHONPATH`, an API key, or Docker. Take
  it from the README of the dir
- Find what the demo needs and costs
  - Name the needs: internet, an LLM, a browser, an API key
  - Say that the demo costs LLM calls when it calls an LLM
  - Do not run a command that costs money. Ask the user to run it
- If the runner has `--dry_run`, run it. Check that it needs no internet, no LLM,
  and no browser

## Find What Is Generated

- Take the output file list from the README of the dir, e.g., from the section
  "Output Dir"
- If the demo's output dir exists, list it and compare it with the README:
  ```bash
  > find <OUTPUT_DIR> -maxdepth 3 | sort
  ```
  - Keep only the files the demo makes
  - Open and add any file in the output dir that the README does not list
  - If a README file is missing from the output dir, say it is made only in some
    cases, and when
- For each file or group, write:
  - The name, with `<BASE>` or `NN` as in the README
  - What it holds, in one short line. Open the file if the README is not clear
  - The stage that writes it
- Cover the results, the issues, the summaries, and the cache and logs
- If the output dir exists, take the past-run counts from the summary files
  - For each stage, take the items processed, completed, failed, and the issues
  - Take one or two values from a result file, e.g., a rating

## Write the File

- Fill the template in this order:
  - `# What the Tool Does`: purpose, input, and output, in 3 bullets
  - `# Run the Demo`: needs, cost, time, the command, and the dry run
  - `# What Is Generated`: the tree of the output dir, and the table of files
  - `# Example Result`: the past-run counts, one row per stage
  - `# Check the Output`: the checks a reader can fail
- Use the table columns `File`, `Written by`, and `Content`
- Write the example result only when an output dir exists
  - Say it is the result of a past run
  - Say the numbers can change with the internet and the LLM, but the files do not
- In `# Check the Output`, write these checks when they apply:
  - Each summary file shows the counts of its stage
  - Each failed item is in the issues file of the same stage
  - A value of the report equals the value in one item's file
  - A second run of the same command skips the finished work
- Do not add a diagram. The file is short text

## Report

- Print the file path, the demo command, what it needs, and what it costs
- Print the list of files the demo makes
- Do not commit the file

# Constraints

- Do not modify any file of the dir except `code_demo.md`. Delete the `*.log` files
  that a run created
- Do not run a command that needs internet, an LLM, or a browser without the user
- Do not invent a command, a flag, a file, or a number
- Use `:` and not `-` to separate a file from its description
- Do not use emojis or the em-dash

# Examples

- Run on the dir `research/Estimate_academic_paper_quality`
  - The runner is `estimate_paper_quality.py`, and the input is
    `paper_list.short.csv`
  - The command writes to `./run_demo`. It needs internet, a browser for SSRN
    papers, and an LLM
  - One file per stage, e.g., `01-resolve.paper_list.json`, and one summary per
    stage, e.g., `02-download.summary.txt`
  - A past run: 5 of 5 papers resolved, 3 of 5 downloaded, and 3 papers rated

# Verification

- [ ] The output file is `code_demo.md` in the dir
- [ ] The five template parts are present, in order
- [ ] The command, flags, and input file exist, and the flags appear in `--help`
- [ ] The file says what the demo needs, costs, and how long it takes
- [ ] The paths in the file are from the repo root
- [ ] Every file the demo makes is in the table, with its content and stage
- [ ] The example result comes from a past run's summary files, and says so
- [ ] The file has no diagram and no invented command
- [ ] No line is over 85 characters outside code blocks and tables
- [ ] No file of the dir changed, other than `code_demo.md`
