---
description: Write a practical tutorial for engineers covering one tool or concept
model: opus
---

# Goal

- Write clear, hands-on tutorials that help engineers quickly learn a new tool,
  technique, or concept
- Tutorials should be practical and immediately applicable, not theoretical surveys

# Audience

- **Target**: Software engineers and technical practitioners
- **Skill level**: General to intermediate (some programming knowledge assumed)
- **Goal**: Readers can use the tool or technique effectively after reading

# Tutorial Structure

- Follow this outline:

  1. **Introduction** (1-2 paragraphs)
     - What is this tool or concept? Why should engineers care?
     - When to use it (not just "always") and which tools solve similar problems
     - Links to official docs: installation, documentation, tutorial

  2. **Prerequisites** (if any)
     - Required knowledge or tools

  3. **Installation/Setup** (if applicable)
     - Clear, copy-paste ready commands
     - Verify the installation with a simple test

  4. **Core Concepts** (1-2 paragraphs)
     - Explain 2-3 key ideas

# Guidelines

## Length
- Target 10-15 minutes of reading time (roughly 1500-2500 words)
- Focus on the 80% use case. Avoid covering everything

## Template
- Use `website/docs/blog/posts/draft.blog_template.md` as template

## Code Examples
- Use copy-paste ready code blocks, with `bash` or language-specific highlighting
- Include expected output, so readers know it worked
- For shell commands, show the prompt style, e.g.,
  - On macOS and Linux using the official installer:
    ```bash
    > curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Platform Coverage
- Focus on macOS and Linux

## Tone & Voice
- Direct and practical ("use this when..." not "one might consider...")
- Active voice, short sentences
- Assume busy engineers. Do not be overly casual

## Visuals
- Include diagrams only if they clarify workflow or architecture
- Use simple mermaid or graphviz diagrams, or external images, if needed
- Do not over-decorate

## Formatting
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Examples to Reference
- Located in `website/docs/blog/posts/`. Study them for structure, tone, depth, and
  length
  - `website/docs/blog/posts/in_30_mins.uv.md`: tool intro, install, core concepts
  - `website/docs/blog/posts/in_30_mins.ripgrep.md`: search tool, use cases
  - `website/docs/blog/posts/in_30_mins.Python_Packaging.md`: concept, with workflow
  - `website/docs/blog/posts/in_30_mins.mdm_unified_markdown_manager.md`:
    multi-tool tutorial

# Verification
- [ ] Confirm the tutorial reads in 10-15 minutes (see `## Length`)
- [ ] Confirm every code block has a language tag and shows expected output
- [ ] Confirm the tutorial follows `.claude/skills/markdown.rules.md` and
      `.claude/skills/text.rules.md`
