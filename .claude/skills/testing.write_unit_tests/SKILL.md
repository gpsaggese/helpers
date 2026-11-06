---
description: Propose a plan for unit testing a file and then implement it
model: haiku
---

# Goal
- Propose a unit test plan for a file, then implement it after the user approves

# Workflow

## Propose a Unit Test Plan
- For a file `<FILE>`, write a comprehensive unit test plan per
  `.claude/skills/testing.rules.md`
- Save a file summarizing what will be tested

## Implement the Unit Test Plan
- Wait for the user to approve or modify the plan
- Then implement it

# Important
- All unit test invariants and conventions are in `.claude/skills/testing.rules.md`
- For all code, follow `.claude/skills/coding.rules.md`

# Verification
- [ ] Make sure everything in `# Verification` in `.claude/skills/testing.rules.md`
  is verified
