---
description: Create a competitor matrix and reference list from a VC pitch
model: opus
---

# Goal
- Given a VC pitch deck in smd format, create `competitors.md` next to it, then
  append a list of references at the end of the file
  - The file rates each competitor on the capabilities that the deck claims as its
    edge
  - The references summarize every source behind the deck and behind the file
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
- Follow the template `.claude/templates/vc_slides_competitors.template.md`
- The deck comes from `.claude/skills/vc_pitch.write_slides/SKILL.md`

# Workflow

## Role
- Act as a VC analyst who does competitive due diligence for an investment committee
  - The committee looks for a competitor that already does what the deck says nobody
    does
  - A rating that favors the company without proof is a defect

## Input
- The user provides:
  - `<PITCH_FILE>`: the slides file, e.g.,
    `papers/Noesis/business/vc_pitch.slides.md`
    - Default: `vc_pitch.slides.md` in the current dir
    - If the file does not exist, ask the user once, then stop
  - (Optional) `<OUTPUT_FILE>`: the file to create
    - Default: `competitors.md` in the dir of `<PITCH_FILE>`
  - (Optional) `<RELATED_WORK_FILE>`: a related-work file, e.g., the state-of-the-art
    section of a paper
    - Read it to seed the competitor list and to cross-check the ratings
- Set `<PITCH_REL>` and `<OUTPUT_REL>` to the paths of the two files relative to the
  parent of the dir of `<PITCH_FILE>`
  - E.g., `business/vc_pitch.slides.md` and `business/competitors.md`
- Use only facts from the pitch and from pages read in this run

## Read Pitch
- Read the whole `<PITCH_FILE>`
- Extract:
  - `<COMPANY>`: the text before the colon in `lesson_title`
  - The product in one line, from `* Elevator Pitch` and the Solution slide
  - The competitors named in the Competition table, in its `@<COMPANY>'s position@`
    sub-bullets, and in the `@Today@` lead-in of the Solution slide
  - The columns of the Competition table
  - The `@<COMPANY>'s edge@` advantages and the `@Advantages@` bullets
  - The sellers and partners named in the go-to-market slide
  - Every source: the entries of `* Sources` and each `(<PUBLISHER>, <YEAR>)`
    citation in the slide text
- Write a placeholder such as `\<FEE\>` of the pitch as `` `<FEE>` `` in the output

## Choose Capabilities
- Derive 4-6 capabilities from the pitch
  - One per Competition table column, after the first column
  - One per edge advantage that a competitor could also claim
  - Merge capabilities that test the same thing
- Define each capability in one bullet: what counts, and what does not count
  - E.g., metered fulfillment: delivery is measured against the bought contract, and
    a generic uptime SLA does not count
- Add a last column `Customer pays for`, with the billing unit of each row

## Find Competitors
- Start from the names found in `## Read Pitch`
- Search for more competitors in each category of the Competition table
  - Run at least 3 searches per category, with generic category terms
    - E.g., `LLM gateway`, `GPU marketplace`
  - Add each close competitor that the pitch does not name
- Add a complement as a row when the pitch cites it, e.g., a payment rail or a
  standard
  - Say `Complement` in its profile
- Put sellers and partners named in the pitch under `## Not Competitors`, with no
  profile
- Use one row per company or product
  - If the name matches another company, say which entity the row covers

## Research Competitors
- For each competitor, fetch:
  - The pricing page
  - The docs or FAQ page that describes the mechanism
  - A funding source: a press release, or a tracker such as Crunchbase or Dealroom
  - A revenue and headcount source: company statements first, then trackers
- Record the title, the year, and the URL of every page that gives a fact
  - The references need them (see `## Add References`)
- Collect for each competitor:
  - The price or fee model
  - The mechanism, for each capability of `## Choose Capabilities`
  - A scale metric with its date
  - The funding: round, amount, date, and lead investor
  - The revenue and the headcount
- Follow `## Figures` for every number
- Write `?` for a fact that no page gives. Never fill it from memory
- Delegate to subagents in parallel for a long list, one subagent per 5 competitors
  - Each subagent returns, per page: title, year, URL, and the figures read, or
    `could not read` with the reason
- Put only competitor and vendor names in search queries and URLs
  - Never put the company name, the founder names, or the pitch figures in them

## Write Competitors File
- Fill the template, in this order: `## Capabilities`, `## What They Do`,
  `## Not Competitors`, `## Company Data`, `## Notes for the Pitch`
- Order the rows by the category order of the Competition table, then by closeness
  to the company
  - Put complements last, before the company row
- Rate each cell as in `## Capability Ratings`
- Write 3-5 bullets per competitor under `## What They Do`
  - What it is, how it charges, a scale metric with its date
  - Last bullet: how it differs from the company, e.g., `Substitute`,
    `Closest incumbent`, `Complement`
- Write the company row from the pitch
  - Yes in every capability, since the capabilities come from its edge
  - The fee from the Business Model slide, the ask from the Ask slide, the traction
    from the Traction slide, and the team size from the Team slide
- Write `## Notes for the Pitch`
  - The main incumbent, and the recent events that changed its position
  - The closest competitor for each capability
  - The complements
  - One `TODO(gp)` per conflict between a slide and a finding
    - E.g., the Competition table says `None` for a penalty, but a competitor pays
      SLA credits
  - Do not edit `<PITCH_FILE>`
- If `<RELATED_WORK_FILE>` rates a competitor differently, add a `TODO(gp)` with both
  ratings

## Add References
- Append `# VC Pitch References` at the end of `<OUTPUT_FILE>`, as in the template
- List, in this order:
  - Every source of the pitch, in the order of its `* Sources` slide
  - Every vendor page that gives a fact to the file, in the row order of the
    capability table
- Write one `##` entry per URL
  - **Title**: the title of the page. Add the vendor in parentheses when the title
    does not name it
  - **Year**: the year of publication. For an undated page, the year it was read
  - **Link**: `[<SHORT_NAME>](<URL>)`, with the publisher and the topic in the name
  - **Key points**: see `## Key Points`
- Read each page with a web fetch. Never summarize from a search snippet or from
  memory
- For a page that cannot be read (HTTP error, login wall, paywall, empty page),
  replace `Key points` with `- **Not read**: <REASON>`
  - Write no summary for it
- If only a mirror of a page was read, link the mirror and say so in a key point
- Do not list local files such as `<RELATED_WORK_FILE>`
- Do not write a `## Sources` list of bare URLs. The references carry every link

## Save Result
- Write `<OUTPUT_FILE>` in one write, after the research
- If `<OUTPUT_FILE>` exists, ask the user before changing it, with two options
  - Rebuild the whole file
  - Replace only the references and keep every other section
    - Take the vendor URLs from `## Sources` and from the bare URLs of the file
    - Replace an old `# VC Pitch References` with the new one
    - Remove `## Sources` only after each of its URLs has a reference
    - Do not add the `Generated by` line, since the skill did not create the file

## Report
- Do not print the file on screen
- Print:
  - The path of `<OUTPUT_FILE>`
  - The number of competitors and the number of references
  - The references with `Not read`
  - The list of `TODO(gp)` comments

# Conventions

## Capability Ratings
- Use only `Yes`, `Partial`, `No`, and `?`
- **Yes**: a page of the vendor docs or pricing shows the feature as core
  - A claim on a landing page alone is company-reported: rate `Partial`
- **Partial**: the feature exists but is limited, manual, or not guaranteed
- **No**: the pricing, docs, and FAQ pages show no such feature
- **?**: the pages cannot be read, or they are silent
- **Bad** (a generic uptime SLA rated as metered fulfillment)
  ```text
  Metered fulfillment: Yes
  ```
- **Good** (the definition says that an uptime SLA does not count)
  ```text
  Metered fulfillment: No
  ```

## Figures
- Write dates as `YYYY-MM` or `YYYY-MM-DD`
- Write money as `$153M` or `$1.3B`, and a price in the unit of the vendor
- Label each revenue, headcount, and scale figure with its source
  - `(company-reported)`
  - `(<TRACKER> est.)`, e.g., `(Sacra est.)`
- Give a range and add `(conflict)` when two sources differ
- Write funding as round, amount, date, and lead investor
- Write `?` for an unknown figure

## Key Points
- Write 2-6 sub-bullets per source
- Start each sub-bullet with a bold label of 1-2 words that names the facet
  - E.g., `Reply rate`, `Pricing`, `Funding`
- State each figure with its scope as the source gives it: sample, period, and unit
- Cover every figure that the pitch or the file takes from the page
- Paraphrase the page. Quote at most 15 words in a row
- **Bad** (no figure, no scope, from memory)
  ```markdown
  - **Reply rate**: very low
  ```
- **Good** (figure with sample and period)
  ```markdown
  - **Reply rate**: 0.45% on average, from 7,530,489 cold emails and 34,393 replies
    sent from January to December 2025
  ```

# Constraints
- Every figure comes from a page read in this run, or is `?`
- Never edit `<PITCH_FILE>`: report conflicts as `TODO(gp)` in the notes
- Never put the company name, the founder names, or the pitch figures in a search
  query or in a URL
- Wrap prose at 85 characters. Tables and URLs are exempt
- No hype words, no emoji, no non-ASCII characters, no `---` separators
- No period at the end of a bullet

# Verification
- [ ] The generated file has the line `Generated by <SKILL_FILE>` as its first
      bullet, with `<SKILL_FILE>` set to
      `.claude/skills/vc_slides.create_competitor/SKILL.md`
  ```bash
  > sed -n 1,3p <OUTPUT_FILE>
  ```
- [ ] The two tables list the same competitors as the `###` profiles
  ```bash
  > sed -n '/^## Capabilities/,/^## What They Do/p' <OUTPUT_FILE> | grep -c '^| '
  > sed -n '/^## Company Data/,/^## Notes for the Pitch/p' <OUTPUT_FILE> | grep -c '^| '
  > grep -c '^### ' <OUTPUT_FILE>
  ```
  - The two table counts are equal, and each equals the `###` count plus 2
- [ ] Every competitor in the Competition table of `<PITCH_FILE>` has a row
- [ ] Every URL in `<PITCH_FILE>` appears in `<OUTPUT_FILE>`
  ```bash
  > grep -oE 'https?://[^ )`]+' <PITCH_FILE> | sort -u
  ```
- [ ] Each reference has a year, a link, and either key points or `Not read`
  ```bash
  > awk '/^# VC Pitch References$/{f=1} f && /^## /' <OUTPUT_FILE> | wc -l
  > awk '/^# VC Pitch References$/{f=1} f && /^- \*\*Year\*\*/' <OUTPUT_FILE> | wc -l
  > awk '/^# VC Pitch References$/{f=1} f && /^- \*\*Link\*\*/' <OUTPUT_FILE> | wc -l
  > awk '/^# VC Pitch References$/{f=1} f && /^- \*\*(Key points|Not read)\*\*/' \
      <OUTPUT_FILE> | wc -l
  ```
  - The four counts are equal
- [ ] Every URL of the file appears in a reference link
- [ ] Each revenue, headcount, and scale figure has a source label
- [ ] Each conflict between the pitch and a finding has a `TODO(gp)` in the notes
- [ ] The file has no non-ASCII character
  ```bash
  > LC_ALL=C grep -n '[^ -~]' <OUTPUT_FILE>
  ```
