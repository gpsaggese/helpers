---
description: Polish a TikZ, SVG, Graphviz, or Mermaid figure into a professional one
model: sonnet
---

# Goal
- Take an existing figure (`<FILE>.tex`/TikZ, `<FILE>.svg`, `<FILE>.dot`/Graphviz,
  or `<FILE>.mmd`/Mermaid) and polish it into a publication-quality figure using
  the project's figure conventions
- Prove the improvement with a before/after image

# Workflow

## Identify the Figure Type
- `.tex` (TikZ/LaTeX source): apply `.claude/skills/tikz.rules.md`
- `.svg` (SVG source): apply `.claude/skills/svg.rules.md`
- `.dot`/`.gv` (Graphviz source): apply `.claude/skills/graphviz.rules.md`
- `.mmd`/`.mermaid` (Mermaid source): apply the `## Mermaid Graph` section of
  `.claude/skills/figure.rules.md`
- All four types share the cross-diagram `## Color Palette` in
  `.claude/skills/figure.rules.md`
- If unsure which rules apply, inspect the extension and content first. Never mix
  rule sets on one figure

## Render the Original (Before)
- Render the figure as given, with no edits, to `before.png`
  - TikZ:
    ```bash
    > dev_scripts_helpers/dockerize/dockerized_tikz_to_bitmap.py \
        -i <FILE>.tex -o before.png
    ```
  - SVG:
    ```bash
    > inkscape <FILE>.svg --export-type=png --export-filename=before.png
    ```
  - Graphviz:
    ```bash
    > dot -Tpng <FILE>.dot -o before.png
    ```
  - Mermaid:
    ```bash
    > mmdc -i <FILE>.mmd -o before.png
    ```
- Keep this file untouched. It is the baseline for the final comparison

## Apply the Rules
- Read the relevant rules file in full. Edit the source to follow every section,
  especially:
  - Layout & spacing (grid alignment, no cramped or overlapping elements; for
    Graphviz: rank/cluster alignment)
  - Color system (restrained, semantic palette; no raw saturated colors; use the
    shared palette in `figure.rules.md` unless the rules file gives a more
    specific one, e.g., Graphviz's flat/architecture color tables)
  - Typography (label-size hierarchy, sentence case, consistent font)
  - Strokes & geometry (consistent line weights and arrowheads/corners; for
    Graphviz: edge style semantics; for Mermaid: the required `%%{init: ...}%%`
    theme directive)
  - The "What NOT to Do" anti-pattern list at the end of the rules file
    (Graphviz/Mermaid have none: follow every section above instead)
- Do not change the figure's meaning or content. Change only its visual execution

## Render the Result and Iterate
- Re-render to `after.png` with the same command, swapping the output name
  (`-o after.png` / `--export-filename=after.png`)
- Inspect `after.png`. If it still breaks a rule (cramped spacing, overlapping
  labels, inconsistent strokes, non-semantic colors), fix the source and
  re-render. Repeat until the figure is professional per the rules

## Compare Side by Side
- Build one image with the before and after panels side by side, and open it:
  ```bash
  > montage before.png after.png -tile 2x1 -geometry +10+10 -label '%f' comparison.png
  > open comparison.png
  ```

# Verification
- [ ] `comparison.png` opened and shows `before.png` and `after.png` clearly
      labeled side by side
- [ ] `after.png` has no unresolved violation from the rules file applied above
- [ ] The figure's content and meaning are unchanged. Only styling improved
