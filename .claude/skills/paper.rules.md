- This file contains the conventions for working with academic papers

# Working on a Paper

## Reading Papers

- When asked to read a paper (e.g., a LaTeX paper), read all the files it includes

## Performing Tasks

- When asked to perform a task
  - Create a todo list for complex tasks
  - Make sure the task is clear. If not, ask for clarifications
  - Track progress and stay on track
  - Ask for confirmation before executing the plan

# Writing Style

## Formal and Objective
- Use precise, scholarly language
- Avoid conversational tone, idioms, or subjective phrasing
- Prefer third person and appropriate passive voice

- **Bad** (subjective, conversational tone): "I think this algorithm is pretty
  efficient."
- **Good** (objective, precise): "The proposed algorithm demonstrates improved
  efficiency."

## Clear and Concise
- Prioritize clarity over stylistic complexity
- Keep sentences logically structured and direct
- Avoid unnecessary adjectives or filler words

## Evidence-Driven
- Support all claims with data, experiments, or citations
- Describe the basis for each assertion

- **Good** (concrete result): "Empirical results show a 12% reduction in latency
  compared to the baseline."

## Precise and Technical
- Use accurate technical terminology
- Define acronyms, symbols, and domain notation on first use

- **Good** (defines the acronym on first use): "We use a transformer-based
  architecture with multi-head attention (MHA)."

## Neutral and Non-Personal
- Avoid emotional or persuasive wording
- Let data and analysis express significance

- **Bad** (emotional, persuasive wording): "The method impressively reduces
  computational complexity."
- **Good** (neutral, factual): "The method reduces computational complexity."

## Structured and Logical
A strong CS academic tone reflects the conventional structure:

- **Abstract:** concise and factual
- **Introduction:** motivation, contributions, background
- **Related Work:** impartial comparisons
- **Method:** technical description, reproducibility
- **Experiments:** quantitative evaluation, transparency
- **Conclusion:** modest, acknowledges limitations

## Modest and Cautious
- Avoid absolute claims such as "solves," "proves," or "always"
- Use hedged language such as "suggests," "indicates," or "in most cases"

# Lists

## Use a Bullet List for Parallel Items

- Convert an enumeration inside a sentence into a bullet list when the sentence
  - Compares or positions something against several items (e.g.,
    `positions XYZ against A, B, and C`)
  - Announces a number of items, also a number of two (e.g., `twofold`,
    `two components`, `three phases`)
  - Enumerates three or more alternatives, components, or cases
- Use one bullet for each item
- Keep the text that introduces or follows the enumeration outside the list

- **Bad** (items buried in a sentence)
  ```latex
  We compare against three alternatives: calling a provider's API directly,
  using a multi-provider gateway, and buying raw compute on a spot market.
  ```
- **Good** (one bullet per item)
  ```latex
  We compare against three alternatives:

  \begin{itemize}
    \item \textbf{Direct API}: calling a provider's API directly.
    \item \textbf{Gateway}: using a multi-provider gateway.
    \item \textbf{Spot compute}: buying raw compute on a spot market.
  \end{itemize}
  ```

## Make the Item Names Bold

- In each bullet, use `\textbf{...}` for the name of the item that the bullet
  describes
  - This applies to a label followed by `:` and to a name that is the subject of
    the sentence
  - This applies also to a name defined by a macro (e.g., `\Noesis{}`)
- If an item has no name, add a short label before it
  - E.g., `How much they value low latency` becomes
    `\textbf{Latency sensitivity}: how much they value low latency`
- When the list explains a table or a figure, use the names that it shows

- **Bad** (plain name)
  ```latex
  \item Cloud spot markets already apply auction-based price discovery.
  ```
- **Good** (bold name)
  ```latex
  \item \textbf{Cloud spot markets} already apply auction-based price discovery.
  ```

# Links

## Make Every URL and Domain Name Clickable

- Every URL and domain name that the reader sees must be a link
  - This applies to the text, tables, captions, and footnotes
  - This applies also to a product name that is a domain name (e.g., `Vast.ai`),
    even if its URL is next to it
- Use `\url{...}` to show a URL
- Use `\href{<url>}{<text>}` to show a domain name or another text as a link
- Include `https://` in the target of the link

- **Bad** (plain text)
  ```latex
  a hosted evaluation provider, e.g., artificialanalysis.ai
  ```
- **Good** (clickable)
  ```latex
  a hosted evaluation provider, e.g.,
  \href{https://artificialanalysis.ai}{artificialanalysis.ai}
  ```

# Figures and Tables

## Legends

- Put the legend on top of the diagram
- Lay out all the legend entries in a single horizontal row

## Labels, Captions, and References

- Every picture and table needs a label and a caption, and must be referenced in the
  text
- Captions state only what is done. Put comments and other content in the text

## Captions and Labels in the Commented Section

- For every figure, add the caption and label to the commented section

- For instance convert

  ````latex
  %     ```
  % rendered_images:end
  % render_images:begin
  \begin{figure}[!ht]
    \centering
    \includegraphics[width=\linewidth]{figs/02_architecture.1.png}
    \caption{Confounding adjustment in causal inference}
    \label{fig:confounding_adjustment}
  \end{figure}
  % render_images:end
  ````

  to

  ````latex
  %     ```
  % caption=Confounding adjustment in causal inference
  % label=fig:confounding_adjustment
  % rendered_images:end
  % render_images:begin
  \begin{figure}[!ht]
    \centering
    \includegraphics[width=\linewidth]{figs/02_architecture.1.png}
    \caption{Confounding adjustment in causal inference}
    \label{fig:confounding_adjustment}
  \end{figure}
  % render_images:end
  ````

## Missing Captions and Labels

- If a figure has no caption or label, infer them from the filename and surrounding
  context
  - E.g., `figs/02_architecture.1.png` becomes `label=fig:architecture`,
    `caption=System architecture overview`
- Use short, lowercase label names with underscores

## References in the Text

- If a figure has a label but no citation in the text, add a parenthetical reference
  near the most relevant paragraph:
  ```latex
  (see Fig.~\ref{fig:confounding_adjustment})
  ```

## Orphaned References

- Scan the text for `\ref{fig:xxx}` or `\ref{tab:xxx}` with no matching `\label` in
  any figure or table environment
- Report orphaned references as warnings. Do not silently delete them

# Bibliography

## Bibliography Entries

- Add bibliography entries to the paper or to `references.bib` if used
- Cite each new entry in the text of the paper
- Make sure every added bibliography entry is relevant to the paper's topic

# Improvements

## Suggesting Improvements

- Write down the suggestions as bullet points
- Make each suggestion actionable and tied to increasing the paper's impact
