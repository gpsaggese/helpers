---
description: Remove all the dead code in a Jupyter notebook and in the paired utility file
model: haiku
---

# Goal
- Given a Jupyter notebook, remove its dead code and the dead code in the paired
  utility file

# Workflow

## Follow Notebook Conventions
- Read and follow `.claude/skills/notebook.rules.md`

## Find Unused Functions
- Find the functions in the notebook and in the paired `*_utils.py` file that the
  notebook does not use
- Print a summary of the unused functions

## Remove Unused Code
- Remove the unused functions from the notebook and from the paired utility file
- Remove their unit tests, if any

## Sync with Jupytext
- At the end, sync the paired `.py` file with Jupytext, following
  `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Verification
- [ ] Confirm no remaining code references the removed functions
- [ ] Run the notebook top to bottom following `## Testing Notebook` in
  `.claude/skills/notebook.rules.md` and confirm it completes without errors
