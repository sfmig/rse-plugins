---
name: proposal
description: Research a change in plan mode, then write a human-reviewable proposal document in GitHub-flavoured Markdown (signatures, diffs, tables, mermaid, collapsible detail). Use when the user asks for a plan, proposal, design doc or RFC to be reviewed by people before any code is written, or types /proposal.
---

# Proposal

Write **one document per PR**, for a human to read, comment on and discuss before any code is written.

- **The proposal replaces the plan-mode plan.** Enter plan mode, but the document is the deliverable. Do not write a second, separate plan for terminal approval.

- **One proposal = one PR = one small feature.** If the change does not fit in one PR, say so and propose the split.

- **Keep your own notes elsewhere.** A task checklist or scratch file is fine, but never inside the proposal.

## Process

1. **Enter plan mode.** Call `EnterPlanMode` before touching anything. Load it with `ToolSearch` (`select:EnterPlanMode,ExitPlanMode`) if its schema is not available. Write no code and edit no source files; the proposal file is the only thing you write.

2. **Investigate first.** A proposal is only worth reading if every claim is checked. Before drafting:
    - read the code you propose to change, and note exact `file:line` anchors;
    - verify API claims against the *pinned* version of the dependency, not memory;
    - check open issues and pull requests that touch the same files (`gh issue list`, `gh pr list`);
    - look for existing tests and fixtures you can reuse.

3. **Plan the document before you write it.** Bullet what must be covered, then order the bullets. Sketch the diagrams first: they carry the argument, and the text only fills the gaps they leave.

4. **Draft it.** Follow *Sections* and *Writing rules* below. Use `reference/template.md` as the skeleton.

5. **Save it** as `claude-plans/proposal-<short-slug>.md`, unless the user names a path.

6. **Present it.** Call `ExitPlanMode` with two or three lines and the file path. Offer to publish it for comment (below). Do not start implementing unless the user asks.

7. **Refine it interactively.** See *During the discussion*.

## Publishing for comment

Offer to publish the proposal as an Artifact once the user has the file. It renders the mermaid diagrams, and the user can highlight any part of it and send a comment thread to Claude.

- Publish the `.md` file directly with the `Artifact` tool — this skill is the explicit instruction that makes a Markdown publish correct.
- Republish to the same URL after every edit, so the rendered document never lags behind the file.
- Read comment threads with `action: "comments"`, answer with `action: "reply"`, and `action: "resolve"` a thread once the document has been changed to match.
- Every edit driven by a comment follows *During the discussion* below.
- Use absolute GitHub URLs (`https://github.com/<org>/<repo>/blob/<branch>/path#L10`) for code anchors if the document will be published or shared. Relative paths only work for a local file.

## During the discussion

The user asks questions about the draft and the document is edited in response. **Every writing rule applies to those edits exactly as it applies to the first draft.**

- **Answer with the conclusion first, then the reason.** This holds in the chat reply and in the document.

- **Fold the answer into the document.** A question that was worth asking marks a part of the document that was not clear enough.

- **Never mention earlier drafts.** The document describes the current proposal only. Banned: *"the first draft left this out"*, *"added here at review request"*, *"note that X is not in this list any more"*. Keep the conclusion and the reasoning; drop the history.

- **Record outcomes in the right-hand column of the *Points to discuss* table.**

- **Re-read the whole section you edited.** An insertion easily breaks general-to-detail order or adds a back-reference to something that is now far away.

## Writing rules

### Structure

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

### Sentences

- **What first, then why.** The subject of the sentence is the thing being decided.
    - ❌ `generate_masks can derive its output path from self.tracking_output_dir and self.input_video_file_root, which prep_outputs already sets — so prep_outputs needs no change either.`
    - ✅ `prep_outputs needs no change: generate_masks derives its output path from self.tracking_output_dir and self.input_video_file_root, the same way it does already.`

- **Short sentences that make one point.** If a sentence runs past two lines, split it.

- **Write as you speak, and cut the lingo.** If you would not say the word out loud, do not write it. No unexplained abbreviations. Define a term of art the first time it appears, in a one-line `> [!NOTE]`.

- **State the conclusion, not your train of thought.** Give the recommendation and the reason for it. Reasoning you rejected belongs in a *rejected alternatives* table, or nowhere.

- **No meta-writing.** Do not say who the document is for, that it was drafted with an assistant, or that it is meant to be read by people. Do not ask for feedback on the format. Propose the change and stop.

- **Be precise and consistent.** Fix your terms and reuse them exactly, matching the names the codebase already uses. If you called it a `plot`, never later call it a `graph`.

### Diagrams

- **Open the document with a diagram**, and put another at the top of *Detailed implementation*.

- **Say what the arrows mean**, in one line directly under the diagram. *"Arrows are sequential steps"* and *"arrows point from parent to child"* are different diagrams and a reader cannot tell them apart by looking.

- **Let the boxes reach the code.** Add `click` directives, and repeat them as a node → link legend under the diagram:

    ```
    click T1 href "https://github.com/org/repo/blob/main/crabs/tracker/track_video.py#L56" _blank
    ```

    Some renderers (GitHub among them) strip `click` for security, so the legend is what guarantees the link is reachable. Ensure that the legend is understandable once rendered (e.g. a node name B may not be visible once rendered).

- **Style only the two or three nodes that matter**, and use ✨ consistently for "new in this PR".

### Scope

- **Propose the simplest implementation that works.** Always aim for the minimum change to the codebase.

- **Anything beyond that minimum goes in *Points to discuss*.** Do not build a nice-to-have into the plan.

- **Be honest about uncertainty.** Say "verified against napari 0.6.6" when you checked. Move anything you did not check into *Points to discuss*. Never present a guess as a finding.

- **Anchor every claim.** Link code as `[loader_widgets.py:356](movement/napari/loader_widgets.py#L356)` and issues or PRs as `[#960](https://github.com/org/repo/issues/960)`. Repeat the link each time the number appears.

- **Pseudocode is allowed** where real code would distract. Keep it in a `python` block with control flow in capitals (`FOR EACH`, `IF`, `skip`) so nobody pastes it.

- **Small code snippets as diffs** are very useful to quickly communicate a suggested implementation detail.

### Raw readability

The document must read well as raw Markdown, not only rendered.

- A blank line between every block, and around every fence, table and diagram.
- Sub-bullets indented by four spaces.
- Lines wrapped at roughly 100 characters.

### Formatting toolkit

| Need | Use |
|---|---|
| New or changed code | ```` ```diff ```` with `+`/`-`, or a bare signature with `...` as the body |
| Flow across files | a `mermaid` `flowchart TD`, styling the two or three nodes that matter |
| Comparing options | a table with one row per option and a *why worse* column |
| Presenting options in text | a bullet list, one option per bullet |
| A definition or aside | `> [!NOTE]` |
| A cell that must hold a code block | raw `<table>` HTML — Markdown tables cannot |
| Long argument | `<details>` |

## Sections

Use these headings, in this order. Drop a section only if it is genuinely empty, and say so in one line rather than deleting the heading silently.

1. **`# Proposal for <what>`** — one line of title, no preamble.

2. **`## Description`** — one or two lines saying what changes, then a diagram of it. Nothing else.

3. **`## References`** — a bullet list of the issues, PRs and related plans this builds on or overlaps.

4. **`## Overview of steps`** — a numbered list, one line per step, no detail. The whole PR should be legible from this list alone.

5. **`## Key aspects of suggested implementation`** — one `###` subsection per decision a reviewer must agree with before the detail matters. Lead with the external constraint (the framework contract, the file format, the API), then what it forces. Signatures, manifests and config snippets go here.

6. **`## Detailed implementation`** — a mermaid diagram of the finished flow, then a numbered table of every change (number, change, signature or diff), then one `<details>` per step with the argument and the rejected alternatives.

7. **`## Files changed`** — a two-column table, file and change. Mark new files **new**.

8. **`## Tests`** — answer *are tests needed?* in one line. If yes, list them grouped by kind (unit, integration), with a code snippet or pseudocode for each, and name the fixtures that already exist. In a first pass, one line per test is enough; expand them when the user asks.

9. **`## Documentation updates`** — answer *is a doc update needed?* in one line, and name the files.

10. **`## Verifications for agent to run`** — the manual checks and the exact commands (`pytest …`, `pre-commit run --all-files`), including how to get any sample data.

11. **`## Points to discuss`** — a two-column table, so conclusions from the review can be written straight into it:

    | # | To discuss | Conclusion |
    |---|---|---|
    | 1 | **Short title.** The question in one or two lines, then your recommendation. | |

### Optional sections

Include these only when they have real content, before *Points to discuss*:

- **`## Dependencies`** — any new dependency, how it installs, and its license.
- **`## Tradeoffs`** — what this design gives up, in a table.
- **`## Gotchas`** — things that will silently degrade or crash this, in a table of detail, consequence and handling.

There is no *Feedback on the format of this proposal* section. Do not add one.

---

The writing rules condense *Scientific Papers Made Easy* (West & Turnbull, OUP 2023), read as advice to a model drafting a proposal for a human reviewer. See `reference/writing-style.md` for the reasoning behind each rule.
