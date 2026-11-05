---
name: proposal
description: Research a code change in plan mode, then write a proposal document for people to review before any code is written, in GitHub-flavoured Markdown with mermaid diagrams, signatures, diffs and tables.
when_to_use: Use when the user asks for a proposal, design doc, RFC or "a plan I can review / share / discuss" for a single PR-sized change. Do not use for a quick plan-mode plan the user will approve in the terminal.
argument-hint: "[change to propose]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/check-mermaid.sh *)
---

# Proposal

The change to propose: $ARGUMENTS

If that is empty, ask the user what the change is before doing anything else.

Write **one document per PR**, for a human to read, comment on and discuss before any code is written.

- **The proposal replaces the plan-mode plan.** Enter plan mode, but the document is the deliverable. Do not write a second, separate plan for terminal approval.

- **One proposal = one PR = one small feature.** If the change does not fit in one PR, say so and propose the split.

- **Keep your own notes elsewhere.** A task checklist or scratch file is fine, but never inside the proposal.

## Process

1. **Enter plan mode.** Call `EnterPlanMode` before touching anything. Load it with `ToolSearch` (`select:EnterPlanMode,ExitPlanMode`) if its schema is not available. Write no code and edit no source files. Plan mode only lets you write its own plan file, so that file is where the proposal is drafted.

2. **Investigate first.** A proposal is only worth reading if every claim is checked.

    Run the `plan-with-diagrams:proposal-investigator` agent with the change to propose. It returns anchored facts, each marked verified or unverified. Read the code behind any fact the proposal will lean on, and carry its *Open questions* into *Points to discuss*.

    If the agent is not available, investigate yourself before drafting:
    - read the code you propose to change, and note exact `file:line` anchors;
    - verify API claims against the *pinned* version of the dependency, not memory;
    - check open issues and pull requests that touch the same files (with `gh issue list` and `gh pr list` if the project is on GitHub and `gh` is installed; otherwise ask the user for related issues);
    - look for existing tests and fixtures you can reuse.

3. **Plan the document before you write it.** Bullet what must be covered, then order the bullets. Sketch the diagrams first: they carry the argument, and the text only fills the gaps they leave.

4. **Draft it in the plan file.** Follow *Sections* and *Writing rules* below. Use [template.md](template.md) as the skeleton.

5. **Check the diagrams render.** Run `${CLAUDE_SKILL_DIR}/scripts/check-mermaid.sh <plan file>` and fix every `FAIL`. If it exits with status 2 (no renderer available), say so when presenting and carry on.

6. **Present it.** Call `ExitPlanMode`. The user sees the proposal itself for approval. Approving it means "the proposal is ready for discussion", not "start implementing".

7. **Save it** once out of plan mode: copy the plan file to `claude-plans/proposal-<short-slug>.md` in the project, unless the user names a path. Tell the user the path and offer to publish it for comment (below). From here on, edit the saved copy, not the plan file. Do not start implementing unless the user asks.

8. **Refine it interactively.** See *During the discussion*.

## Publishing for comment

Offer a way to read the proposal rendered, with its diagrams, and comment on it. Use the first option that is available:

- **An Artifact**, if the `Artifact` tool is available in this session.
    - Publish the saved `.md` file itself. This skill is the explicit instruction that makes a Markdown publish correct.
    - The artifact is private until the user shares its link. The user can highlight any part of it and send a comment thread to Claude.
    - Republish the same file path after every edit, so the rendered document never lags behind the file.
    - Handle comment threads with the `ArtifactComments` tool (load it with `ToolSearch` if only its name is listed). Resolve a thread once the document has been changed to match.

- **GitHub**, if the project is on GitHub and the user agrees to push. A file on a branch, a gist or a draft PR renders mermaid and takes line comments. Never push without asking.

- **Otherwise**, the local file. Most editors can preview Markdown with mermaid.

Every edit driven by a comment follows *During the discussion* below.

Use absolute GitHub URLs (`https://github.com/<org>/<repo>/blob/<branch>/path#L10`) for code anchors if the document will be published or shared. Relative paths only work for a local file.

## During the discussion

The user asks questions about the draft and the document is edited in response. **Every writing rule applies to those edits exactly as it applies to the first draft.**

- **Answer with the conclusion first, then the reason.** This holds in the chat reply and in the document.

- **Fold the answer into the document.** A question that was worth asking marks a part of the document that was not clear enough.

- **Never mention earlier drafts.** Keep the conclusion and the reasoning; drop the history.

- **Record outcomes in the right-hand column of the *Points to discuss* table.**

- **Re-read the whole section you edited.** An insertion easily breaks general-to-detail order or adds a back-reference to something that is now far away.

- **Re-run the diagram check** after editing a diagram.

## Writing rules

Read `${CLAUDE_PLUGIN_ROOT}/skills/writing-style/SKILL.md` before drafting, and follow it for the first draft and every edit after it.

On top of those rules, a proposal has its own:

- **Open the document with a diagram**, and put another at the top of *Detailed implementation*.

- **Propose the simplest implementation that works.** Always aim for the minimum change to the codebase.

- **Anything beyond that minimum goes in *Points to discuss*.** Do not build a nice-to-have into the plan.

- **Anything you did not verify goes in *Points to discuss* too.**

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

10. **`## Verifications for agent to run`** — the manual checks and the exact commands the project uses for tests and linting (for example `pytest …`, `pre-commit run --all-files`), including how to get any sample data.

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

