# PR and Code Review Checks: Decisions

- Every non-obvious choice, why it was made, and what else was considered. Newest
  at the bottom of each section
- Moved from the section `## Design Decisions` of
  [`02-design.architecture.md`](/helpers_root/dev_scripts_helpers/repo_checks/docs/02-design.architecture.md)
- Each PR adds its decisions here and links them in its description
- Every status is `proposed`: edit the choice if you disagree, then mark it
  `accepted`
- The ids `CHK1` to `CHK4c` are the ids of the design doc
  [`02-design.architecture.md`](/helpers_root/dev_scripts_helpers/repo_checks/docs/02-design.architecture.md),
  not the ids of
  [`02.1-design.checks.md`](/helpers_root/dev_scripts_helpers/repo_checks/docs/02.1-design.checks.md)
- Task list: [`05-tasks.md`](/helpers_root/dev_scripts_helpers/repo_checks/docs/05-tasks.md)

## Inputs and Selectors

### `D1` (A check gets only the dir and the paths)

- **Decision**: a check gets `--dir` and a selector, and asks the disk, git, and `gh`
  for the rest
- **Why**:
  - The PR is the branch checked out in `--dir`
  - The base of `--branch` is the base of that PR
- **Alternatives**: add `--pr_url`, `--base`, `--head`, and `--branch_name`
  - It works offline and on a `--dir` with no PR branch
  - The value can disagree with the files on disk, so a check needs a guard
- **Status**: proposed

### `D2` (`--all_files` is the default selector)

- **Decision**: `--all_files` is the default, since `--dir` alone checks the code in
  a dir
- **Why**: a check with no flags works on a dir outside a PR
- **Alternatives**: `--branch` as the default, as `invoke git_files` does
  - A check with no flags would check the diff of the branch
  - It would not run on a dir outside a PR
- **Status**: proposed

### `D3` (The selectors are written in `repo_check_utils.py`)

- **Decision**: write the selectors in `repo_check_utils.py`, and reuse the flag
  names and semantics of `invoke git_files`
- **Why**: `hgit.get_files_to_process()` does not fit
  - It hardcodes `origin/master`
  - It drops the deleted files, which CHK2 needs
  - Its `--all_files` does not honor `.gitignore`
  - Its `branch` paths are relative to the repo root, not to `dir_name`
- **Alternatives**: extend `get_files_to_process()` with a base and the deleted
  files
  - One implementation for all the tools
  - It changes a shared function used by many `invoke` tasks
- **Status**: proposed

### `D4` (`--all_files` includes the untracked files)

- **Decision**: `--all_files` returns tracked and untracked files, minus the ignored
  ones
- **Why**: a large file that is not yet added is checked too
- **Alternatives**: tracked files only
  - This hides a large file that is not yet added
- **Status**: proposed

## Layout and Reuse

### `D5` (The generic checks live in a new dir `repo_checks/`)

- **Decision**: new dir `helpers_root/dev_scripts_helpers/repo_checks/` for the
  scripts that are not PR specific
- **Why**: the name does not say PR for a check that works on a dir
- **Alternatives**: keep all of them in `helpers_root/dev_scripts_helpers/github/`
  with the `gh_pr_` prefix
  - Simpler, but the name says PR for a check that works on a dir
- **Status**: proposed

### `D6` (The class checks and the runner live in `class_project/`)

- **Decision**: the class checks and the runner live in `class_project/`
- **Why**: the generic checks live in `helpers_root/`, which other repos also use
- **Alternatives**: all scripts in `helpers_root/`
- **Status**: proposed

### `D7` (A public `compare_docker_files()` in `create_project.py`)

- **Decision**: add a small public `compare_docker_files()` to
  `class_project/create_project.py` and call it from `check_project_layout.py`
- **Why**:
  - No log file in the current client, no `uv` call
  - The function needs `pandas`, which only `create_project.py` loads today
- **Alternatives**: leave `create_project.py` unchanged and copy its small `filecmp`
  logic
  - This duplicates the `_DOCKER_FILES` list
- **Status**: proposed

### `D8` (`check_all.py` is written in the last PR)

- **Decision**: write `check_all.py` in the last PR
- **Why**: the runner needs all the checks
- **Alternatives**: skip it, and let the skill call each script
- **Status**: proposed

## Pre-Commit Hook

### `D9` (The pre-commit hook is unchanged)

- **Decision**: leave the pre-commit hook unchanged
- **Why**:
  - `check_file_size()` skips notebooks, while CHK1 does not
  - `pre-commit.py` has a note that it should depend only on the Python standard
    library, and a hook runs in every client, so it should not import `repo_checks/`
  - The rules exist in two places: the hook and the scripts
    - The tests of the scripts cover the cases of the hook rules, to catch a drift
- **Alternatives**: later, add the `--modified` selector and make the hook call the
  scripts
  - One copy of each rule
  - The `ruff` phase of the hook keeps `--fix`, since the scripts are read-only
  - The hook needs the scripts on its import path
- **Status**: proposed

### `D10` (The rules of CHK4c are written again, not imported from the hook)

- **Decision**: write the rules of CHK4c again in `check_code.py`, as small
  functions that return findings
- **Why**:
  - The `check_*()` functions of `git_hooks/utils.py` return `None`: they print, and
    call `sys.exit()`, so there is no `Why` with a path
  - They read the paths relative to the working dir, and write `cfile` there
  - `check_ruff_format()` rewrites the files and `check_python_compile()` writes
    `__pycache__/`: a PR worktree must stay unchanged
  - `check_file_size()` skips notebooks
- **Alternatives**: make the pure helpers of the hook public, e.g.,
  `_is_merge_conflict_marker()` and `_is_tmp_log_file()`, and import them
  - No copy of the two rules
  - It edits a file that has no change in this task, and its private names become
    an API
- **Status**: proposed

### `D11` (CHK4c is part of the verdict CHK4)

- **Decision**: CHK4c is part of the verdict CHK4, code conventions
- **Why**:
  - The template and the skill keep four verdicts
  - A conflict marker, a syntax error, and a `ruff` finding are convention findings
- **Alternatives**: a new verdict CHK5, with the template at `of 5 checks`
  - A failure of these checks is visible on its own
  - It changes the skill and the template
- **Status**: proposed

## Tooling

### `D12` (`ruff` uses the `pyproject.toml` of the client that holds the script)

- **Decision**: use the `pyproject.toml` of the client that holds the script, as for
  the rules of `gitleaks`
- **Why**: the author of a PR cannot loosen the lint rules in the same PR
- **Alternatives**: let `ruff` find the `pyproject.toml` of the checked dir, as the
  hook does
  - The result is the same as the one the author sees at commit time
  - A PR that edits `pyproject.toml` changes its own verdict
- **Status**: proposed

### `D13` (The local `gitleaks` binary)

- **Decision**: use the local `gitleaks` binary, and print `unknown` when it is
  missing
- **Why**: it works on a range of commits of a worktree, with no mount
- **Alternatives**: the Docker image of the hook, `zricethezav/gitleaks:latest`
  - Same image as the hook
  - It needs Docker and the mounts of the worktree and of the common git dir
- **Status**: proposed
