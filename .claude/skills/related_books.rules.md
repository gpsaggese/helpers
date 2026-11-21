- Rules for the file `related_books.md`, which lists the books related to the content
  of a directory
- Follow the template `.claude/templates/related_books.template.md`
- Create or update the file with `.claude/skills/related_books.create/SKILL.md`

# File

## One File per Directory

- Name the file `<DIR>/related_books.md`
  - One file covers all the books related to the content of `<DIR>`
  - Put it in the dir that holds the content, not in a parent dir
- Do not keep the books of one dir in several files
  - **Bad**: `book_list.md`, `books.md`, and `related_books.md` in one dir
  - **Good**: one `related_books.md`
- If the file covers only part of the dir (e.g., one lesson), say it in the `Scope`
  tag
- List only books
  - Put papers in `related_papers.md`
  - Put Python packages in `related_python_packages.md`
  - Do not list a topic, a framework, or a web page as a book, e.g., "Business Model
    Canvas"

## Single Source of Truth

- The book sections hold the data
- The tables `Topic Clusters` and `Book Summary` summarize the book sections
  - Regenerate the tables from the sections
  - Do not add a book or a score to a table only

## Other Files that Name Books

- A `book_map.md`, a `resources.md`, or a slide file can keep its own short list of
  books for a chapter
  - Keep the `ID` of the book in that list, so that it points to this file
- Do not delete `book_info.md` and `book_info.tsv`
  - The skill `.claude/skills/book_list.gather_info/SKILL.md` generates them
  - Merge their rows into `related_books.md`

# Structure

## Headers

- Use one `#` title: `# Related Books: <DIR_TOPIC>`
- Use `##` for `Rating Scales`, `Topic Clusters`, `Book Summary`, and each cluster
  - Write the cluster header as `## Cluster <N>. <CLUSTER_NAME>`
  - Number the clusters from 1, in order
- Use `###` for each book
  - Write the title of the book, with the subtitle if the cover has one
  - If two books have the same title, add the last name of the first author
    - E.g., `### Causal Artificial Intelligence (Hurwitz)`
- Do not use `####`

## Order

- Order the clusters from foundational topics to applied topics
  - Keep the order of the source file when it already has a logical order
- Order the books inside a cluster by year, newest first
  - Put forthcoming books first
  - Put the books with `n/a` year last
  - Break ties alphabetically by title
- Make the tables follow the same order

## One Cluster per Book

- Put each book in exactly one cluster: the cluster of its primary topic
- Show the other uses of the book in its `Alternatives` and `Lessons`
- Use 3 to 12 clusters
  - Name each cluster with a short noun phrase
  - Write the topic of the cluster in one line

# Book Fields

## Field Order

- Write the fields of a book in this order, as bold tags:
  - **ID**
  - **Authors**
  - **Year**
  - **Publisher**
  - **Link**
  - **Technical**
  - **Scores (1-10)**
  - **Lessons**
  - **Relevance**
  - **Content**
  - **Caveats**
  - **Alternatives**
- Do not add other fields
- Always write `ID`, `Authors`, and `Year`
- Omit any other field that has no known value
  - Do not write a placeholder, e.g., `Publisher: n/a`
  - The table `Book Summary` shows `n/a` for a missing value
  - Drop a column of the table when all its values are `n/a`

## ID

- Write `B<NNN>`, with 3 digits, e.g., `B007`
- Keep the IDs unique inside the file
  - IDs are local to a file, so `B001` in two dirs is two different books
- Never change or reuse an ID of an existing book
  - Other files, e.g., `book_map.md`, point to the ID
- For a new file, number the books from `B001`, in the order of the sections
- When two IDs name the same book, write both: `B027/B054`

## Authors

- Write the full names, separated by commas, e.g., `Judea Pearl, Dana Mackenzie`
  - Do not use `and` or `&`
- Write `<Name> et al.` only when the source gives a partial list and the full list is
  not found
- Do not shorten the names to the format of `references.rules.md`, which is for
  running text
- If an old list gives only last names, e.g., `Pearl et al.`, copy them as they are
  - Fill the full names when you update the file, with the page of the publisher

## Year

- Write one of these values:
  - `<YYYY>`: the year of the edition that the project uses
  - `<YYYY> (forthcoming)`: the book is not published yet
  - `<YYYY> (not confirmed)`: the sources disagree, or the year is not checked
  - `n/a`: the year is not known

## Publisher and Link

- `Publisher`: the name of the publisher, e.g., `O'Reilly Media`
- `Link`: a public page of the book
  - Prefer the page of the publisher, the author, or a free full text
  - Check each URL before writing it
  - If you cannot check a URL, add ` ???` after it
  - Do not copy a URL from another list without checking it

## Technical

- Write `Yes` for a technical book, otherwise `No`

## Scores

- Write one line, with the scales of `Rating Scales`:
  ``- **Scores (1-10)**: Goodreads 6.6, Reviews 4, Academic 4, Practical 8, Clarity 7, Average 5.9``
- Use `n/a` for a score that cannot be found
- Compute `Average` as the mean of the scores that are not `n/a`
- Collect the scores with `.claude/skills/book_list.gather_info/SKILL.md`
- Write the date of the collection once, in the header tag `Ratings as of`
  - Write `n/a` if no book has a score

## Lessons

- List the lesson or chapter tags that use the book, e.g., `03.2, 03.3`
- Use the tags of the lecture files in the dir
- If the dir has a `book_map.md`, use its chapter numbers and say it in the `Scope` tag

## Relevance

- Write one sentence: how the book fits the content of the dir
- Do not end the sentence with a period

## Content

- Write 2 to 6 bullets
- Take the content from the publisher page, the preface, or the table of contents
- Use a nested bullet list for a list of topics
- Do not describe what the book might cover

## Caveats

- List the limits of the book, one bullet per limit
  - E.g., dated tool coverage, mixed reviews, unchecked author
- Use the field to flag data copied from a source that you could not verify

## Alternatives

- List the `ID` of the books that solve the same need, one bullet per book
- Write only IDs that have a section in the same file
- Do not list the book itself

# Examples

## Book Section

- **Bad** (no ID, short author, free-text year, placeholders)
  ```markdown
  ### Beyond Vibe Coding

  - Author: Osmani
  - Year: ~2025
  - Publisher: n/a
  - Link: n/a
  ```
- **Good**
  ```markdown
  ### Beyond Vibe Coding: From Coder to AI-Era Developer

  - **ID**: B001
  - **Authors**: Addy Osmani
  - **Year**: 2025
  - **Publisher**: O'Reilly Media
  - **Technical**: Yes
  - **Scores (1-10)**: Goodreads 6.6, Reviews 4, Academic 4, Practical 8, Clarity 7,
    Average 5.9
  - **Content**:
    - Practical guide for experienced developers that works with any AI coding tool
  ```
