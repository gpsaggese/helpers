---
description: Format markdown cells corresponding to interactive cells in a Jupyter notebook
model: haiku
---

# Goal
- Given a Jupyter notebook, format the markdown cells that correspond to interactive
  or visualization cells
- Each visualization uses a triplet: pre-visualization markdown, the code cell, and
  post-visualization markdown

# Workflow

## Update the Cell Triplets
- Make the markdown cells around each interactive cell follow the triplet structure:
  - **Before the visualization**: a markdown cell with the goal, then a description
    cell with the plot descriptions (under each title) and widget descriptions
    (close to each widget)
  - **After the visualization**: a guided-usage markdown cell that explains which
    experiments to run and what was learned, then the implementation cell and the
    `print_obj_info()` code cell

## Sync with Jupytext
- At the end, sync the paired `.py` file with Jupytext, following
  `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Conventions
- Follow the rules in `.claude/skills/notebook.rules.md`, especially:
  - `## Visualization Cell Triplet Details` for the structure of pre- and
    post-visualization markdown cells
  - `# Visualization and Interactivity` for the interactive widget patterns
  - `## Cell Triplet Structure` for the overall three-cell organization

# Constraints
- Do not change the intent of the notebook

# Verification
- [ ] Confirm each interactive cell has both a pre- and post-visualization
      markdown cell
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
