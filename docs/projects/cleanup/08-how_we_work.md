# How We Work on Cleanup

- **Goal**: a new contributor or an AI agent reads this file and knows how we work on
  the cleanup of `helpers`
- **Process**:
  [`docs/planning/all.plan_work.how_to_guide.md`](/docs/planning/all.plan_work.how_to_guide.md)

## Resources

- **GitHub project**: [Cleanup](https://github.com/users/gpsaggese/projects/17)
- **Parent issue**: [#1465](https://github.com/gpsaggese/helpers/issues/1465)
- **Related issues**: [#1447](https://github.com/gpsaggese/helpers/issues/1447),
  [#1433](https://github.com/gpsaggese/helpers/issues/1433)
- **Slack channel, Google Drive dir, Google Doc**: none yet

## Master Plan

- **File**: [`04-plan.md`](/docs/projects/cleanup/04-plan.md), the source of truth,
  per
  [`D2`](/docs/projects/cleanup/03-decisions.md#d2-the-plan-file-is-the-source-of-truth)
- Change the plan in a PR, like code, and log why in `07-progress.md`

## Log

- **File**: [`07-progress.md`](/docs/projects/cleanup/07-progress.md)
- **Format**: a history table, one row per date
  - Switch to one section per merged PR when a row is too short

## Task Rule

- Execute only the PRs that are in the plan
  - Propose a new PR as a change of `04-plan.md` first
- Create the GitHub issue of a PR before starting it
  - Title: `Cleanup: <PR id> <title>`, e.g., `Cleanup: PR_B1 Remove the AWS step from
    the CI workflows`
  - Body: `Parent: #1465`, and a link to the PR entry in `04-plan.md`, not a copy of
    it
  - Add the issue to the Cleanup project
- Name the branch `HelpersTask<issue>_<description>`
- Follow
  [`all.issue_to_tmux_workflow.how_to_guide.md`](/docs/tools/git/all.issue_to_tmux_workflow.how_to_guide.md)
  for the issue, the branch, the PR, the worktree, and the tmux session
- Post an ETA in the issue when you take the task, and update it when it changes
- Confirm with the reviewer before removing an item that looks dead: some items are
  done in a certain way for a reason

## PR Rule

- One PR of the plan per GitHub PR, unless the PR is over the size cap of
  [`all.submit_code_for_review.how_to_guide.md`](/docs/coding/all.submit_code_for_review.how_to_guide.md#stick-to-smaller-prs)
- Run the commit gates with `pre-commit.py` before each commit
- Describe the PR with `.claude/templates/github_PR_description.template.md`
  - Add the migration note of
    [`R19`](/docs/projects/cleanup/01-prd.md#r19-migration-notes-for-downstream-repos)
    when the PR renames or removes an env var, a config key, a linked file, a public
    function, or an invoke task
  - Give the fast and slow test counts before and after the PR, per
    [`R18`](/docs/projects/cleanup/01-prd.md#r18-no-new-test-failures)
- In the same PR, tick the PR in `04-plan.md` and add a row to `07-progress.md`
  - Draft the update with `/project.update_progress <PR id>`

## AI Rule

- Skills to use in each step of the loop:
  [`docs/tools/ai/all.ai_workflows.how_to_guide.md`](/docs/tools/ai/all.ai_workflows.how_to_guide.md)
- An agent can run one PR of the plan from start to end
  - Write the spec first for the PRs marked "needs `06-spec.<PR id>.md`"
  - Use `/auto_task.criticize` on the spec before the agent starts
- Prefer running the agents on a laptop to a hosted agent platform
- Show every change to GitHub (issue edit, comment, label) before applying it, per
  `.claude/skills/github.rules.md` "Propose Before Applying"
- Using AI is fine, but the author must be able to explain every line of the
  AI-written code

## Communication Rule

- GitHub for coding questions and code review
- Comments on the docs PR or edits to the docs for the plan
- Slack for quick pings

## Records Rule

- Keep every decision in [`03-decisions.md`](/docs/projects/cleanup/03-decisions.md)
- Never keep a decision only in Slack or in a GitHub comment
- Label each finding in `07-progress.md` as tested or read in the code

## Example

- Example PR that follows the process well: none yet; add the first merged PR of
  `v0.1`
