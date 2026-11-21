---
description: Update research/ideas/README.md tracking table from idea files
model: haiku
---

# Goal
- Update `research/ideas/README.md` to reflect the current content of
  `research/ideas/*.md`

# Workflow

## Find the Files to Process
- Extract `<TIMESTAMP>` from the comment at the end of `research/ideas/README.md`,
  e.g. `// Last update timestamp: "Aug 3 10:54"`
- Find every `research/ideas/*.md` file modified or added after `<TIMESTAMP>`, or
  with no row in the table yet
- Build the list of those files, `<FILES>`

## Read the Template
- Read `.claude/templates/research_idea.template.md` to learn what each idea file
  should contain

## Update the Table
- For each file in `<FILES>`, add or update its row in `research/ideas/README.md`
  using the column order:
  `| File | Links | Status | Assignee | Specs Complete | GitHub Issue | Result |`
- Fill each column from the file content and status prefix, as well as you can
- Sort all rows by descending `Specs Complete`

## Update the Timestamp
- Set the `// Last update timestamp: "..."` comment at the end of the file to the
  current timestamp

# Conventions
- Follow `.claude/skills/research_idea.rules.md`

# Constraints
- Only touch rows of files in `<FILES>`. Re-sorting the table is the only change
  allowed to other rows
- Do not remove a row for a file that still exists in `research/ideas/*.md`

# Verification
- [ ] Every file in `<FILES>` has a row in the table
- [ ] Rows are sorted by descending `Specs Complete`
- [ ] The `// Last update timestamp: "..."` comment reflects the current time
