---
description: Move or add notebook code to a *_utils.py library file
model: haiku
---

# Goal
- You are an expert Python developer

- I will pass you a Python file paired with a Jupyter notebook using jupytext
  in `py:percent` format

# Constraints
- Follow `.claude/skills/coding.rules.md` for all code

- Important Notes
  - Always sync before editing: `uvx jupytext --sync notebook.py`
  - Always sync after editing: `uvx jupytext --sync notebook.py`

# Scenarios
- This skill handles two complementary scenarios:

## Scenario 1: Moving Existing Functions to Utils
- Extract functions from an existing notebook and move them to utils

## Scenario 2: Adding New Code to Utils
- Add new functions or code to the utils file that corresponds to the notebook

# Workflow

## Identify or Create the Utils File
- Find or create the library file for the notebook, named after it with underscores
  - E.g., `Lesson94-Information_Theory.ipynb` ->
    `Lesson94_Information_Theory_utils.py`
  - E.g., `tutorial_advanced.ipynb` -> `tutorial_advanced_utils.py`

## Organize Code Structure in Utils File
- Mirror the notebook's flow, with section separators for each notebook section
  - Example:
    ```python
    # #############################################################################
    # Cell 1: Visual Bin - Population of Marbles
    # #############################################################################

    def cell1_draw_bin_with_marbles_interactive(...):
        ...

    def _cell1_helper_function(...):
        ...

    # #############################################################################
    # Cell 2: Entropy Calculations
    # #############################################################################

    def cell2_calculate_entropy(...):
        ...
    ```

- Put each function in the part of the utils file that matches its notebook section
- Group related functions together
- Use private functions (prefix `_`) for helpers not called from the notebook

## Move or Add Functions

### For Moving Functions (Scenario 1):

- Follow these steps:

  1. Copy all functions from the notebook to the utils file, without changing code
  2. Remove the functions from the notebook
  3. Update the notebook cells to call the utils functions

### For Adding Functions (Scenario 2):

- Follow these steps:

  1. Implement new code directly in the utils file
  2. Create caller code in the notebook that imports and uses the functions
  3. Add the code in the matching section of the utils file

## Update Notebook to Call Utils
- Replace function implementations with imports and calls
- Pattern:
  ```python
  import notebook_name_utils as utils

  # In code cells:
  utils.function_name(...)
  ```

- Keep each code cell minimal:
  ```python
  # Display results of Cell 2 analysis.
  utils.cell2_calculate_entropy()
  ```

## Code Reuse
- Reuse code already in the `*_utils.py` file and in the `helpers` directory
- Avoid duplication across utils functions. Extract common patterns into helpers

## Sync with Jupytext
- After all modifications, sync both files, following `# Code Architecture and
  Responsibility` -> `## Utilities vs. Notebook Responsibilities` in
  `.claude/skills/notebook.rules.md`:
  ```bash
  > uvx jupytext --sync <path/to/notebook.py>
  ```

# Conventions
- Always follow `.claude/skills/notebook.rules.md`

# Verification
- [ ] Confirm no function moved to `*_utils.py` changed behavior
- [ ] Confirm every notebook cell that held inline code now calls its utils function
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
