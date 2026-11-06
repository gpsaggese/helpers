---
description: Find unused packages in requirements.txt not needed by the project code
model: haiku
---

# Goal
- Act as an expert in Docker
- Given a project dir `<TARGET_DIR>`, find the packages in `requirements.txt`
  that its code does not need

# Workflow

## Methodology
- Find actual imports in all `.py` files in `<TARGET_DIR>` with
  `grep -r "import <PKG>"` or AST-based analysis
- Map each package in `requirements.txt` to its import name (e.g., `Pillow` ->
  `PIL`, `scikit-learn` -> `sklearn`, `PyYAML` -> `yaml`)
- Also check `setup.py`, `pyproject.toml`, `tasks.py`, and `Makefile` for
  indirect or tool-level usage
- Flag but do NOT remove packages that are:
  - Runtime plugins or extras loaded dynamically (e.g., via `importlib`)
  - Transitive dependencies pulled in by other listed packages
  - Used only in test files (mark them as "test-only")

## Output
- Print a table with columns:
  ```verbatim
  package | import_name | used_in_code | verdict
  ```
  - `verdict` is one of: `remove`, `keep`, `investigate`, `test-only`
- Propose the trimmed `requirements.txt` contents and write it to disk

# Verification
- [ ] Confirm every package in `requirements.txt` has a verdict
- [ ] Confirm no package marked `remove` is still imported anywhere in
      `<TARGET_DIR>`
- [ ] Confirm the trimmed `requirements.txt` was written to disk
