---
name: writing-style
description: Writing rules for technical Markdown documents that people read and comment on, such as proposals, design docs and review reports (structure, sentences, mermaid diagrams, code anchors, raw readability). Use when drafting, editing or checking such a document.
user-invocable: false
---

# Writing style

Rules for a document a person will read, comment on and discuss.

- **They apply to every revision**, not only the first draft. An edit made mid-discussion is held to the same rules as the text it replaces.

- **The reader's confusion is evidence about the writing.** A question asked about the document marks a part that was not clear enough.

The rules condense *Scientific Papers Made Easy* (West & Turnbull, OUP 2023). Read
[reference/book-summary.md](reference/book-summary.md) when a rule needs interpreting.

## Structure

- **General to detail, everywhere.** A reader who stops after the first section still knows what is being proposed and why. The same holds for a section, a paragraph and a bullet list.

- **Lead with a one-line statement of the idea.** Then the detail, below it and indented.

- **One idea per bullet, per paragraph, per sentence.** One-line paragraphs are good. Start a new paragraph for each new idea.

- **Prefer vertical to horizontal.** Anything of the form "X is A and B" becomes a lead line and a list:
    - ❌ `The entire feature is two new modules: the entry point and the read-side helper.`
    - ✅ `The entire feature is two new modules:` then one bullet per module.

- **Bullet points, not prose.** Fall back to a sentence only for reasoning no list, table, diagram, signature or diff can carry.

- **Make cross-references links**, e.g. `[§5](#5-configuration-a-separate-mask-config)`, never a bare `(§5)`.

- **Avoid back-references.** No *"the former"*, *"the latter"*, *"the above"*, or a bare *"these"*. Name the thing again — repetition is cheaper than a reader scrolling up.

- **Collapse deep detail.** Anything past roughly fifteen lines of argument, or that only matters to whoever implements it, goes in `<details><summary><b>…</b></summary>`.

## Sentences

- **What first, then why.** The subject of the sentence is the thing being decided.
    - ❌ `load_config can read the new field from settings.yaml, which the CLI already parses — so the CLI needs no change either.`
    - ✅ `The CLI needs no change: load_config reads the new field from settings.yaml, which the CLI already parses.`

- **Short sentences that make one point.** If a sentence runs past two lines, split it.

- **Write as you speak, and cut the lingo.** If you would not say the word out loud, do not write it. No unexplained abbreviations. Define a term of art the first time it appears, in a one-line `> [!NOTE]`.

- **State the conclusion, not your train of thought.** Give the recommendation and the reason for it. Reasoning you rejected belongs in a *rejected alternatives* table, or nowhere.

- **No meta-writing.** Do not say who the document is for, that it was drafted with an assistant, or that it is meant to be read by people. Do not ask for feedback on the format.

- **Never mention earlier drafts.** The document describes its current state only. Banned: *"the first draft left this out"*, *"added here at review request"*, *"note that X is not in this list any more"*.

- **Be precise and consistent.** Fix your terms and reuse them exactly, matching the names the codebase already uses. If you called it a `plot`, never later call it a `graph`.

## Diagrams

- **Say what the arrows mean**, in one line directly under the diagram. *"Arrows are sequential steps"* and *"arrows point from parent to child"* are different diagrams and a reader cannot tell them apart by looking.

- **Let the boxes reach the code.** Add `click` directives, and repeat them as a node → link legend under the diagram:

    ```
    click T1 href "https://github.com/<org>/<repo>/blob/main/src/<pkg>/loader.py#L56" _blank
    ```

    Some renderers (GitHub among them) strip `click` for security, so the legend is what guarantees the link is reachable. Ensure that the legend is understandable once rendered (e.g. a node name B may not be visible once rendered).

- **Style only the two or three nodes that matter**, and use ✨ consistently for "new in this PR".

- **If box colours or line styles are used**, they should have a meaning. Do not use different colours for boxes that represent the same idea (e.g. an action, or an output).

## Evidence

- **Be honest about uncertainty.** Say "verified against <dependency> <pinned version>" when you checked. Never present a guess as a finding.

- **Anchor every claim.** Link code as `[loader.py:356](src/<pkg>/loader.py#L356)` and issues or PRs as `[#960](https://github.com/<org>/<repo>/issues/960)`. Repeat the link each time the number appears.

- **Pseudocode is allowed** where real code would distract. Keep it in a code block in the project's language, with control flow in capitals (`FOR EACH`, `IF`, `skip`) so nobody pastes it.

- **Small code snippets as diffs** are very useful to quickly communicate a suggested implementation detail.

## Raw readability

The document must read well as raw Markdown, not only rendered.

- A blank line between every block, and around every fence, table and diagram.
- Sub-bullets indented by four spaces.
- Lines wrapped at roughly 100 characters.

## Formatting toolkit

| Need | Use |
|---|---|
| New or changed code | ```` ```diff ```` with `+`/`-`, or a bare signature with `...` as the body |
| Flow across files | a `mermaid` `flowchart TD`, styling the two or three nodes that matter |
| Comparing options | a table with one row per option and a *why worse* column |
| Presenting options in text | a bullet list, one option per bullet |
| A definition or aside | `> [!NOTE]` |
| A cell that must hold a code block | raw `<table>` HTML — Markdown tables cannot |
| Long argument | `<details>` |
