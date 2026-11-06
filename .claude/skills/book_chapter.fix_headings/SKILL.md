---
description: Fix Typst book chapter headings and slide titles to match its .smd source
model: sonnet
---

# Goal

- Given a lecture's `.smd` source and its generated `.typ` book chapter (from
  `gen_book_chapter.py --mode typst_aima`), fix the heading levels and slide-title
  handling to follow the "Structural Hierarchy" rule in
  `.claude/skills/typst.rules.md`
- Mostly mechanical (moving `=`/`==`/`===` markers). A slide title that must become
  a transition (see Step 3) needs one reworded sentence. That is the only text this
  skill may change. The rest of the prose stays untouched
- A fix-up for chapters generated before that rule existed, or hand-edited
  inconsistently. On a chapter that already follows the rule, it is a no-op

# Inputs

- `<SMD_FILE>`: the lecture source
  - E.g., `msml610/lectures_source/Lesson02.1-A_Map_of_Machine_Learning.smd`
- `<TYP_FILE>`: the generated book chapter for `<SMD_FILE>`
  - E.g., `msml610/book/Lesson02.1-A_Map_of_Machine_Learning.typ`

# Workflow

## Classify Every Heading/slide in `<SMD_FILE>`

- Walk `<SMD_FILE>` top to bottom, collecting every `#`/`##`/`###`(+) heading line
  and every `* Slide Title` line, in source order, with its line number
- Track one running flag, `seen_subheading`, starting `False`: flip it to `True` the
  first time a `##` or deeper heading is seen. Its value when each `* Slide Title`
  line is reached (before any `##` on the same line updates it) is what Step 3
  needs for that slide

## Locate the Matching Line in `<TYP_FILE>`

- `<TYP_FILE>` carries a
  ```text
  // From: <SMD_FILE>:<LINE_NUMBER> '<MARKER> <TITLE>'
  // Slide: <TITLE>
  ```
  comment immediately above every heading/slide it was generated from.
  Match each Step 1 entry by line number + marker, not by title alone, since titles
  can repeat (e.g., a lesson and its own first slide sharing a name)
- The heading/title line itself is the next non-comment line after
  `// Slide: <TITLE>`: it may currently be `#strong[Title]`, `= Title` / `== Title`
  / `=== Title`, or missing entirely (the block's paragraph starts right after the
  comment, no title line at all)

## Apply the Rule From `typst.rules.md`

// TODO(ai_gp): Make reference to the typst.rules.md instead of this wall of text
For each block from Step 2, make its title line match the `## Structural Hierarchy`
and `## Mandatory Sections` rules in `typst.rules.md`. This skill decides *which*
rule applies to each block. The rules define the heading syntax:
- **H1** (`#`), title equal to the chapter title in `#chapter(...)` (the common
  case: one `#` per lesson): delete the title line, keep the `// From:`/`// Slide:`
  comments. If a body-level H1 has _different_ text, check for `##`/`###` under it
  before the next `#` (or end of document). With no nested subsections, use
  `#strong[Title]` instead of deleting it. With nested `##`/`###` subsections (e.g.,
  a lesson combining two topics, each `# Topic` with its own `##` subsections), keep
  a real `= Title` heading, since `typst.rules.md` forbids `#strong` in place of a
  heading. If unsure, cross-check `extract_toc_from_txt.py -i <SMD_FILE>` vs
  `grep "^=" <TYP_FILE>`
- **`##`/`###`/deeper**: apply the `## Structural Hierarchy` heading-level mapping.
  Leave alone if already correct
- **`* Roadmap`**, **`* Summary`**, **`* References`**: always the mandatory level-1
  headings per `## Mandatory Sections`, whatever `seen_subheading` is. The
  `seen_subheading` rule below covers ordinary slides only and never applies to them
- **`* Slide Title`** (any other slide):
  - `seen_subheading` was `False` -> `= Title`, a real heading (add the line if
    missing, replace `#strong[Title]` or a transitioned-in paragraph)
  - `seen_subheading` was `True`, and this is the first slide since that heading
    (no other `* Slide Title` block since) -> drop the title: no `#strong[Title]`
    line, no added transition. Delete a `#strong[Title]` line if present (and the
    blank line after it). The paragraph opens with its own first sentence, directly
    after the `// Slide:` comment
  - `seen_subheading` was `True`, and at least one other slide appeared since that
    heading -> drop the title and transition in from the previous slide's ending
    instead of restating the title:
    - Read the previous block's last sentence and this block's first sentence
    - If the previous sentence already works as a lead-in (a forward reference, a
      rhetorical question, a "this raises the question of X" close) and the
      paragraph's opening picks it up, deleting the title line is enough
    - Otherwise, prepend one short sentence (or reword the first clause of the
      opening sentence) that connects the two: a callback to the previous slide's
      last term or claim, a contrast ("beyond X, a second axis is..."), or an
      explicit bridge. Keep it to one sentence. Do not summarize or repeat what the
      paragraph says next
    - A slide's central term may get `#strong[...]` inside the transition or the
      first sentence, never on its own line
  - Either way, remove the blank line between the title line and the body: the
    comment block is followed directly by the paragraph (see the "Good" examples in
    `typst.rules.md`)
Never touch `#strong[...]`/`#emph[...]` elsewhere in the prose (mid-paragraph terms,
list lead phrases). Never touch sentences beyond the first of a transitioned-in
paragraph. Only the title lines from Step 2 and the opening sentence next to them
are in scope

# Verification

- [ ] Lint the file: `typstyle --inplace --wrap-text -l 85 <TYP_FILE>`
- [ ] Compile and check the PDF looks right: see
      `.claude/skills/book.fix_rendered_pdf/SKILL.md`
- [ ] Confirm no prose beyond the in-scope title lines and their opening
      sentence was changed
