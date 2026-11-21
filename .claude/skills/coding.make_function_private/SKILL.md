---
description: Identify private or public functions in a file and rename with underscore
model: haiku
---

# Goal
For each function `<FUNC>` in the passed Python file `<FILE>`, decide if it is
private or public by checking whether Python files or Jupyter notebooks outside
`<FILE>` call it.

# Conventions
- Follow `## Mark Private Functions` in `.claude/skills/coding.rules.md`

# Definitions

## External Files
- **External files** = any Python file or Jupyter notebook outside the target
  file
  - Including:
    - Sibling scripts in the same package (e.g., `notes_to_pdf.py` calling
      functions from `lib_notes_to_pdf.py`)
    - Parent/sibling modules that import from the target
    - CLI entry point scripts
  - Excluding:
    - Test files of the target. A function stays private even if a test calls it

- **Note:** Functions in a library module's public API are PUBLIC, even if no
  `__main__` entry point calls them. Utilities that other scripts in the package
  import are PUBLIC too

# Private Functions
- If `<FUNC>` is not called by any external file, it is private: rename it with a
  `_` prefix
  - E.g., `def function` -> `def _function`
  - Include only internal utilities, helpers, and implementation details
- Update all callers of `<FUNC>` to the new name

- **Good** (only called within its own file, so renamed private)
  ```python
  # lib_helper.py
  def public_function():
      _internal_helper()  # Only called within this file, so private.

  def _internal_helper():
      pass
  ```

# Public Functions
- If `<FUNC>` is called by external files, it is public: its name must not start
  with `_`
  - This includes functions in shared utility modules that sibling scripts call
- Update all callers, external and internal, to the new name

- **Good** (called by an external file, so it stays public)
  ```python
  # lib_notes_to_pdf.py
  def preprocess_notes(file_name, prefix):  # Called by notes_to_pdf.py, so public.
      _internal_step_1(file_name)  # Private helper.

  def _internal_step_1(file_name):  # Only used within lib_notes_to_pdf.py, so private.
      pass
  ```

# Workflow

## Find All Functions
- Find all functions in `<FILE>`

## Search for External Calls
- For each function, search the whole codebase:
  ```bash
  grep -r "<FUNC>" --include="*.py" --include="*.ipynb" --exclude="test_*.py"
  ```

## Classify and Rename
- Classify each function as public or private from its external usage
- Rename functions and update all call sites (in both files)
- Verify the changes

# Verification
- [ ] Grep the entire codebase to confirm all calls were renamed correctly
      ```bash
      grep -r "old_name\|new_name" --include="*.py" --include="*.ipynb"
      ```
- [ ] Run pyright to verify type correctness of modified function invocations
- [ ] Run unit tests for the modified files to ensure nothing broke
