---
description: Fix slide formatting: semantic tags, bold, LaTeX, punctuation, unicode, emoji
model: haiku
---

# Goal
- Given a markdown file with slides, fix formatting and add missing semantic
  tags, bold, and italic markup, without changing content or structure
- Read `.claude/skills/slides.rules.md` and apply its formatting rules strictly

# Workflow

## Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`

## What to Fix

- **Semantic tags and bold labels**: Ensure every first-level bullet starts
  with an approved `@Tag@` label
  - See `.claude/skills/slides.rules.md`, section `## Use Tags for Slide
    Sections`, for the approved tags and ordering
  - Add a missing tag when a first-level bullet has none. Do not invent a tag
    outside the approved list

- **Bold and italic emphasis**: Apply `**bold**` and `_italic_` where the
  rules call for them
  - See `.claude/skills/slides.rules.md`, sections `## Use Bold` and
    `## Use Italic`
  - When both apply to the same phrase, bold wins: see
    `.claude/skills/slides.rules.md`, section `### Emphasis Precedence: Bold
    Over Italic`

- **Unicode characters**: Replace non-ASCII characters with LaTeX equivalents
  - See `.claude/skills/slides.rules.md`, sections `## General Formatting
    Rules` and `### Symbols and Characters`

- **Emoji**: Remove emoji per `.claude/skills/slides.rules.md`, section
  `## General Formatting Rules`

- **Page separators**: Remove `---` lines per `.claude/skills/slides.rules.md`,
  sections `## General Formatting Rules` and `### Spacing and Breaks`

- **Punctuation**: Remove trailing periods from bullet point phrases per
  `.claude/skills/slides.rules.md`, section `## Slide Structure`

## Leave Structure and Content Unchanged
- Do not change the structure (titles, bullet hierarchy, div fenced blocks)
- Do not change the substantive content. Change only formatting

## Output
- Emit the improved output in markdown, wrapped to 80 columns (see
  `.claude/skills/slides.rules.md`, section `## Use 80 columns`), with no other
  comment

# Verification
- [ ] Make sure that the updated slides render correctly, e.g.,
  ```bash
  > gen_slides.py -i <FILE> --notes_to_pdf_args="--skip_action open_pdf"
  ```
