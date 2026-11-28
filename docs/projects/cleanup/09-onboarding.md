# Cleanup Onboarding

- **Goal**: from zero to running the tests of `helpers` and the checks of the
  cleanup, then a first PR of the plan
- Point to the general setup of the repo instead of repeating it:
  [`all.development_setup.how_to_guide.md`](/docs/onboarding/all.development_setup.how_to_guide.md)

## 1. What the Project Is (5 Minutes)

- Read the goal of [`01-prd.md`](/docs/projects/cleanup/01-prd.md) and the roadmap
  of [`04-plan.md`](/docs/projects/cleanup/04-plan.md)
- The project removes and renames code: most PRs delete files, rename env vars, or
  change the image build

## 2. Access You Need

- Write access to [`gpsaggese/helpers`](https://github.com/gpsaggese/helpers)
- `gh` logged in with the `repo`, `workflow`, and `read:packages` scopes
  - Add `read:project` to read the
    [Cleanup project](https://github.com/users/gpsaggese/projects/17)
- Read access to the dev image
  - Until the image is copied, before `PR_B1`: `ghcr.io/causify-ai/helpers`, a
    private package of another org
  - After the copy: `ghcr.io/gpsaggese/helpers`
- No AWS account: no test needs one, see finding 4 of
  [`07-progress.md`](/docs/projects/cleanup/07-progress.md)

## 3. Setup

- Build and activate the thin environment, per "Set up the thin environment" in
  [`all.development_setup.how_to_guide.md`](/docs/onboarding/all.development_setup.how_to_guide.md)
  ```bash
  > ./dev_scripts_helpers/thin_client/build.py
  > source dev_scripts_helpers/thin_client/setenv.sh
  ```
- Until `PR_R1` merges, set the registry env var, or every `invoke` command fails
  - `invoke docker_pull` pulls `$CSFY_ECR_BASE_PATH/helpers:dev`
  - Use `ghcr.io/causify-ai` until the image is copied to `ghcr.io/gpsaggese`
  ```bash
  > export CSFY_ECR_BASE_PATH=ghcr.io/gpsaggese
  ```
- Log in to GHCR and pull the dev image
  ```bash
  > gh auth token | docker login ghcr.io -u <github_user> --password-stdin
  > invoke docker_pull
  ```

## 4. Run the Tests

- Run the fast and slow tests, and save the counts: each PR compares them with
  `master`, per [`R18`](/docs/projects/cleanup/01-prd.md#r18-no-new-test-failures)
  ```bash
  > invoke run_fast_tests
  > invoke run_slow_tests
  ```
- Run one test file in the container
  ```bash
  > invoke docker_cmd --cmd "pytest helpers/test/test_hserver.py -v"
  ```
- Run the commit gates
  ```bash
  > pre-commit.py
  ```

## 5. Run the Checks of the Cleanup

- Count what is left of each theme
  ```bash
  > git grep -i -l -E "causify|csfy|cryptokaizen|kaizen" | wc -l
  > git grep -i -l poetry | wc -l
  > git grep -l -E "s3_bucket_info|\becr\b|ECR" | wc -l
  ```
- Check the state of CI on `master`
  ```bash
  > gh run list --repo gpsaggese/helpers --branch master --limit 10
  ```

## 6. Read the Code in This Order

- [`repo_config.yaml`](/repo_config.yaml): the config that the invoke tasks read
- [`tasks.py`](/tasks.py): the invoke entry point
- [`helpers/lib_tasks/lib_tasks_docker.py`](/helpers/lib_tasks/lib_tasks_docker.py):
  how invoke starts the container
- [`devops/docker_build/dev.Dockerfile`](/devops/docker_build/dev.Dockerfile) and
  [`devops/docker_run/entrypoint.sh`](/devops/docker_run/entrypoint.sh): how the
  image is built and started
- [`.github/workflows/common_run_tests.yml`](/.github/workflows/common_run_tests.yml):
  how CI runs the tests

## 7. Pick a First Task

- Take the first unchecked PR of `v0.1` in
  [`04-plan.md`](/docs/projects/cleanup/04-plan.md), e.g., `PR_B1`
- Follow [`08-how_we_work.md`](/docs/projects/cleanup/08-how_we_work.md) for the
  issue, the branch, and the PR

## 8. Common Problems

- **`KeyError: 'CSFY_ECR_BASE_PATH'` on any `invoke` command**: set the env var, see
  "Setup"; `PR_R1` removes the need
- **`docker pull` of the dev image fails with `denied`**: log in to GHCR with a token
  that can read the package
- **Docker-in-Docker does not start on Mac**: the container needs `--privileged`,
  see finding 9 of [`07-progress.md`](/docs/projects/cleanup/07-progress.md)
- **The CI test workflows fail at "Configure AWS credentials"**: expected until
  `PR_B1` merges
- **The CI test workflows do not run on the PR**: they skip draft PRs
- **`pre-commit.py` fails at `check_gitleaks` with `container: command not found`
  on Mac**: set `CSFY_DOCKER_ENGINE=docker`, see finding 12 of
  [`07-progress.md`](/docs/projects/cleanup/07-progress.md)
