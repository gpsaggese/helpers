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

# Figures and Tables

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
