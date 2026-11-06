---
description: Execute a sequence of tasks as one stack of branches and PRs
model: haiku
---

# Goal

- Execute one GitHub issue as a stack of sequential branches and PRs
  - Name each branch `<BASE>_<ID>` (`ID` = 1, 2, 3, ...)
  - Branch each one from the previous branch, so the PRs stack in review order
- Create the whole stack without stopping for review
  - The user reviews, edits, and merges each PR bottom-up later
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified,
  and named

## Input

- The user passes a task in the format

# When to Use This Skill

- Use only when tasks favor stacked execution: complete specs, a real dependency
  chain, and a user who prefers one batch review over interruptions
- If a spec is unclear, follow `.claude/skills/auto_task.rules.md` section "Ask for
  Clarification Before Executing an Unclear Plan". Do not build on a guess
- Resolve all doubts with the user before you start, so the stack runs uninterrupted

# Workflow

## Confirm the Task List

- Follow `.claude/skills/auto_task.rules.md` section "Confirm the Task List Before
  Executing". Each ordered task is one branch
- Confirm task `<ID+1>` depends only on `<ID>`, not on `master` or earlier tasks
- If the order or a dependency is unclear, ask before starting. A wrong dependency
  means rebasing the whole stack above it

## Create the Issue and the First Branch (`_1`)

- Follow `.claude/skills/auto_task.rules.md` section "One GitHub Issue Is the Unit
  of Work": one issue covers the whole stack
- Create the issue and the first branch / PR `<BASE>_1`

  ```bash
  > git_create_issue_and_branch.py \
      --gh_issue_title "<TITLE>" --gh_issue_body "<Description of entire stack>" \
      --suffix 1
  ```

- The description of the entire task is
- Commit the file passed by the user (e.g., `tasks.md`)
- Implement task 1, run its tests, commit, push

## Stack Each Following Branch (`_<ID>`)

- For `ID` from 2 to `N`, while still checked out on `<BASE>_<ID-1>`:
  - Derive `<BASE>_<ID>` from the issue, not from the current branch name. Branch
    it from `<BASE>_<ID-1>`, not from `master`:

    ```bash
    > invoke git_branch_create --issue-id <NUM> --suffix <ID> \
        --no-only-branch-from-master --no-abort-if-not-master --no-create-pr
    ```

    - Do not use `invoke git_branch_next_name`. It appends `_1`, `_2`, ... to the
      current branch, so from `<BASE>_<ID-1>` it gives `<BASE>_<ID-1>_1`
    - Pass both `--no-only-branch-from-master` and `--no-abort-if-not-master`. The
      default `only_branch_from_master` (`True`) switches to `master` first
  - Implement task `<ID>`, run its tests, commit, and push
  - Open the PR against `<BASE>_<ID-1>`, not `master`:

    ```bash
    > gh pr create --base <BASE>_<ID-1> --head <BASE>_<ID> --title "<TITLE>"
    ```

  - Do not stop for review. Move to `<BASE>_<ID+1>` once `<BASE>_<ID>`'s tests pass

## Report the Stack

- Confirm each PR's base with `gh pr view <BASE>_<ID> --json baseRefName`
- Report one ordered list to the user: branch, PR link, and base branch, for every
  `ID`

# How the Stack Gets Merged

- This is the user's process. It is documented so a later run can resume a stack
- The user reviews, edits, and merges PRs bottom-up, one at a time
- After `<BASE>_<ID-1>`'s PR merges into `master`:
  - Retarget `<BASE>_<ID>`'s PR to `master`, if GitHub did not do it when the merged
    branch was deleted: `gh pr edit <BASE>_<ID> --base master`
  - Sync `<BASE>_<ID>` with the updated `master`, resolve any conflicts, then commit
    and push:

    ```bash
    > invoke git_merge_master
    ```

    - This is a merge, not a rebase. After a squash merge, expect a conflict even on
      identical content: Git cannot tell the squashed commit from the originals
  - Repeat for `<BASE>_<ID+1>` once `<BASE>_<ID>`'s PR merges
- Never force-push a branch whose PR has unresolved review comments without telling
  the user first

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, naming, and coding and
  testing conventions
- If a task needs splitting mid-run, use `.claude/templates/auto_task.template.md`
- If the issue also spans a submodule (see `.claude/skills/auto_task.rules.md`
  "Multi-Repo Issues, Branches, and PRs"), only the outer repo stacks
  - The submodule gets one companion branch and PR, since
    `invoke git_branch_create --suffix` does not fan out to submodules
  - Pass `--submodules` with `--suffix 1` on the first
    `git_create_issue_and_branch.py` call, then refresh the companion PR links after
    the stack is built:

    ```bash
    > git_create_issue_and_branch.py --gh_issue_id <NUM> --submodules \
        --update_pr_links
    ```

# Constraints

- Follow `.claude/skills/auto_task.rules.md` sections "The User Owns Commit and
  Merge Decisions" and "One GitHub Issue Is the Unit of Work"
- Do not start the next task before the current task's tests pass. An untested task
  compounds into everything stacked on it
- Do not squash or reorder commits across tasks unless asked
- Keep one task per branch and one PR per task. Do not fold queued tasks together
- One GH issue covers the whole stack. Do not open an issue per branch

# Verification

- [ ] Every branch is named `<BASE>_<ID>`, with `ID` rising by 1 from `<BASE>_1`
- [ ] Each branch's merge base is the previous branch, and `<BASE>_1`'s is `master`
- [ ] Each PR's base is its parent branch, and `<BASE>_1`'s PR base is `master`
- [ ] Every branch and PR sits under the one GH issue created with `<BASE>_1`
- [ ] Each task's tests passed before its branch was pushed
- [ ] The final report lists every branch and PR in dependency order, with links
