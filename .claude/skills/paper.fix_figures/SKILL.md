---
description: Add labels, captions, and text references to every figure in a LaTeX paper
model: haiku
---

# Goal

- Add labels, captions, and text references to every figure in the LaTeX files of
  the passed dir

# Workflow

- Follow the section `# Figures and Tables` of `.claude/skills/paper.rules.md`

# Verification

- [ ] Every figure and table has a `\label` and a `\caption`
- [ ] Every figure and table `\label` is referenced by a `\ref` in the text
- [ ] No orphaned `\ref{fig:xxx}` or `\ref{tab:xxx}` exists without a matching
      `\label` in any figure or table environment
