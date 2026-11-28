# Docs

- All the docs of the cleanup of `helpers`, tracked in
  [#1465](https://github.com/gpsaggese/helpers/issues/1465) and the
  [Cleanup project](https://github.com/users/gpsaggese/projects/17)
- Where to start:
  - [`01-prd.md`](/docs/projects/cleanup/01-prd.md) for what the cleanup must do
  - [`04-plan.md`](/docs/projects/cleanup/04-plan.md) for the themes and the PRs
  - [`09-onboarding.md`](/docs/projects/cleanup/09-onboarding.md) to set up and pick
    a first PR
- This dir is the `docs/` dir of the project, per
  [`D1`](/docs/projects/cleanup/03-decisions.md#d1-keep-the-project-docs-in-the-docs-tree)
  - The project has no code dir: it changes the whole repo
- Process:
  [`docs/planning/all.plan_work.how_to_guide.md`](/docs/planning/all.plan_work.how_to_guide.md)

## Structure of the Dir

- The dir has no subdir: all the docs sit at the top level
  - The number at the start of a name is the slot of the doc and gives the reading
    order, see `.claude/skills/project.rules.md` section "Name the Docs with a Slot
    Number"
- Slots `05` (tasks) and `06` (specs) are empty: they are written when the work of a
  version starts
- No component design doc `02.<N>-design.<component>.md` yet: the cleanup removes and
  renames code, and a PR gets one only when it needs a design

## Description of Files

| File                        | Description                                                         | Cluster    |
| :-------------------------- | :------------------------------------------------------------------ | :--------- |
| `01-prd.md`                 | Requirements, non-goals, success metrics, and open questions        | Specs      |
| `02-design.architecture.md` | The dev system today and after the cleanup, with C4 diagrams        | Design     |
| `03-decisions.md`           | Decisions, accepted and proposed, with the alternatives             | Specs      |
| `04-plan.md`                | Roadmap by theme (`B`, `R`, `U`, `A`, `D`, `C`, `L`, `T`, `W`)      | Plans      |
| `07-progress.md`            | Status, findings with evidence, next steps, and history             | Plans      |
| `08-how_we_work.md`         | Issues, branches, PRs, agents, and records for the cleanup          | Onboarding |
| `09-onboarding.md`          | Access, setup, tests, checks, and a first PR                        | Onboarding |
| `10-glossary.md`            | The terms of the docs and of the code that the cleanup changes      | Onboarding |
