---
description: Get the current PR to a state where it can be reviewed and merged
model: sonnet
---

# Goal

- Run the AI lint, the standard linter, the local tests, and GitHub CI for the
  current PR, and fix anything that comes up, so the PR is ready to review and merge

# Workflow

## Create and Update a Plan

- Create `plan-github.get_pr_ready_to_merge.md`, a bullet list of actions. Keep it
  updated: `[.]` in progress, `[x]` done, `[F]` failed
- E.g.,
  ```
  # Plan: get PR #... ready to merge

  - [ ] Get PR number and branch name
  - [ ] Make sure PR is ready (not draft)
  - [ ] Run AI lint with --add_todos, commit TODOs
  - [ ] Resolve added TODO(ai_gp) items
  - [ ] Run standard linter, fix issues
  - [ ] Make Sure The Affected Local Tests Pass
  - [ ] Make local tests pass
  - [ ] Run and monitor GitHub CI
  - [ ] Report status on PR
  - [ ] Fix any CI failures
  ```

## Get the PR Number and Branch Name

- Get the PR number:

  ```bash
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name:

  ```bash
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Run the AI Lint and Add TODOs

- Run the AI linter on the branch. Make it leave `TODO`s, not silently rewrite code:

  ```bash
  > linters2/cc_lint.py --branch --add_todos
  ```

- Commit the added `TODO`s with pending changes (see "Never Commit Junk Files")

## Resolve the Added TODOs

- For each file that `cc_lint.py` annotated, use `/coding.todoai_gp` to implement
  its `TODO(ai_gp)` items
- Commit the fixes (see "Never Commit Junk Files")

## Run the Standard Linter

- Run the standard linter on the branch:

  ```bash
  > linters2/lint.py --branch
  ```

- Commit any resulting changes (see "Never Commit Junk Files")

## Fix Pyright Issues
- Fix the pyright warnings and errors in the branch
  ```bash
  > linters2/lint.py --clear_actions --action "pyright" --branch
  ```
- Commit any resulting changes (see "Never Commit Junk Files")

## Make Sure The Affected Local Tests Pass
- Run the tests affected by the change, using
  ```
  > pytest <TEST_NAMES>
  ```
  to iterate, then check all builds with `pytest_multi_build.py`
  ```
  > pytest_multi_build.py --target <TEST_NAMES>
  ```

## Make Sure Local Tests Pass
- Use `/github.get_pr_to_pass_local_tests` to run and fix the local unit tests, even
  if it is a long task

## Make Sure GitHub CI Passes
- Use `/github.get_pr_to_pass_ci_tests` to run, monitor, and fix GitHub CI failures

## Never Commit Junk Files

- Never run `git add -A` or `git add .` to stage a fix. They sweep in untracked
  junk: logs, `tmp.*` scratch files, and test-run caches like `.pkl`/`.json`
- Stage files explicitly by path, e.g., `git add <file1> <file2>`
- Before committing, run `git status --short` and drop anything not part of the fix
- If junk was already committed and pushed, amend the commit to contain only the
  intended files, then force-push (`git push --force-with-lease`). Do not leave the
  junk in history

## Loop

- Repeat until no `cc_lint.py` `TODO`s remain, the standard linter is clean, and the
  local tests and GitHub CI checks all pass

# Constraints

- Runs both locally on a dev computer and remotely on cloud (e.g., on GitHub or
  Anthropic infrastructure)

# Verification

- [ ] `linters2/cc_lint.py --branch --add_todos` adds no new `TODO`s
- [ ] No unresolved `TODO(ai_gp)` items remain in the branch's modified files
- [ ] `linters2/lint.py --branch` reports no issues
- [ ] Local unit tests pass (per `/github.get_pr_to_pass_local_tests`)
- [ ] `gh pr checks --watch $GH_PR_NUM` reports all checks successful (per
      `/github.get_pr_to_pass_ci_tests`)
- [ ] A PR comment reports the final CI status
- [ ] `git status --short` shows only the intended files staged before commit
