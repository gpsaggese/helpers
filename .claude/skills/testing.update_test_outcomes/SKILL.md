---
description: Update the expected outcome of failing unit tests
model: haiku
---

# Goal
- The user passes a list of tests, or a repro script, with failing tests
  `<FAILING_TESTS>` whose actual and expected outputs mismatch

# Important
- For all code, follow `.claude/skills/coding.rules.md`
- Follow the invariants and conventions for unit tests in
  `.claude/skills/testing.rules.md`

# Workflow

## Run the Failing Tests
- Run the tests one at a time, the way the user suggested, to confirm they fail
  due to mismatching outputs

## Classify the Assertion Method
- For each failing test method, check whether the result is checked with
  - `self.check_string()`
  - `self.assert_equal()` or a similar assertion (e.g.,
    `hunteuti.assert_sys_calls()`, `self.assertEqual()`)

- Print a table with the following info:
  path of test | fail / pass | check_string or assert_equal
  ```text
  | Path | Test | Status | Assertion Method |
  |------|------|--------|------------------|
  | dev_scripts_helpers/documentation/test/test_notes_to_pdf.py | Test_notes_to_pdf_latex_options::test1 | FAIL | self.assert_equal() with fuzzy_match=True |
  | dev_scripts_helpers/documentation/test/test_notes_to_pdf.py | Test_notes_to_pdf_latex_options::test2 | FAIL | self.assert_equal() with fuzzy_match=True |
  | dev_scripts_helpers/documentation/test/test_notes_to_pdf.py | Test_notes_to_pdf_output_types::test1 | FAIL | self.assert_equal() with fuzzy_match=True |
  ```

- Save this to `tmp.update_test_outcomes.failing_tests.md`

## Update the Expected Output
- For each failing test method:
  - If the result is checked with `self.check_string()`
    - Run the test with the pytest option `--update_golden` to refresh the output
  - If the result is checked with `self.assert_equal()` or a similar assertion
    (e.g., `hunteuti.assert_sys_calls()`), read the file
    `<TEST_DIR>/tmp.initial.actual.txt`
    (e.g.,
    `dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_html.test1`)
    that holds the actual variable, and update the `expected` variable
    - E.g.,
      ```python
      expected = """
      [{'args': (f'jupytext --to ipynb --update {py_file}',),
        'function': 'hsystem.system',
        'kwargs': {}},
       {'args': (f'jupytext --sync {py_file}',),
        'function': 'hsystem.system',
        'kwargs': {}}]
      """
      ```

- Follow `.claude/skills/testing.rules.md`:
  - `## Code Formatting in Tests`
  - `# Test Input and Output Handling`

- Do not change how results are checked
  - E.g., do not replace `self.assert*()` with `self.check_string()` or vice versa
  - E.g., do not replace `self.assert*()` with `self.assertIn()`

# Verification
- [ ] Run all the tests to make sure they are passing
