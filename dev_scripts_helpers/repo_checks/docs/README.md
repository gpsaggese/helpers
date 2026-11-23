# Docs

- These docs describe the tools that automate the review of a PR and of a chunk of
  code (GitHub issue `HelpersTask1451`)
  - One script per check returns `PASS`, `FAIL`, or `N/A`, with a `Why` and a `Fix`
  - The same check works on a PR (`--branch`) and on a dir (`--all_files`, `--files`,
    `--from_file`)
- Start with
  [`02-design.architecture.md`](/helpers_root/dev_scripts_helpers/repo_checks/docs/02-design.architecture.md),
  then
  [`02.1-design.checks.md`](/helpers_root/dev_scripts_helpers/repo_checks/docs/02.1-design.checks.md)
- The process is in
  [`docs/planning/all.plan_work.how_to_guide.md`](/docs/planning/all.plan_work.how_to_guide.md)
- The scripts are not written yet: the code goes in
  [`helpers_root/dev_scripts_helpers/repo_checks/`](/helpers_root/dev_scripts_helpers/repo_checks/)
  and in [`class_project/`](/class_project/)

## Structure of the Dir

- All the docs sit at the top level of `docs/`
- Their names start with the slot number that gives the reading order, see
  [Name the Docs with a Slot Number](/docs/planning/all.plan_work.how_to_guide.md#name-the-docs-with-a-slot-number)
- The slots `01`, `04`, `06`, `07`, and `08` are empty: the docs do not exist yet

## Description of Files

| File                       | Description                                                                          | Cluster |
| :------------------------- | :----------------------------------------------------------------------------------- | :------ |
| `02-design.architecture.md` | Design of the scripts: selectors, queries to git, flags, output, tests, pre-commit hook | Design  |
| `02.1-design.checks.md`    | Every check of a PR and of a chunk of code, `CHK1` to `CHK13`, and how to implement each | Design  |
| `03-decisions.md`          | Why the scripts are built this way, with the alternatives, `D1` to `D13`             | Specs   |
| `05-tasks.md`              | Queue of the PRs that the `auto_task` flow runs, `PR1` to `PR5`                      | Plans   |
