# How to Test a Project in Docker

## Summary

- Goal: check that a project dir builds its image, runs its notebooks, and
  passes its unit tests inside its own container
- Use this guide for a project dir with its own `docker_build.sh` and
  `docker_cmd.sh`, e.g., a tutorial or a research project
- The tests subclass `DockerTestCase` from `helpers/hdocker_tests.py`
  - The base class builds the image and checks `docker_cmd.sh` and
    `docker_bash.sh`
  - The subclass adds one test per notebook and one test for the unit tests

## Add the Test File

- Create `test/test_docker_all.py` in the project dir
  - `DockerTestCase` finds the project dir by going up 2 levels from the test
    file, so the file must be in `test/`
- Set `_test_file = __file__`, then add the tests:

  ```python
  import pytest

  import helpers.hdocker_tests as hdoctest


  class Test_docker(hdoctest.DockerTestCase):
      """
      Run all Docker tests for `my_project`.
      """

      _test_file = __file__

      @pytest.mark.slow
      def test1(self) -> None:
          """
          Test that `my_project.API.ipynb` runs without error inside Docker.
          """
          # Prepare inputs.
          notebook_name = "my_project.API.ipynb"
          # Run test.
          self.run_notebook(
              notebook_name, use_docker_cmd=True, generate_html=False
          )

      @pytest.mark.slow
      def test2(self) -> None:
          """
          Test that the unit tests of `my_project` pass inside Docker.
          """
          # Prepare inputs.
          test_file_names = ["test_my_project_utils.py"]
          # Run test.
          self.run_unit_tests(test_file_names)
  ```

- `run_notebook()` runs one notebook with `jupyter nbconvert --execute`
  - `use_docker_cmd=True` runs it through the `docker_cmd.sh` of the project
  - `generate_html=True` renders the HTML with the `html_anchorfix` template, so
    that the per-cell anchors work
- `run_unit_tests()` runs `pytest` on the listed files through `docker_cmd.sh`
  - The names are relative to the `test/` dir of the project
  - The repo is mounted at `/git_root` in the container, so the paths are
    computed from the root of the repo
  - An error is raised if a test file does not exist

## Prepare the Image

- Make sure that the image has `pytest`, e.g., by adding it to the
  `requirements.txt` of the project
  - Without it, `run_unit_tests()` fails inside the container
- Pin the versions in `requirements.txt` to the ones tested together
  - An unpinned package can change on the next build and break the image even if
    the code did not change
  - Add a comment for each pin that is not obvious, e.g., a package that needs
    an old version of another one

## Run the Tests

- Build the image first, from the project dir:
  ```bash
  > cd my_project
  > ./docker_build.sh
  ```
- Run the test file by name, from the root of the repo:

  ```bash
  > python -m pytest my_project/test/test_docker_all.py
  ```

  - If the `pytest.ini` of the repo ignores `test_docker_*.py`, the tests only
    run when the file is named explicitly, as above

- The build test runs first only when the `pytest-order` plugin is installed
  - Without it, the tests run in name order, so `test1` runs before
    `test_docker_build`
  - On a machine that has never built the image, run `./docker_build.sh` once
    before the tests

## Known Issues

- With `use_docker_cmd=True`, `run_notebook()` writes the HTML of each notebook
  next to the notebook
  - Add `*.html` to the `.gitignore` of the project
- On Windows, run the tests from WSL2 and not from Git Bash
  - Git for Windows checks out `.sh` files with CRLF line endings when
    `core.autocrlf=true`, and a script with CRLF fails inside a Linux container
    with "not found"
    - Keep LF for these files in `.gitattributes`:
      ```text
      *.sh text eol=lf
      bashrc text eol=lf
      etc_sudoers text eol=lf
      ```
  - Git for Windows does not create symlinks by default, so files linked from
    `helpers_root/` (e.g., `conftest.py`, `pyproject.toml`) become plain text
    files and `pytest` fails to start

## Example

- `research/Causal_Analysis_of_Agent_Skill_And_Luck/test/test_docker_all.py` in
  `gpsaggese/gpsaggese.github.io` runs the notebooks and the unit tests of the
  project
  - Added in
    [gpsaggese/gpsaggese.github.io#734](https://github.com/gpsaggese/gpsaggese.github.io/pull/734)
  - It uses the older `helper()` method, which was renamed to `run_notebook()`
