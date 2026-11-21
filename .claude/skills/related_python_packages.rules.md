- Rules for the file `related_python_packages.md`, which lists the Python packages
  related to the content of a directory
- Follow the template `.claude/templates/related_python_packages.template.md`
- Create or update the file with
  `.claude/skills/related_python_packages.create/SKILL.md`

# File

## One File per Directory

- Name the file `<DIR>/related_python_packages.md`
  - One file covers all the packages related to the content of `<DIR>`
  - Put it in the dir that holds the content, not in a parent dir
- Do not keep the packages of one dir in several files
  - **Bad**: `package_list.md`, `packages.md`, and `related_packages.md` in one dir
  - **Good**: one `related_python_packages.md`
- If the file covers only part of the dir (e.g., one lesson), say it in the `Scope`
  tag

## Single Source of Truth

- The package sections hold the data
- The table `Functionality Clusters` summarizes the package sections
  - Regenerate the table from the sections
  - Do not add a package or a star count to the table only

# Structure

## Headers

- Use one `#` title: `# Related Python Packages: <DIR_TOPIC>`
- Use `##` for the table `Functionality Clusters` and for each cluster
  - Write the cluster header as `## Cluster <N>. <CLUSTER_NAME>`
  - Number the clusters from 1, in order
- Use `###` for each package
  - Write the package name used by the project (GitHub, PyPI, or its docs)
  - Keep the case of the name, even for a name that starts in lower case
    - **Bad**: `### Z3-solver`
    - **Good**: `### z3-solver`
- Do not use `####`

## Order

- Order the clusters by the stars of their top package, highest first
- Order the packages inside a cluster by stars, highest first
  - Put the packages with `N/A` stars last
  - Break ties alphabetically
- Make the table `Functionality Clusters` follow the same order

## One Cluster per Package

- Put each package in exactly one cluster: the cluster of its primary function
- Show the other uses of the package in its `Alternatives` and `Lessons`
  - **Bad**: `HMMlearn` listed in the clusters Causal Discovery and Time Series
  - **Good**: `HMMlearn` in Time Series only

# Package Fields

## Field Order

- Write the fields of a package in this order, as bold tags:
  - **Description**
  - **GitHub**
  - **Docs**
  - **Stars**
  - **Status**
  - **Category**
  - **Lessons**
  - **Features**
  - **Alternatives**
- Do not add other fields
- Do not skip a field
  - Use `N/A` for a missing URL or a missing star count
  - Omit `Lessons` only when the dir has no lessons, or when the packages are not
    mapped to lessons yet

## Description

- Write one sentence: what the package does and why it is relevant to the dir
- Do not end the sentence with a period

## GitHub and Docs

- `GitHub`: the repo URL
  - If the project has no GitHub repo, use its primary home (Bitbucket, PyPI,
    project site) and set `Stars` to `N/A`
- `Docs`: the docs site or the homepage
  - If there is none, repeat the GitHub URL
- Check each URL before writing it
  - Do not copy a URL from another list without checking it
  - **Bad**: link `ALICE` to `https://github.com/aimacode/aima-data`, a repo of a
    different project
  - **Good**: link a package to the repo that holds its code

## Stars

- Write the count with a thousands separator, e.g., `10,700`
- Collect the count with:
  ```bash
  > gh repo view <OWNER>/<REPO> --json stargazerCount
  ```
- Prefix the count with `~` when it is an estimate that was not checked live
- Write `N/A` when the project has no GitHub repo, or the URL is an org page
- Write the date of the collection once, in the header tag `Stars as of`
  - Do not repeat the date in each package

## Status

- Use one of these values:
  - `active`: the repo has a push in the last 12 months
  - `maintenance`: no push for 12 months or more, and not archived
  - `archived`: the repo is archived
  - `not used`: the project decided not to use the package
  - `N/A`: the project has no GitHub repo, so the status cannot be collected
- Collect the data with:
  ```bash
  > gh repo view <OWNER>/<REPO> --json isArchived,pushedAt
  ```
- Do not write free text, e.g., "Less actively maintained"

## Category

- Use a label already used in
  `class_project/project_descriptions/all_projects.md`
  - E.g., `Causal AI & Reasoning`, `Visualization`
- Copy the label verbatim, including `&`, so that it matches the column of
  `all_projects.md`
- If the repo has no `all_projects.md`, reuse the labels of the other
  `related_python_packages.md` files in the repo
- Add a new label only when the dir covers a topic that the file does not have

## Lessons

- List the lesson tags that use the package, e.g., `03.2, 03.3`
- Use the tags of the lecture files in the dir

## Features

- Write 2 to 5 bullets, one capability per bullet
- Take the features from the docs or the README of the package
- Do not describe what the package might do

## Alternatives

- List the packages that solve the same problem, one bullet per package
- Write the name of a package that has a section in the same file
  - Check that each name matches the `###` header of a section
- For a package outside the file, write `<NAME>: <URL>`
- Do not list the package itself

# Examples

## Package Section

- **Bad** (free-text status, missing fields, comma-chained alternatives)
  ```markdown
  ### HMMlearn

  - Description: Hidden Markov Models with sklearn API.
  - GitHub stars: 1,600
  - Status: less actively maintained
  - Alternatives: Tetrad, gCastle
  ```
- **Good**
  ```markdown
  ### HMMlearn

  - **Description**: Hidden Markov Models with a scikit-learn API
  - **GitHub**: https://github.com/hmmlearn/hmmlearn
  - **Docs**: https://hmmlearn.readthedocs.io
  - **Stars**: 3,447
  - **Status**: maintenance
  - **Category**: Time Series & Forecasting
  - **Features**:
    - Fits HMMs with EM
    - Decodes state sequences with Viterbi
    - Samples sequences from a fitted model
  - **Alternatives**:
    - pomegranate
  ```
