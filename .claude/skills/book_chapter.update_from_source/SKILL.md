---
description: Update a book's content to match changes in its source file
model: opus
---

# Goal
- Given a book content file `<TARGET>` (markdown or tex) and its source file
  `<SOURCE>`, find the changes in `<SOURCE>` and incorporate them into `<TARGET>`

# Workflow

## Read the Version Header
- `<SOURCE>` has a header with the Git hash and timestamp of the material used to
  generate the current `<TARGET>`
  - E.g.,
    ```text
    % git_hash=<GIT_HASH>, timestamp=<TIMESTAMP>
    % <SOURCE>
    ```
  - E.g.,
    ```text
    % git_hash=f15bc6b9, timestamp=2026-07-15 14:41:12 EDT
    % book_springer/lectures_source/Lesson02.1_From_Data_Science_To_Decision_Science.txt
    ```
- Get the diff of `<SOURCE>` since `<GIT_HASH>` once, up front, not per section:
  ```bash
  > git diff <GIT_HASH> -- <SOURCE>
  ```

## Incorporate Changes
- Modify `<TARGET>` to reflect every change in `<SOURCE>` since `<GIT_HASH>`
- Follow the style of `<TARGET>`, reading the matching `.claude/skills/*.rules.md`
- `<TARGET>` may be a superset of `<SOURCE>`. A `.typ` chapter routinely adds
  headings, diagrams, or paragraphs that group or expand several flat `.smd` slides
  (see "Structural Hierarchy" in `typst.rules.md`)
  - If `<SOURCE>` drops a heading or diagram that `<TARGET>` built on, keep the
    `<TARGET>` content, since it has no direct counterpart anymore
  - Remove it only if the diff shows the underlying fact or example was changed or
    retracted, not merely reorganized out of the slide deck
- Update the header at the top of `<TARGET>` to the new hash and timestamp:
  ```text
  // git_hash=<NEW_GIT_HASH> timestamp=<NEW_TIMESTAMP>
  ```

## Compare Entire Flow
- Make the flow of `<TARGET>` (typst, latex, or md) follow the flow of `<SOURCE>`
- E.g., run `extract_toc_from_txt.py` on both files and compare
  ```bash
  > extract_toc_from_txt.py -i msml610/lectures_source/Lesson03.3-Non_classical_logics.smd

  > extract_toc_from_txt.py -i msml610/book/Lesson03.3-Non_classical_logics.typ
  ```
- Ensure the flow of `<TARGET>` is consistent with `<SOURCE>`

## Update Source-Line References
- A `.typ` `<TARGET>` has a `// From: <SOURCE>:<LINE> '<slide title>'` comment above
  each section, pointing to the exact `<SOURCE>` line it was generated from
- An edit above a slide shifts every later line number. After incorporating the
  changes, walk the `// From:` comments top to bottom and fix each `<LINE>` so it
  matches the slide's current position in `<SOURCE>`
  - Find a slide by grepping `<SOURCE>` for its `*` or `#` title

## Update Rendered Images
- If the diff changes a `graphviz`/`mermaid`/`tikz`/... code block (new styling, new
  nodes, or a static image swapped for a rendered diagram, or vice versa), carry the
  same change into the matching `rendered_images:begin`/`rendered_images:end`
  placeholder in `<TARGET>` (see "Diagram Placeholders and `wrap-content`" in
  `typst.rules.md`)
- Never edit the numbered `.png` files (`<Chapter>.typ.figs/<Chapter>.<N>.png`)
  or the `#figure(image(...))` calls by hand for content that already renders
  correctly. `render_images.py` regenerates both on the next render
- If a section gains or loses a rendered figure, every later `<N>` shifts. After
  editing the placeholders, grep `<TARGET>` for `\.typ\.figs/.*\.[0-9]+\.png` and
  renumber every `#figure(image(...))` call, and its matching `label=`/`caption=`
  line, sequentially from 1 in document order
- Carry caption or label wording changes like prose. If the diff renames or rewords
  what a diagram depicts, update the figure's `caption=`/`caption:` per "Figures:
  Required Elements" in `typst.rules.md` (sentence case, one plain line, no
  node-by-node listing)

# Verification
- [ ] Confirm every change in `<SOURCE>` since `<GIT_HASH>` is reflected in
      `<TARGET>`
- [ ] Confirm `<TARGET>` still follows the style of its `.claude/skills/*.rules.md`
      (`typst.rules.md`, `latex.rules.md`, or `markdown.rules.md`)
- [ ] Confirm `<TARGET>` compiles
  - For `.typ`, use `render_book_chapter.py -i <TARGET>` if Docker and graphviz work
  - Lighter syntax-only check without Docker. It avoids the image-tagging bug of
    `render_book_chapter.py` and re-rendering of sibling `.typ` files under a
    running `gen_slides.py --daemon`: stub the unrendered figure PNGs, then compile
    ```bash
    > typst compile --root . <TARGET> /tmp/check.pdf
    ```
  - After either check, `git status`/`git diff` the whole book directory, not just
    `<TARGET>`, to catch side effects on sibling chapters
- [ ] Confirm every `// From: <SOURCE>:<LINE>` comment points to the current line
      in `<SOURCE>`
- [ ] Confirm every figure's numbered `.png` filename is sequential in document
      order, with no gaps or duplicates
