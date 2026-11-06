---
description: Analyze and fix failure of tests in GitHub CI
model: haiku
---

# Goal

- Given a run of the GitHub CI, analyze the failures and fix the failing tests

# Workflow

- Read `.claude/skills/pytest.rules.md`

## Parse Logs From CI

- Parse the output of `invoke gh_workflow_list`, which lists the failing tests
- The CI log of the failing tests is in a file `<CI_LOG>`, e.g.:

  ```bash
  # Log is in 'tmp.failure.check_if_the_linter_was_run.gp_scratch_19.txt'
  ```

- The list of failing tests `<FAILING_TESTS>` is in a file `<REPRO_SCRIPT>`, e.g.:

  ```bash
  ... # To run the tests:
  ... > ./tmp.pytest_repro.fast_tests.sh
  ```

## Check Whether the Failure Reproduces Locally

- Parse `<CI_LOG>`
- Run `<REPRO_SCRIPT>` locally to check whether `<FAILING_TESTS>` fail there too
  - For tests that run Docker or Apple containers, run them with each container
    build, per `## Analyze the Effect of Container Builds` in
    `.claude/skills/pytest.rules.md`
- Note any CI vs. local difference: env vars, secrets, container build, or
  flakiness. `/pytest.fix_local_tests` cannot see this CI-specific context, so
  capture it here

## Diagnose and Fix

- Run `/pytest.fix_local_tests` with `<REPRO_SCRIPT>` as `<FAILURE_INFO>` to
  diagnose the root cause and fix the failing tests
  - If a failure reproduces only on CI, diagnose the CI-specific cause directly
    (env, secrets, container build, flakiness) and fix it
- In `plan-pytest.fix_ci_tests.md` in the current dir, report a table of which tests
  pass on CI and locally, and why they fail on CI and locally
- Verify the fixes per `# Verification of the Fix` in
  `.claude/skills/pytest.rules.md`

## Ask the User to Commit
- Ask the user to review and commit the changes
- Wait for CI to pick up the changes and run the tests, then repeat the workflow

# Verification

- [ ] `plan-pytest.fix_ci_tests.md` lists a fix for every failing test
- [ ] Every fix follows `# Verification of the Fix` in
      `.claude/skills/pytest.rules.md`
- [ ] The failing tests pass on both CI and locally after the fix
