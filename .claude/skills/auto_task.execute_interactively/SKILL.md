---
description: Execute a sequence of tasks in a loop "execute -> review -> commit"
model: haiku
---

# Goal

- Execute an ordered list of well-specified, sequential tasks `<FILE>` by
  alternating agent execution, human review, and commit in a branch
- Create the GH issue, branch, and PR for `<FILE>` before the loop: each `auto_task`
  maps to one GH issue and one branch/PR (see `.claude/skills/auto_task.rules.md`)
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified,
  and named

# When to Use This Skill

- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" when a task's spec is unclear or incomplete

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, naming, and
  coding/testing conventions

# Constraints

- Create the GH issue, branch, and (draft) PR for `<FILE>` up front: this is this
  skill's job, not the user's
- Do not commit any code change for a task: committing is the user's decision
- Do not merge any PR: merging is the user's decision

# Workflow

## Confirm the Task List

- Read `<FILE>` and follow `.claude/skills/auto_task.rules.md` section "Confirm the
  Task List Before Executing" for the format and the problem/solution check
- Make sure each task is clear. Add a plan of 5 markdown bullets under each task
- If the order or a dependency is unclear, follow the "Ask for Clarification Before
  Executing an Unclear Plan" section of `.claude/skills/auto_task.rules.md` before
  starting

## Create the Issue and the Branch

- Follow `.claude/skills/auto_task.rules.md` section "One GitHub Issue Is the Unit
  of Work": one GH issue covers the whole task list in `<FILE>`
- Create the issue and branch (`<RepoPrefix>Task<IssueNum>_<Description>`) in one
  shot with `git_create_issue_and_branch.py`. Unlike `invoke gh_issue_create` and
  `invoke git_branch_create`, it also branches submodules (e.g., `helpers_root`)

  ```bash
  > git_create_issue_and_branch.py \
      --gh_issue_title "<TITLE>" --gh_issue_body "<Description of the task list>" \
      --no_create_pr
  ```

  - Pass `--gh_issue_id <NUM>` instead of `--gh_issue_title` to reuse an issue
  - `--no_create_pr`: a PR needs a commit ahead of `master`. Open it after the first
    task's commit (see "Wait for User to Confirm")
- `git add` (do not commit) `<FILE>` on the new branch, so its plan is tracked from
  the start, per `@.claude/task_instructions.md`

## Loop Over the Tasks

### Execute Each Task

- Execute each task following `@.claude/task_instructions.md`
- Keep `<FILE>` updated per `.claude/skills/auto_task.rules.md` section "Track Task
  Status"

### Verify Each Task

- If the N-th task writes code, test it locally and in CI following:
  - `.claude/skills/github.get_pr_to_pass_ci_tests/SKILL.md`
  - `.claude/skills/github.get_pr_to_pass_local_tests/SKILL.md`

### Wait for User to Confirm

- After each task, wait for the user to confirm, validate, and review, then commit
- Push the commit. If the branch has no PR yet (first task), open the draft PR now,
  since there is now a commit to diff against `master`
  - If the task spans several repos (see `.claude/skills/auto_task.rules.md`
    "Multi-Repo Issues, Branches, and PRs"), open a draft PR in each affected repo,
    then refresh the issue's companion PR links:

    ```bash
    > git_create_issue_and_branch.py --gh_issue_id <NUM> --submodules \
        --update_pr_links
    ```

- After the user confirms the N-th task, do the N+1 task the same way

# Verification

- [ ] One GH issue and one branch/PR were created for `<FILE>` before the loop,
      named per `.claude/skills/auto_task.rules.md`
- [ ] Each task's status in `<FILE>` reflects its progress (`[ ]`, `[.]`, or `[x]`)
- [ ] Tests touched by each task pass locally and in CI before the task is marked
      done
- [ ] No task started before its spec was clarified with the user
- [ ] No commit was made without the user's confirmation
