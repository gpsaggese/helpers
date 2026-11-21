---
description: Make the local unit tests pass for the current PR
model: sonnet
---

# Goal
- Run, monitor, and fix the local unit tests for the current PR

# Workflow

## Create and Update a Plan
- Create `plan-github.get_pr_to_pass_local_tests.md`: a bullet list of actions
- Keep it updated, marking each action `[.]` in progress, `[x]` done, `[F]` failed

## Get the PR Number and Branch Name
- Get the PR number
  ```bash
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name
  ```bash
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Run Local Regressions
- Run full test suite locally:
  ```bash
  > pytest_multi_build.py --target . 2>&1 --timeout -1 | tee tmp.auto_task.pytest_multi_build.log
  ```
- Wait for the script to terminate

## Check Regressions to Complete

- Check the output of the local regressions with:
  ```bash
  > pytest_failed_multi_build.py 2>&1 | tee tmp.auto_task.pytest_failed_multi_build.log
  ```

## Report Status on the PR
- If local regressions are passing:
  ```bash
  > gh pr comment $GH_PR_NUM --body "Local tests passing"
  ```
- If any failures, document error and post:
  ```bash
  > gh pr comment $GH_PR_NUM --body "Local test failures found: [error summary]. Investigating..."
  ```

## Fix the Failures
- If failures were found, run `tmp.pytest_failed_multi_build.repro.sh` to understand
  what failed and use `/pytest.fix_local_tests` to analyze and fix them
  - If the fix is simple, just fix it and commit
  - If the fix is not clear, stop and ask for the user to help

## Never Commit Junk Files
- Never run `git add -A` or `git add .` to stage a fix: they sweep in every
  untracked file (logs, `tmp.*` scratch files, test-run artifacts like
  `.pkl`/`.json` caches), not just the intended files
- Always stage files explicitly by path, e.g. `git add <file1> <file2>`
- Before committing, run `git status --short` and drop anything that is not part
  of the intended fix
- If junk was already committed and pushed, amend the commit to hold only the
  intended files and force-push (`git push --force-with-lease`)

## Loop
- Keep repeating until the PR is passing all the local tests

# Constraints
- This skill runs both when executed locally on a dev computer and remotely on cloud
  (e.g., on GitHub or Anthropic infrastructure)

# Verification

- [ ] `pytest_failed_multi_build.py` reports no failing tests
- [ ] A PR comment reports the final local test status
- [ ] `git status --short` shows only the intended files staged before commit
