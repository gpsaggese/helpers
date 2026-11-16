---
description: Write a VC pitch deck of at most 12 slides as smd slides
model: opus
---

# Goal
- Given a company description, write a venture capital (VC) pitch deck of at most
  12 slides in smd format
- The deck covers at least: the problem, the solution, the addressable market, and
  the go-to-market plan
- Write an investment pitch, not a lecture. Follow `## Pitch Style`
- Follow `.claude/skills/slides.rules.md`, except where `# Conventions` overrides it
  (sections, `Roadmap`, `Summary`, `References`)
- Follow the slide syntax in `.claude/templates/slides.template.md`
- Follow `.claude/templates/vc_pitch_slides.template.md` for the slide order and
  the content of each slide

# Workflow

## Role
- Act as a startup founder who pitched seed and Series A investors, and as a VC
  partner who has read thousands of decks
- The audience is a VC investment committee: technical, financial, short on time,
  and skeptical
  - Each slide answers one investor question in under 30 seconds of reading

## Input
- The user provides:
  - A company description, notes, or a file `<TOPIC>`. Read the file if given
    - If there is no company description, ask the user once, then stop
  - (Optional) `<COMPANY>`: company name
    - Default: `NewCo`, with a TODO to replace the working name
  - (Optional) `<FOUNDERS>`: founder names
  - (Optional) `<ROUND>`: funding round, e.g., `Seed`, `Series A`
  - (Optional) `<ASK>`: amount raised
  - (Optional) `<NUM_SLIDES>`: number of slides, from 10 to 12
    - Default: `<NUM_SLIDES> = 12`. Outside 10-12, use the closest bound
  - (Optional) `<LOGO_PATH>`: logo path relative to the repo root
    - Default: a placeholder logo (see `## Add Logo`)
- Use only facts present in the input
  - Do not invent market sizes, revenue, customers, growth rates, or biographies
  - For each missing fact, write a `\<PLACEHOLDER\>`, with no TODO (see
    `## Flag Doubts` and `## Placeholders and Special Characters`)

## Plan Deck
- Write a one-line pitch `<TAGLINE>` of at most 15 words: the customer, the pain,
  and the outcome
  - E.g., `Cut month-end close from 10 days to 2 for mid-size finance teams`
- Fit the deck in `<NUM_SLIDES>` slides, never more than 12
  - The count includes `* Elevator Pitch`
  - The count excludes `* Sources`
- Always keep these 10 slides, the minimum deck
  - `* Elevator Pitch`
  - Problem slide
  - Solution slide: includes the product and how it works, with a diagram
  - Market slide: TAM, SAM, and SOM
  - Competition slide
  - Why now and moat slide
  - Business model slide: includes unit economics and a 3-year revenue path
  - Go-to-market slide
  - Team slide
  - Ask slide: includes the reasons to invest
- Add the Traction slide when `<NUM_SLIDES>` is 11 or 12
  - When `<NUM_SLIDES>` is 10, put the traction in one `@Traction@` lead-in on
    `* Elevator Pitch`
- Add the objection slide when `<NUM_SLIDES>` is 12 (see `## Objection Slide`)
- Do not add a slide for the product, existing alternatives, or financials, since
  the slides above already carry them
- Keep the order from `## Deck Structure`

## Add Logo
- If the user gave no `<LOGO_PATH>`, download a placeholder logo showing the company
  name
  ```bash
  > curl -sSL -o <SCRATCH_DIR>/logo.png "https://placehold.co/480x160/0B2545/FFFFFF/png?text=<COMPANY>&font=montserrat"
  > file <SCRATCH_DIR>/logo.png
  ```
  - Replace each space in `<COMPANY>` with `+` in the URL
  - Download into a new, empty `<SCRATCH_DIR>` and confirm `file` reports
    `PNG image data`
  - Copy it to `assets/images/<COMPANY>_logo_placeholder.png` and set `<LOGO_PATH>`
    to that path
  - Add a TODO to replace the placeholder with the real logo
- Never keep the default logo of `type=UMD_slides`. A university logo makes the deck
  read as a lecture

## Write Slides
- Write the metadata block first, then every slide
- Follow `# Conventions` for slide content
- Use the heading of the template slide as the title of each slide (see
  `## Slide Titles`)

## Add Visuals
- Follow `.claude/skills/figure.rules.md`
- Add at least 3 figures
  - A product or solution diagram
  - The nested TAM, SAM, SOM diagram on the market slide
  - The phase diagram on the go-to-market slide
- Put each figure or table beside its text in columns, per
  `.claude/skills/slides.rules.md` `# Visuals`
  - Use 60/40 by default
  - Use 65/35 when the text needs more room (e.g., the market slide)
  - Use 55/45 when the right column holds a table (e.g., the business model
    slide)
- Draw the product flow top to bottom, with the customer steps and the company
  steps in two side-by-side clusters, numbered in the order they happen
- Draw TAM, SAM, SOM as nested Graphviz clusters, with the beachhead as a box
  inside SOM
- Draw go-to-market phases top to bottom, with `fontsize=16` and subtitle
  `point-size="13"`, so labels stay readable in a 40% column
- Follow `.claude/skills/graphviz.rules.md` and the "Architecture Style" section of
  `.claude/templates/graphviz.template.md`
- Use a `styled-table` for numbers investors compare: competition, unit economics,
  cost sensitivity, use of funds
  - Follow `.claude/skills/slides.rules.md` `## Typst Tables`

## Flag Doubts
- A `\<PLACEHOLDER\>` is already the flag for a missing fact
  - Never add a TODO above a bullet only because it has a placeholder
  - The reader finds each gap by searching for `\<`
- Put a TODO comment right above a bullet only in these two cases
  - **Uncertain**: the bullet has a real value that is a number or claim from
    memory, a self-made estimate, or an unverified source
    ```
    // TODO(gp): Check <WHAT> : <WHY IN DOUBT>
    ```
  - **Missing, with no placeholder**: the input lacks a fact that no
    `\<PLACEHOLDER\>` can stand for, e.g., a whole table or a claim
    ```
    // TODO(gp): Provide <WHAT> : not in the input
    ```
  - Start the comment at column 0
  - Wrap a long TODO on more lines, each starting with `//` at column 0
  - Put a TODO that covers a whole slide right above the slide title
- Never indent the comment. The preprocessor strips only lines that start with `//`,
  so an indented comment renders inside the slide
- **Bad** (the placeholders already show what is missing, so the TODO repeats them)
  ```markdown
  // TODO(gp): Provide <N_REQ>, <N_BUYERS>, and <N_PAID> : not in the input
  - @Observed funnel@: \<N_REQ\> requests logged $\to$ \<N_BUYERS\> active
    buyers $\to$ \<N_PAID\> paying buyers
  ```
- **Good** (placeholders only)
  ```markdown
  - @Observed funnel@: \<N_REQ\> requests logged $\to$ \<N_BUYERS\> active
    buyers $\to$ \<N_PAID\> paying buyers
  ```

## Save Result
- Save the deck to `<OUTPUT_FILE>`
  - If the user gave an output path, use it
  - Otherwise, create `<STEM>.vc_pitch.slides.md` in the current dir
    - `<STEM>` is the input file name without extension, or `<COMPANY>` in lowercase
      with underscores
  - A deck in a course `lectures_source` dir uses the extension `.smd`
  - A standalone deck outside `lectures_source` uses `.slides.md`, which
    `class_scripts/gen_slides.py` treats as standalone
- Say in the slides file how it was generated, with this comment right after the
  metadata block:
  ```
  // Generated by `.claude/skills/vc_pitch.write_slides/SKILL.md`
  ```
- If `<OUTPUT_FILE>` already exists, ask the user before overwriting it

## Render and Check Layout
- Render the deck to `<PDF_FILE>`, which `gen_slides.py` writes next to
  `<OUTPUT_FILE>`
  ```bash
  > gen_slides.py -i <OUTPUT_FILE> --slides_engine typst --notes_to_pdf_args="--skip_action open_pdf"
  ```
- Confirm each slide fits on one page
  - `<PDF_FILE>` must have `<NUM_SLIDES> + 2` pages: the slides, the title page, and
    `* Sources`
  ```bash
  > pdfinfo <PDF_FILE> | grep Pages
  ```
- Build a contact sheet and check every page
  ```bash
  > pdftoppm -png -r 50 <PDF_FILE> <SCRATCH_DIR>/p
  > magick montage <SCRATCH_DIR>/p-*.png -tile 4x -geometry +4+4 <SCRATCH_DIR>/sheet.png
  ```
- Fix each defect, then render again
  - A slide that spills onto an extra page: cut words, inline a formula, or widen
    the text column
  - Overlapping table cells: shorten the text or raise the weight in `col-widths`
  - A placeholder missing from the PDF: escape it (see
    `## Placeholders and Special Characters`)

## Report
- Do not print the slides on screen
- Print only the paths of `<OUTPUT_FILE>` and `<PDF_FILE>`, the list of all TODO
  comments, and the list of all distinct `<PLACEHOLDER>` names to fill

# Conventions

## Metadata Block
- Start the file with this block, in this order
  ```
  // type=UMD_slides
  // course_title=<ROUND> Investment
  // lesson_title=<COMPANY>: <TAGLINE>
  // Authors=<FOUNDERS>
  // logo=<LOGO_PATH>
  // slides_engine=typst
  ```
  - E.g., `// course_title=Seed Investment` and
    `// lesson_title=NewCo: Month-end close in 2 days`
  - Escape a placeholder in `course_title` and `lesson_title`, e.g.,
    `// course_title=\<ROUND\> Investment`
    - Typst reads a bare `<ROUND>` as a label and drops it
  - Always set `Authors`. The `UMD_slides` default prints
    `Instructor: Dr. GP Saggese` on the title slide
    - List founders in the order the user gives, e.g.,
      `// Authors=Alice, Bob, Carol`
    - If the user gives no order, list operating founders first, then the
      chairman and part-time founders
    - If founders are unknown, write `// Authors=<FOUNDERS>`, unescaped, with no
      TODO comment
  - Always set `logo` (see `## Add Logo`)
- Follow `.claude/skills/slides.rules.md` `## First Slide`

## Deck Structure
- Use no `#` and no `##` header. Each header adds a "Table of Content" page, which
  makes the deck read as a lecture
- Place the slides in this order, skipping those not selected
  - `* Elevator Pitch`: the one-slide summary of the company
  - Problem slide
  - Solution slide: includes the product and how it works
  - Traction slide
  - Market slide
  - Competition slide
  - Why now and moat slide
  - Objection slide
  - Business model slide: includes the financials
  - Go-to-market slide
  - Team slide
  - Ask slide: ends with the reasons to invest
  - `* Sources`: last slide, only if the deck cites a source
- Do not add `* Roadmap`, `* Summary`, or `* References`. Use the fixed slides
  `* Elevator Pitch` and `* Sources` instead
- Follow the slide order and the content of each slide in the template
  `.claude/templates/vc_pitch_slides.template.md`
- Keep the Traction slide right after the Solution slide, even when the input has
  only a prototype or pilots
- Group the slides in 5 acts, so that each act answers one investor doubt
  - Hook: `* Elevator Pitch`, Problem, Solution
  - Proof: Traction
  - Opportunity: Market, Competition, Why now and moat
  - Engine: Objection, Business model, Go-to-market
  - People and plan: Team, Ask

## Slide Titles
- Use the heading of each template slide as the slide title
  - Copy the heading text from `.claude/templates/vc_pitch_slides.template.md`,
    without the `#` and without the number
  - Do not reword the title and do not write a headline that states a claim
  - The objection slide is the only exception (see `## Objection Slide`)
- Use these titles, in this order, skipping the slides not selected
  ```markdown
  * Elevator Pitch
  * Problem
  * Solution and Product
  * Traction
  * Market Size
  * Competition
  * Why Now, Moat, and IP
  * <Claim>, Not <Objection>
  * Business Model and Financials
  * Go-to-Market (GTM) Strategy
  * Team
  * The Ask
  * Sources
  ```
  - `Sources` is the only title that is not in the template
- Put the key number of the slide in its first lead-in, since the title carries
  none
- **Bad** (a headline, a different title than the template)
  ```markdown
  * Outbound Burns Time, Money, and Domains
  * A \<TAM\> Market, Sized Bottom-Up
  ```
- **Good** (the template title)
  ```markdown
  * Problem
  * Market Size
  ```

## Pitch Style
- Start every top-level bullet with an `@...@` lead-in of 1-5 words and a colon,
  per `.claude/skills/slides.rules.md` `## Use Tags for Slide Sections`
  - Do not use `**...**` for the lead-in
  - Put the number in the lead-in when the bullet has one, e.g.,
    `@TAM \$\<TAM\> a year@:`
  - Write a pitch phrase, not a lecture tag (e.g., not `@Definition@`,
    `@Fact@`, `@Naive Solution@`)
  - Separate top-level bullets with a blank line
- Start a sub-bullet that carries a number or a named item with a bold lead-in
  and a colon, e.g., `**0.45% reply rate**:`
- Use an inline `@phrase@` at most twice per slide, to stress the key idea of a
  bullet
- Do not use lecture tags: `@Definition@`, `@Fact@`, `@Naive Solution@`,
  `@Example@`
- Use plain English: no formal definitions, no `\triangleq`, no symbols bound to
  quoted meanings
  - Use `$\times$` for a product in a sizing or cost line
- Write about customers in the third person, and name the company
- **Bad** (lecture tag vocabulary)
  ```markdown
  - @Fact@: the hit rate of cold outreach is often below 1%
  ```
- **Bad** (bold lead-in instead of `@...@`)
  ```markdown
  - **Under 1% hit rate**: hundreds of cold emails yield a handful of replies
  ```
- **Good** (pitch style: a label lead-in, then bold numbers in sub-bullets)
  ```markdown
  - Getting meetings is a @numbers game@ with a very @low success rate@
    - **Under 1% reply rate**: hundreds of cold emails yield a handful of
      replies
  ```
- **Good** (pitch style: `@...@` lead-in that carries the number)
  ```markdown
  - @Under 1% hit rate@: hundreds of cold emails yield a handful of replies
  ```
- Use these lead-ins per slide
  - `* Elevator Pitch`: `@Problem@` with 2-3 example personas as sub-bullets,
    `@Solution@` with 3 verbs as sub-bullets, `@Model@`, `@Edge@`, plus
    `@Traction@` when the deck has no Traction slide
  - Problem slide: `@Problem@` with one `E.g.,` persona, then one group bullet
    with one bold sub-bullet per quantified pain (rate, time, skill, risk, cost)
  - Solution slide: `@Today@` (how customers cope) at full width, then
    `@With <COMPANY>@` as 3 numbered steps `1) 2) 3)` beside the diagram, then
    `@Advantages@` with at most 4 bold benefits (e.g., **Pay on outcome**)
  - Traction slide: `@Commercial@` first when the input has it, else the
    strongest usage signal (e.g., `@Prototype@`), then `@Observed funnel@`,
    `@Paid pilots@`, and `@Product@` with the launch date
  - Market slide: `@TAM ...@`, `@SAM ...@`, `@SOM ...@`, plus `@Cross-check@`
    when the input has a top-down figure
  - Competition slide: the table, then `@<COMPANY>'s position@` with a price
    comparison and the competitor price sources as sub-bullets
  - Why now and moat slide: `@Why now@` with one dated trend per sub-bullet, then
    `@<COMPANY>'s edge@` with 3 numbered advantages
  - Objection slide: `@<Claim>@`, `@Not <Objection>@`, the table, then `@Result@`
  - Business model slide: `@Pricing@`, the cost sensitivity table, the unit
    economics table, `@Cost driver@`, then `@Assumptions@` and `@Revenue path@`
  - Go-to-market slide: `@Beachhead@`, then one lead-in per phase (e.g.,
    `@Months 0-12@`)
  - Team slide: the founder name in bold, then the role and one credential, then
    `@First hires and advisors@`
  - Ask slide: `@The round@`, `@Milestones@`, `@Use of funds@` (table), then
    `@Why invest@` with 3 sub-bullets, one reason each, each backed by a slide

## Placeholders and Special Characters
- Escape a placeholder in slide text as `\<PLACEHOLDER\>`. Pandoc drops a bare
  `<PLACEHOLDER>` as raw HTML, and Typst reads it as a label, so it vanishes from
  the PDF
- Keep a bare `<PLACEHOLDER>` in these places
  - `//` comments, including `// Authors=`
  - Typst string cells, e.g., `("NewCo", "<MODEL>")`
  - Graphviz plain labels, e.g., `label="SOM: $<SOM>"`
  - Graphviz HTML-like labels need `&lt;PLACEHOLDER&gt;`
- Write a dollar sign in slide text as `\$`, so pandoc never reads it as math
- **Bad** (the placeholder vanishes and `$` can open math)
  ```markdown
  - @Pricing@: $<PRICE> per meeting
  ```
- **Good**
  ```markdown
  - @Pricing@: \$\<PRICE\> per meeting
  ```

## Elevator Pitch
- Summarize the company in 4-5 bullets: problem, solution, model, edge
- Give 2-3 example personas who feel the problem, in italics, one per sub-bullet
- Write the solution as 3 verbs, one per sub-bullet (e.g., find, run, book)
- **Good**
  ```markdown
  * Elevator Pitch

  - @Problem@: \<CUSTOMER_TYPE\> need \<OUTCOME\> and cannot get it:
    - Customers: _\<PERSONA_1\>_
    - Investors: _\<PERSONA_2\>_

  - @Model@: \$\<PRICE\> per \<UNIT\>, sold in packs of \<N\>
  ```

## Problem and Solution
- Show one problem
  - Name the customer persona that feels the pain, as an `E.g.,` sub-bullet
  - Quantify the pain in rate, hours, dollars, or risk, with one bold sub-bullet
    each and a source
  - Do not mention the product on the problem slide
- Show the solution as a customer outcome, not a feature list
  - Contrast `@Today@` with `@With <COMPANY>@` to show why current tools fail
  - Write `@With <COMPANY>@` as 3 numbered steps, each with an `E.g.,` sub-bullet,
    in the 60% column beside the product diagram
  - Add at most 4 advantages under `@Advantages@`, below the columns
- **Bad** (product on the problem slide, no number, no persona)
  ```markdown
  * Problem

  - @Problem@: finance is hard and our AI platform makes it easy
  ```
- **Good** (one pain, one persona, numbers in the lead-ins)
  ```markdown
  * Problem

  - @Problem@: mid-size finance teams lose days to the month-end close
    - E.g., a \<SIZE\> company closes the books in \<DAYS\> days each month

  - Closing the books is @manual work@
    - **\<HOURS\> analyst hours**: go to manual reconciliation in each close
  ```

## Addressable Market
- Size TAM, SAM, and SOM, each in one bullet with the figure in the label
  - **TAM**: yearly revenue if every potential customer buys
  - **SAM**: the part of TAM reachable with the current product, region, and channel
  - **SOM**: the revenue captured within a stated number of years
- Use a bottom-up calculation as the main estimate. Top-down figures (analyst
  reports) are allowed only as a cross-check
  - Investors reject "we only need 1% of a huge market"
- Write the calculation as plain arithmetic: customers $\times$ units $\times$ price
- State the currency, the time unit (per year), and the year of each figure
- Attach a source to every number in the slide text, and list it on `* Sources`
- Put the bullets in the 65% column and the nested diagram in the 35% column
- **Bad** (top-down, no source, no SAM or SOM)
  ```markdown
  - @Huge market@: the global logistics software market is worth \$50B

  - @1% share@: is enough to reach \$500M
  ```
- **Good** (bottom-up, plain arithmetic, missing facts shown as placeholders)
  ```markdown
  * Market Size

  - @TAM \$\<TAM\> a year@: \<N\> \<CUSTOMER_TYPE\> in \<REGION\> $\times$
    \$\<ACV\> a year each

  - @SAM \$\<SAM\> a year@: \<N_REACH\> customers reachable with today's
    product and channel

  - @SOM \$\<SOM\> in \<YEARS\> years@: \<SHARE\>% of SAM, starting from the
    beachhead
  ```

## Competition
- Show 3-5 real alternatives, including the status quo (spreadsheets, in-house
  tools, manual work), with their prices when known
- Never claim "no competitors"
- Use a `styled-table` with `bold-first-col: true`
  - Put the table at the top level of the slide, with no bullet above it
  - Either compare options on 2-4 columns that matter to the customer, with the
    company in the last row
  - Or place the options in a 2x2 grid on the business model (e.g., who does the
    work, who bears the outcome risk), with the company in one cell
- Follow the table with one `@<COMPANY>'s position@` bullet, with a price
  comparison and the competitor price sources as sub-bullets
- **Bad** (no competitors)
  ```markdown
  - @Competition@: \<COMPANY\> has no direct competitors
  ```
- **Good**
  ````markdown
  ```{=typst}
  #styled-table(
    headers: ("Who does the work", "Customer bears risk", "Vendor bears risk"),
    rows: (
      ("Customer", "Spreadsheets, <TOOL_1>, <TOOL_2>", "None"),
      ("Vendor", "<AGENCY>, $<PRICE_1> a month", "<COMPANY>, $<PRICE> per <UNIT>"),
    ),
    col-widths: (1fr, 2fr, 2fr),
    bold-first-col: true,
    width: 100%,
  )
  ```

  - @\<COMPANY\>'s position@: \<COMPANY\> underwrites outcomes
    - A customer pays \$\<PRICE\> per \<UNIT\> vs. \$\<ALT_PRICE\> in-house
  ````

## Why Now and Moat
- `@Why now@`: 2-3 trends that opened the market, one per sub-bullet, each dated
  and sourced
- `@<COMPANY>'s edge@`: 3 numbered advantages that reinforce each other, each
  with a bold lead-in
  - Each advantage is durable: data, technology, process, distribution, or IP
  - Tie at least one advantage to a number from the business model slide

## Objection Slide
- Add it only when `<NUM_SLIDES>` is 12
- Answer the main investor objection to the product (e.g., "AI spam", "a
  feature, not a company")
- Title the slide `<Claim>, Not <Objection>`, e.g.,
  `* Multi-Channel Outreach, Not AI Spam`
  - This is the only title that states a claim
- `@<Claim>@`: how the product works, in 1-2 sub-bullets
- `@Not <Objection>@`: why the incentives of the company differ from the
  objection
- A `styled-table` with columns `Side`, `Win`, `What enforces it`, one row per
  side (e.g., prospect, customer, company)
- `@Result@`: the effect on the business, in one bullet

## Business Model, Traction, Team, Ask
- **Business model**: state who pays, for what, how much, and how often
  - Use 55/45 columns
  - Left column: `@Pricing@` with the definition of the billable unit and the
    cost of the in-house alternative as sub-bullets, then a cost sensitivity
    `styled-table` with the cases `Plan`, `Downside`, `Break-even`, and an
    industry benchmark
  - Right column: a one-row unit economics `styled-table` (price, cost, gross
    margin, LTV to CAC), then `@Cost driver@` with the cost formula in plain
    English and the observed value
    - E.g., `cost per meeting = cost per prospect $\times$ prospects per meeting`
  - Below the columns: `@Assumptions@` (price per customer a year, CAC, price
    trend), then `@Revenue path@` with the ARR at each year end for 3 years, on
    one line
  - Flag each missing value
- **Traction**: lead with commercial metrics (revenue, paying customers, letters of
  intent), each with a value and date, e.g., `\<N\> customers as of \<MONTH_YEAR\>`
  - If there is no commercial traction, lead with the strongest usage signal
    (prototype usage, pilots, letters of intent, waitlist size) and flag it
  - Show the observed funnel when the product has one
  - End with the launch date of the production product
- **Team**: one bullet per founder, with the name in bold, a role, and one
  verifiable credential related to the problem
  - End with `@First hires and advisors@`
- **Ask**: use 60/40 columns
  - Left column: `@The round@` with the amount `<ASK>`, the round, the runway in
    months, and the net burn a month, then `@Milestones@` as a numbered list of
    2-3 milestones, ending with the one that justifies the next round
  - Right column: `@Use of funds@` as a `styled-table` with columns `Area`,
    `Share`, `Amount`, with shares summing to 100%
- **Why invest**: close the Ask slide, below the columns, with 3 reasons, each
  backed by a slide of the deck

## Sources Slide
- Shrink the text and use 50/50 columns, so all sources fit on one page
  ````markdown
  * Sources

  ```{=typst}
  #set text(size: 0.7em)
  ```

  ::: columns
  :::: {.column width=50%}
  - **\<PUBLISHER\>**: _"\<TITLE\>"_ (\<YEAR\>), \<URL\>
  ::::
  :::: {.column width=50%}
  - ...
  ::::
  :::
  ````

## Claims and Style
- Use measurable statements
  - **Bad**: `a revolutionary, best-in-class platform`
  - **Good**: `cuts reconciliation time from <X> hours to <Y> hours`
- Do not use hype words (revolutionary, disruptive, game-changing, world-class,
  best-in-class, cutting-edge)
- Name the company, not "it" or "we", in the problem and solution bullets
- Cite a source in the slide text for every external number, and list it in
  `* Sources`
  - Format each entry as in `.claude/skills/slides.rules.md` `## References Slide`
    and `.claude/skills/references.rules.md`
  - Verify each source exists before listing it
  - If a source cannot be verified, add ` ???` after its link and a TODO comment

## Slide Pitfalls
- Avoid these defects, on top of the ones in the sections above
  - `* Elevator Pitch`: a vague mission statement instead of customer, pain, and
    outcome
  - Solution slide: a feature list, roadmap items shown as shipped, or a dense
    architecture diagram
  - Traction slide: vanity metrics (downloads, page views) with no link to
    revenue, and future milestones, which belong on the Ask slide
  - Market slide: generic statements (e.g., "AI is growing fast")
  - Why now and moat slide: undated trends, or an edge that any competitor can
    copy
  - Business model slide: several unproven revenue streams, or a hockey-stick
    revenue path with no assumptions
  - Competition slide: a 2x2 positioning chart where only the company sits in the
    top-right corner
  - Team slide: full CVs and credentials unrelated to the problem
  - Ask slide: an ask with no milestones, or no call to action

# Constraints
- Total slides: at most 12, counting `* Elevator Pitch`, excluding `* Sources`
- Each slide fits on one PDF page
- At most 7 top-level bullets per slide and 3 lines per bullet
- Wrap text at 80 columns, except inside Typst and Graphviz code blocks
- No lecture tags (`@Definition@`, `@Fact@`, `@Example@`) and no `#` or `##`
  headers
- No emoji and no non-ASCII characters (use LaTeX, e.g., `$\to$`)
- No `---` page separators and no period at the end of a bullet
- Do not join two clauses with a dash inside a bullet. Use a sub-bullet or a colon
- Do not use `\text{...}` in math mode
- Do not write `// From:` lines, since a pitch has no source slides
- Do not invent facts. Every figure comes from the input, or is a
  `\<PLACEHOLDER\>`. Add a TODO comment only as `## Flag Doubts` says

# Verification
- [ ] Count the slides. The output must have at most 12
  ```bash
  > grep '^\* ' <OUTPUT_FILE> | grep -v '^\* Sources$' | wc -l
  ```
- [ ] Confirm the fixed slides and the four required topics are present
  ```bash
  > grep -c '^\* Elevator Pitch$' <OUTPUT_FILE>
  > grep -c '@With ' <OUTPUT_FILE>
  > grep -cE '@(TAM|SAM|SOM)' <OUTPUT_FILE>
  > grep -c '@Beachhead@' <OUTPUT_FILE>
  ```
- [ ] Confirm every TODO comment starts at column 0
  ```bash
  > grep -n '^ \+// TODO' <OUTPUT_FILE>
  ```
- [ ] Confirm each real number that has no source has a `// TODO(gp)` line above it
- [ ] Confirm no `// TODO(gp)` line sits above a bullet that has a `\<PLACEHOLDER\>`
      and no doubt about a real value
- [ ] Confirm the deck has at least 3 figures and at least one `styled-table`
- [ ] Confirm every top-level bullet starts with an `@Label@:` lead-in, except
      the founder bullets on the Team slide
- [ ] Confirm `// logo=` points to an existing file and `// Authors=` lists the
      founders in the order the user gave
- [ ] Confirm the slide order follows the template
      `.claude/templates/vc_pitch_slides.template.md`
- [ ] Confirm each slide title equals a template heading (see `## Slide Titles`),
      except `* Sources` and the objection slide
  ```bash
  > grep '^\* ' <OUTPUT_FILE>
  > grep '^# ' .claude/templates/vc_pitch_slides.template.md
  ```
- [ ] Confirm that the slides render and each slide fits on one page (see
      `## Render and Check Layout`)
- [ ] The slides file says it was generated by
      `.claude/skills/vc_pitch.write_slides/SKILL.md`
