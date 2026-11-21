This document contains the rules to follow when working with GitHub issues,
projects, branches, and Pull Requests

# Issues and Projects

## Prefix Issue Titles With a Project Tag

- Start the title of every issue in a project with `<TAG>: `, where `<TAG>` is the
  project name (e.g., `Noesis`)
  - **Bad**: `Get the team gelled together`
  - **Good**: `Noesis: Get the team gelled together`

- Put a roadmap ID right after the tag, separated by a space
  - **Bad**: `Noesis_PR_M12 Add auction result tables`
  - **Good**: `Noesis: PR_M12 Add auction result tables`

- Use the same tag for all the issues of one project, so the issues sort and filter
  together

## Drop Redundant Words From Titles

- Write the tag once, at the front
  - **Bad**: `Organize Noesis codebase into components`
  - **Good**: `Noesis: Organize codebase into components`

- Do not repeat in the title what the issue number already carries, e.g., a branch
  ID like `UmdTask639_`
  - **Bad**: `Noesis: Follow up to UmdTask639_Noesis_PR_S11`
  - **Good**: `Noesis: Follow up to PR_S11`

- Keep a second mention of the tag when it is the subject of the sentence
  - **Good**: `Noesis: Prove that Noesis improves over a single-sided market`

## Link Child Issues to Their Parent

- Start the body of a child issue with the links that place it in the plan
  ```
  Parent: #640

  Architecture: #742

  Depends on: #744
  ```
- Add every child issue of a tagged parent to the same project as the parent

## Handle Each Project Item Type Differently

- Read `content.type` of each project item before acting on it
  - `Issue`: apply the title rules above
  - `PullRequest`: leave the title unchanged, it follows the branch convention
    (see `## Name Branches After the Issue`)
  - `DraftIssue`: has no issue number, so `gh issue edit` cannot change it; list it
    and let the user decide

## Read All the Items of a Project

- Always pass `--limit` to `gh project item-list`, since the default is 30 items
  ```bash
  > gh project item-list <NUM> --owner <OWNER> --limit 500 --format json
  ```
- Compare the number of items read with `items.totalCount` from
  `gh project view <NUM> --owner <OWNER> --format json`

## Get the Project Scope Before Reading a Project

- Reading a project needs the `read:project` scope
  - The error is `your authentication token is missing required scopes
    [read:project]`
- Ask the user to grant it with this command in the prompt
  ```
  ! gh auth refresh -h github.com -s read:project
  ```
  - Do not run it with a tool: it waits for a browser and a device code, and times
    out
  - `-h github.com` is required in a non-interactive shell, otherwise the command
    prints `--hostname required when not running interactively`

# Branches and Pull Requests

## Name Branches After the Issue

- Name a branch `<Repo>Task<NUM>_<Description>`, where `<NUM>` is the issue number
  - **Good**: `UmdTask640_Noesis_PR_S4_spec`
  - **Good**: `HelpersTask1273_Get_Mac_tests_to_pass`
- Add a `_<N>` suffix for the next branch of the same issue
  (`HelpersTask1273_Get_Mac_tests_to_pass_4`)
- Skills find the issue of a branch from the `Task<NUM>` token, so keep it intact

## Write a Linux-Friendly PR Title

- Write a one-line title
- Use only letters, digits, spaces, `_`, `-`, and `:`
  - **Bad**: `Fix tests & lint (macOS)`
  - **Good**: `Fix tests and lint on macOS`

## Describe the PR With the Template

- Write the PR description following the template
  `.claude/templates/github_PR_description.template.md`
- Write the plan to split a branch into PRs following the template
  `.claude/templates/github_PR_plan.template.md`
- Do not invent test counts or results: run the tests or ask the user

## Stage Files Explicitly

- Never run `git add -A` or `git add .`: it stages untracked junk (logs, `tmp.*`
  files, `.pkl` caches)
- Stage by path and review `git status --short` before each commit
  - **Bad**
    ```bash
    > git add -A
    ```
  - **Good**
    ```bash
    > git add <FILE1> <FILE2>
    > git status --short
    ```

## Report Status on the PR

- Post the result of a local or CI run as a PR comment
  ```bash
  > gh pr comment <PR_NUM> --body "GitHub CI checks passing"
  ```

# Safe Use of the GitHub CLI

## Propose Before Applying

- Treat every change to GitHub (rename, edit, comment, close) as visible to others
  and hard to undo
- Show the exact before / after, wait for a clear "go", then apply
  - An answer to a design question is not a "go"
  - A "do not change" given earlier stays in force until the "go"
- Apply the change with one command per item, from a reviewed script, and stop at
  the first failure

## Change Only What Was Asked

- Rename only titles when asked to rename: do not touch labels, status, body, or
  project fields
- Do not rename PRs unless the user asks for it

## Use the URLs Returned by GitHub

- Take links from the output of `gh`, do not build them by hand
  ```bash
  > gh issue view <ISSUE_NUM> --repo <OWNER>/<REPO> --json url,state
  ```

## Keep Scratch Files Out of the Repo

- Save downloaded JSON and generated scripts in the scratchpad directory, not in
  the Git client
- Keep a downloaded file in a different directory than the script that reads it
- Parse downloaded JSON with `python3 -I`, so a stray module in the current
  directory is not imported

## Name the Files Generated by a Skill

- Name a generated file `<TYPE>-<TOPIC>.<ACTION>.<EXT>` as in
  `.claude/skills/skill.rules.md` `## Generated File Naming`
  - **Good**: `plan-github.update_project.md`
