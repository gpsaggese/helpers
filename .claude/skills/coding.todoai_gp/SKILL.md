---
description: Implement TODO(ai_gp) items in a file: renames, code updates, references
model: haiku
---

# Goal
Implement all the `TODO(ai_gp)` items in the passed file `<FILE>`.

# Workflow

## Renaming and Moving Objects
- When renaming an object, update all its references in the code base
  - When renaming or moving files, update imports
  - For functions, find the callers in notebooks (`ipynb`), Python files, and other
    files, and update them (use `grep` to confirm all references are updated)
  - Update the docs in txt and md files

- In a `TODO(...):` the sign `-> XYZ` means "rename to XYZ"

- When moving a function among files, also move its tests to the corresponding
  `.../test/test_...` file

## Fix TODOs Around the Code
- When fixing a TODO, check the same file for more instances of it and fix those too

## Remove TODOs
- Remove a `TODO` only if it was implemented
- If a TODO cannot be implemented, leave it and add a short comment on why

# Conventions
- Depending on the file type, follow the corresponding instructions in
  `.claude/rules.md`

# Verification
- [ ] Run the corresponding unit tests to make sure the code works
- [ ] Grep in the repo for the renamed or removed objects to confirm there are no
      hanging references
