---
description: Make sure that the PDF rendered from a Typst file looks good
model: haiku
---

# Goal

- Make sure the book chapter from `<TYP_FILE>` compiles and its PDF looks good

# Inputs

- `<TYP_FILE>`: Typst file
  - E.g., `msml610/book/Lesson01.2-AI_and_Machine_Learning.typ`

# Workflow

## Generate the PDF

- Create the PDF from `<TYP_FILE>`:

  ```bash
  > run_typst.py -i <TYP_FILE>
  ```

- The PDF goes in the same dir as `<TYP_FILE>`
  - E.g., `msml610/book/Lesson01.2-AI_and_Machine_Learning.pdf`

## Check the Typst Source Code

- Make sure the Typst file follows `.claude/skills/typst.rules.md` and
  `.claude/templates/typst.template.typ`

## Check the PDF

- Read `<PDF_FILE>` and check the layout of each page:
  - Figures are readable and not too small
  - No excessive space around a figure, caused by poorly wrapped text
- If there are visual problems, change the Typst file without changing the text.
  Regenerate the PDF (see `## Generate the PDF`) until it looks good

# Verification
- [ ] Confirm the Typst file follows `.claude/skills/typst.rules.md` and
      `.claude/templates/typst.template.typ`
- [ ] Confirm every page's figures are readable and not too small
- [ ] Confirm there is no excessive space around a figure from poorly
      wrapped text
