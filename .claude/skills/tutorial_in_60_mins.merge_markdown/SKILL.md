---
description: Merge the content of a markdown file into a Jupyter notebook
model: haiku
---

You are a technical writer

# Goal
- Given a markdown file `<MD_FILE>` and a Jupyter notebook `<NOTEBOOK_FILE>`, add
  all the content of `<MD_FILE>` to `<NOTEBOOK_FILE>`

# Workflow
- Read `<MD_FILE>`
- Decide where each chunk fits in `<NOTEBOOK_FILE>`, as a markdown cell or as
  comments in a Python cell
- Remove each moved concept from `<MD_FILE>`
- Leave in `<MD_FILE>` the chunks that cannot go into `<NOTEBOOK_FILE>`
- At the end, jupytext sync the notebook and its Python file
