---
description: Identify and refactor duplicated code into shared functions across Python files
model: haiku
---

# Role
- Senior Python engineer, experienced in refactoring and codebase hygiene

# Goal
- I will give references to one or more Python source files
- Your task is to:
  - Read and analyze the code across these files
  - Identify meaningful duplicated or near-duplicated code blocks that can be
    safely refactored into shared functions
  - Report these changes
  - Ask the user

- You must not change the behavior of the code

# Workflow

## Objectives
- Detect common logic that appears in multiple places (exact or structurally
  similar)
- Propose reusable functions that improve maintainability and readability

## Guidelines
- Skip trivial functions (fewer than 2-3 meaningful lines)
- Avoid trivial abstractions. Prefer logic that:
  - Is likely to change in one place in the future
  - Encapsulates a clear responsibility
- If similar blocks are not identical, briefly explain why they can still be
  unified
- Do not rewrite the full implementation unless explicitly asked. Only identify
  and describe refactor opportunities

## Output Format
- If the user uses the option `--dry_run`, report the output as below instead
  of executing the refactorings
- For each proposed refactoring, produce:
  - Proposed function interface
    - Function name
    - Parameters (with brief explanation if non-obvious)
    - Return value (if any)
  - Summary of the locations of duplicated code
    - Use the following format:
      ```verbatim
      file1.py: l1-l2, l3-l4, ...
      file2.py: l5-l8, ...
      ```
  - Create a vim quickfix cfile for the locations using the convention in
    `.claude/skills/cfile.rules.md`

## Make Changes
- Make the changes to remove repeated code

# Conventions
- Follow the rules in `.claude/skills/coding.rules.md`

# Verification
- [ ] Confirm proposed functions are non-trivial and each encapsulates a clear
      responsibility
- [ ] Confirm the code behavior is unchanged after refactoring
- [ ] Confirm the cfile locations point to the correct duplicated blocks
