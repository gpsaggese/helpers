# Cleanup Glossary

- **Goal**: the meaning of the terms used in the docs of the cleanup and in the code
  that it changes

| Term                    | Meaning                                                                                                    |
| :---------------------- | :--------------------------------------------------------------------------------------------------------- |
| Causify                 | The company inside which `helpers` grew; its names are the target of the rename theme                      |
| CK                      | CryptoKaizen, the other company name in the code, e.g., the `requires_ck_infra` marker, `s3://cryptokaizen-*` |
| `CSFY_*`                | The prefix of the Causify env vars, e.g., `CSFY_ECR_BASE_PATH`                                             |
| Thin environment        | The small Python venv on the host that runs `invoke` and Docker, built by `thin_client/build.py`           |
| Thin client             | Another name of the thin environment, used in the dir `dev_scripts_helpers/thin_client/`                    |
| Dev container           | The Docker container, built from `dev.Dockerfile`, where the code, the tests, and the linters run          |
| Dev image               | The image of the dev container, e.g., `helpers:dev`                                                        |
| Prod image              | The image built from `prod.Dockerfile` on top of the dev image, e.g., `helpers:prod`                       |
| Docker-in-Docker (DinD) | A Docker engine that runs inside the dev container; the container needs `--privileged`                     |
| Sibling containers      | Containers that the dev container starts on the Docker engine of the host, through its socket              |
| Dockerized tool         | A tool that the code runs in its own container, e.g., Mermaid, PlantUML, Pandoc                            |
| GHCR                    | GitHub Container Registry, `ghcr.io`, the image registry that stays                                        |
| ECR                     | AWS Elastic Container Registry, the image registry that the cleanup removes                                |
| ECS                     | AWS Elastic Container Service; `tasks.py` creates ECS task definitions for it                              |
| S3                      | AWS object storage; `repo_config.yaml` lists Causify S3 buckets                                            |
| `moto`                  | A Python library that fakes AWS services in the tests                                                     |
| Poetry                  | The Python package manager that the image build uses today                                                 |
| `uv`                    | The Python package manager that replaces Poetry                                                           |
| Lock file               | The file that pins the version of every Python package, `poetry.lock` today and `uv.lock` after            |
| `repo_config.yaml`      | The config of a repo that the invoke tasks read, e.g., the image name and the registries                   |
| Downstream repo         | A repo that includes `helpers` as the submodule `helpers_root` and links some of its files                 |
| `helpers_root`          | The path of the `helpers` submodule inside a downstream repo                                               |
| `linters/`              | The old linter framework, which the cleanup removes                                                        |
| `linters2/`             | The linter framework that stays                                                                            |
| Commit gates            | The checks that `git commit` runs, through `pre-commit.py`                                                 |
| Theme                   | A group of PRs of the plan with one component letter, e.g., `B` for build and CI                           |
| Migration note          | The part of a PR description that tells the downstream repos what was renamed or removed and the replacement |
