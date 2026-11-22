# Issue to tmux Workflow

- This guide shows the flow from a GitHub issue to a tmux session for the work
  ```
  Issue -> Branch -> PR -> Worktree -> tmux -> Merge -> Cleanup
  ```
- Each step lists the main commands only
  - See `all.manual_flow.how_to_guide.md` for the branch and PR tools
  - See `all.git.how_to_guide.md` for worktrees and general Git use

## Create Issue, Branch, and PR

- Create the issue, the branch, and a draft PR in one step
  ```bash
  > git_create_issue_and_branch.py --gh_issue_title "Write AI_Sw_Eng_Book" \
      --gh_issue_body ""
  ```
  - `--no_create_pr` skips the draft PR
  - It does not create a worktree or a tmux session
  - It prints the `git_worktree_tmux.py` command to run next
- To start from an existing issue, use `--gh_issue_id <ID>`
- To create the branch only, from the current repo
  ```bash
  > i git_branch_create --branch-name UmdTask911_Write_AI_Sw_Eng_Book_1
  ```
- Other commands
  - `i gh_issue_create`: Create an issue
  - `i gh_issue_title -i <ID>`: Print the canonical branch name of an issue
  - `i gh_create_pr`: Create a draft PR for the current branch

## Open Worktree and tmux

- Create the worktree and open its tmux session for a branch or a PR
  ```bash
  > git_worktree_tmux.py --branch_name HelpersTask1354_Improve_bookmarking_flow_1
  > git_worktree_tmux.py --pr_number <PR>
  ```
  - Run it outside tmux
  - The worktree is `<dir_suffix>_worktree_<issue_id>` in `~/src`
- Use `--action create` to create the worktree only, and `--action open` to open
  its session later
- Open the session of an existing worktree with the launcher
  ```bash
  > ~/go_helpers --index _worktree_1354
  ```

## Work in the Session

- `i git_merge_master`: Merge `origin/master` into the branch
- `i git_branch_files`, `i git_branch_diff`: List or diff the changed files
- `gh_info.sh`: Print the PR and the issue of the current branch
- `tmux_reset.py`: Reset the window names of the session
- ...

## Check and Merge

- `gh_pr_run_checks.sh`: Print the CI state of the PR, rerun the checks, and
  print the state again
- `i gh_watch`: Watch the workflows until they end
- `/github.get_pr_ready_to_merge`: Get the PR ready for review and merge
- `/github.get_pr_to_pass_ci_tests`: Fix the failing CI checks

## Clean Up

- After the PR is merged, delete the worktree, the tmux session, and the branch
  ```bash
  > git_worktree_tmux.py --pr_number <PR> --action delete --delete_branch
  ```
  - Run it from the main repo, outside the session to delete
- `i git_branch_is_merged`: Check that the branch is merged into `master`
- `i git_branch_delete_merged`: Delete all the merged branches, local and remote
