---
description: Format the markdown cells of a notebook like slides
model: haiku
---

# Goal
- Given an interactive Jupyter notebook, format all the markdown cells without
  changing their content

# Workflow

## Sync Markdown Cells
- Sync every markdown cell with its interactive cell

## Markdown Cells Needs to Use Bullet Lists
- Structure the text in markdown cells as markdown bullet points, with nested
  bullets for clarity and conciseness, following
  - `.claude/skills/slides.rules.md`: slide formatting
  - `.claude/skills/text.rules.md`: bullet point formatting
- Follow `## Use Bullet-Point Comments for Structured Explanations` in
  `.claude/skills/notebook.rules.md`

## Sync Notebook
- Finally, sync the paired `.py` file with Jupytext, per `# Code Architecture and
  Responsibility` -> `## Utilities vs. Notebook Responsibilities` in
  `.claude/skills/notebook.rules.md`

# Conventions
- Always follow `.claude/skills/notebook.rules.md`

# Constraints
- Do not change the intent of the cell

# Verification
- [ ] Confirm the meaning of every markdown cell is unchanged
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
