---
description: Fix the input / output variables of a test
model: haiku
---

# Goal
- Transform the test method so that:
  - The inputs and outputs are strings with """ and dedent
  - The output is checked with `self.assert_equal()`
  - Follow `.claude/skills/testing.rules.md`:
    - `# Writing Test Code`
    - `## Code Formatting in Tests`
    - `# Test Input and Output Handling`
    - `## Compare Whole Output with assert_equal, Not Piecewise`

- Factor out as much code as possible into helper functions
  - Follow `## Use Helper Methods When You Have Repetitive Tests` in
    `.claude/skills/testing.rules.md`

- Do not change the intent of the test

# Verification
- [ ] Run the tests to make sure they pass
