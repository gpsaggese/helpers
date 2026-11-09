# PR #<PR_NUM> Check: <TITLE>

- **PR link**: <PR_URL>
- **Worktree**: `<WORKTREE>`
- **Result**: <NUM_FAILED> of 4 checks failed
- **CHK1 (file size and binary files)**: <PASS_OR_FAIL>
  - **Why**: <FINDING_WITH_PATH_AND_SIZE>
  - **Fix**: <PROPOSED_FIX>
- **CHK2 (project directory)**: <PASS_FAIL_OR_NA>
  - **Why**: <FINDING_WITH_PATH>
  - **Fix**: <PROPOSED_FIX>
- **CHK3 (PR title)**: <PASS_OR_FAIL>
  - **Why**: <FINDING_WITH_TITLE_AND_EXPECTED_TITLE>
  - **Fix**: <PROPOSED_FIX>
- **CHK4 (code conventions)**: <PASS_OR_FAIL>
  - **Why**: <FINDING_WITH_PATH_AND_LINE_AND_RULE_FILE>
  - **Fix**: <PROPOSED_FIX>
- **Clean up**:
  ```bash
  > git worktree remove <WORKTREE>
  ```
