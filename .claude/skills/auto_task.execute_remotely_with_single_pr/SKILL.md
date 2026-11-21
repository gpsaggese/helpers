---
description: Execute a sequence of tasks by dispatching them to Claude on GitHub
model: haiku
---

# Goal

- Execute a well-specified task `<FILE>` by delegating it to Claude running remotely
  on GitHub (the `claude-code-action` GitHub Action), not by implementing it in this
  session
- The task becomes its own GitHub issue, branch, and draft PR, so the remote run is
  independent and asynchronous, with no local checkout doing the work
- A task's whole spec lands in one PR: Claude on GitHub may push several commits for
  different parts, but must never open a second PR for the same task
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified,
  and named

## Inputs
- `<FILE>` or a GitHub issue already filed (e.g., #580 or
  https://github.com/gpsaggese/gpsaggese.github.io/issues/580)

# When to Use This Skill

- Use it when tasks are clear enough for an unattended agent, and need no local
  interactivity, local Docker container, or hands-on debugging
- Prefer `.claude/skills/auto_task.execute_interactively/SKILL.md` for exploratory
  tasks or a tight local feedback loop
- Prefer `.claude/skills/auto_task.execute_with_stacked_prs/SKILL.md` for a real
  dependency chain that must be branched from each other
- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" when the spec is unclear or incomplete: a remote run
  must not build on a guess

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, naming, and
  coding/testing conventions. They apply to the code Claude on GitHub writes
- Claude on GitHub starts only on an explicit `@claude` mention in an issue's title
  or body, or in an issue or PR comment, per
  `helpers_root/.github/workflows/claude.yml`
  - Assigning the GH issue (`--gh_assignee`) does not trigger a run

# Constraints

- Do not implement a task's code yourself: dispatch it, then only monitor and report
  on the run and PR
- Do not commit, push, or amend the task's branch: Claude on GitHub pushes to it,
  and merging is the user's decision
- Keep one PR per task: several commits on that PR are fine, but never open a second
  issue/branch/PR for a dispatched task

# Workflow

## Create Issue, if Needed

- If the GitHub issue is not filed, create it

### Confirm the Task List

- Read `<FILE>`, wrapped around the task list like

  ```text
  # Title
  <TITLE>

  # Goal
  <High level goal>

  # Workflow

  ### [ ] <Goal of first task>
  - <Change 1>
  - <Change 2>

  ### [ ] <Goal of second task>
  - <Change 1>
  - <Change 2>
  ```

- Follow `.claude/skills/auto_task.rules.md` section "Confirm the Task List Before
  Executing" for the format and the problem/solution check
- Keep `<FILE>` updated per that file's section "Track Task Status": `[.]` means
  dispatched with the remote run unfinished, `[x]` means the PR is ready for human
  review

### Create the Issue, Branch, and Draft PR

- Locally, create the issue and a draft PR for the task, named per
  `.claude/skills/auto_task.rules.md`

  ```bash
  > git_create_issue_and_branch.py \
      --gh_issue_title "<TITLE>" \
      --gh_issue_body_file <FILE>
  ```

  - By default this opens a branch/PR only in the outer repo. Pass `--submodules` if
    the task also touches a submodule, per `.claude/skills/auto_task.rules.md`
  - With `--submodules`, once a PR exists in several repos, this call also refreshes
    the issue's `## Companion PRs` section. No separate `--update_pr_links` step is
    needed, since the PR is created now
- Return to `master`. The implementation happens on GitHub, not in this checkout

  ```bash
  > git checkout master
  ```

## Trigger Claude on GitHub

- Post the task's spec as a PR comment with an explicit `@claude` mention, so
  `helpers_root/.github/workflows/claude.yml` picks it up

  ```bash
  > gh pr comment <PR_NUM> --body "Assigned to @claude"
  ```

## Monitor Each Remote Run

- Find the `claude.yml` run the comment triggered

  ```bash
  > gh run list --workflow=claude.yml --branch <BRANCH> --limit 1
  ```

- Watch it to completion

  ```bash
  > gh run watch <RUN_ID>
  ```

- If a run fails, read its log. Decide whether the fix needs a follow-up `@claude`
  comment or the user's input, and report which

## Verify Each Resulting PR

- After a successful run, confirm the PR changed, not just replied in a comment

  ```bash
  > gh pr view <PR_NUM> --json commits,additions,deletions
  ```

  - Several commits on this PR are fine, e.g. one per part of a multi-part spec
  - If a follow-up `@claude` comment makes a second PR for the same task, close the
    extra PR and keep the original: one PR per task, no exceptions
- Get the PR's CI to pass following
  `.claude/skills/github.get_pr_to_pass_ci_tests/SKILL.md`
- Mark the task `[x]` in `<FILE>` only once its PR is ready for human review

## Report the Queue

- Report one list to the user, with task, issue, PR link, and run status for every
  task in `<FILE>`, so the batch can be reviewed at once

# Verification

- [ ] Every dispatched task has its own GH issue, branch, and exactly one PR
- [ ] No task has more than one PR (several commits on one PR are fine)
- [ ] Every dispatch comment contains an explicit `@claude` mention
- [ ] No task's code was implemented locally in this session
- [ ] Each task's status in `<FILE>` reflects its remote progress (`[ ]`, `[.]`,
      `[x]`)
- [ ] The final report lists every task with its issue, PR link, and run status
