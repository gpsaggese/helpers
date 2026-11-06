---
description: Make sure that all the functions have a single return statement
model: haiku
---

- I will pass you one or more files `<FILES>`

# Goal
- Go through each function and make sure it has a single return statement

- For functions returning `None`, keep the `return` statements that exit early

# Conventions
- Do not change the behavior of the code in any way
- Follow the rules in `.claude/skills/coding.rules.md`

# Verification
- [ ] Confirm each function has a single `return` statement (except early exits
      in functions returning `None`)
- [ ] Run the file's unit tests to confirm behavior is unchanged
