# PR review aid: notes for a future skill

Draft notes, not a skill yet. No `SKILL.md` until the design settles.

## Goal

Help a person review a large PR by producing **maps and indexes** of it, not judgments. The person reads the code and decides. The AI only puts the PR in an order they can follow.

## What was done (first trial, 2026-11-19)

Trial PR: a branch of `crabs-exploration` (17 files, +1906/-332, 27 commits).

### Input prompt

```
Review aid for PR <link/diff>. Output ONLY:
tables, bullet lists (≤12 words per item), Mermaid diagrams, code blocks.
No paragraphs, no adjectives like "robust" or "seamless".
Every claim cites file:line. If unsure, write "UNSURE" — don't guess.
Do not judge quality; I will. Produce:
1. File triage table (bucket, lines changed, 1-line purpose)
2. Signature diff (before → after)
3. Sequence diagram of the main path
4. Suggested review order
5. 10 skeptical questions with file:line
```

### Output: a `pr-review/` folder in the reviewed repo, one file per view

| File | Content |
|---|---|
| `0-summary.md` | Aim (~3 sentences), how it was done (≤6 sentences) |
| `1-file-triage.md` | Every file: bucket, +/-, one-line purpose |
| `2-signature-diff.md` | Public functions, constants, config keys, before → after |
| `3-flow-diagram.md` | Flowchart of the main path, then the sequence diagram |
| `4-review-order.md` | Ordered files with line ranges and focus |
| `5-skeptical-questions.md` | 10 questions, each with file:line |
| `6-commits.md` | Original commits; atomic scratch branch table |
| `7-component-diagram.md` | Before/after component diagrams |
| `8-tests-as-spec.md` | Behaviours tested; behaviours not tested |
| `9-red-flags.md` | CI changes, duplicate helpers, one path end to end |
| `10-difftastic.md` | Structural diff commands |
| `11-difit-workflow.md` + `difit-comments.json` | Local diff viewer with questions preloaded as comments |
| `12-predict-first.md` | Table to sketch your own design before reading |
| `13-session-plan.md` | Review split into short sessions with checkboxes |

### Methods that worked

- **Verify every file:line** with `sed -n` / `grep -n` before writing it. Estimated line numbers were often off by a few lines.
- **Atomic scratch branch.** Rebuild the branch as plumbing → core → wiring → tests → docs commits. Build intermediate file versions with exact string replacements. Assert the last stage equals the branch tip. Commit with a temporary index (`GIT_INDEX_FILE`, `commit-tree`, `update-ref`), so the working tree is untouched. Check: `git diff original scratch` is empty. Do not push.
- **difit comments.** Anchor each comment to an *added* line of the diff (new side), or it may not show. Check by parsing `git diff -U0`.
- **Red flags by search.** Duplicate-helper check = grep the repo for each new helper's core call.
- **Rename detection.** Diff the old and new module to confirm moved code is byte-identical; mark it "skim only".

### Gotchas

- zsh: `$VAR:c...` is read as a modifier. Write `"${VAR}:path"`.
- npm in the sandbox: set `npm_config_cache=$TMPDIR/npmcache`.
- `git worktree add` needs the sandbox off.
- Mermaid breaks on `;` in labels (statement end), and is fragile with `{}`, `%`, `#`.
- GitHub's Mermaid renderer disables `click` links. Add a markdown table of links under the diagram.

## User feedback

Add new feedback here when the user asks. Newest last.

| # | Feedback | Applied as |
|---|---|---|
| 1 | Keep it minimal and simple; one file per output | One short file per view |
| 2 | Sequence diagrams are hard to read | Flowchart first; sequence diagram kept at the end of the same file |
| 3 | Flowchart needs a legend | Legend subgraph: step, check, error, new-in-PR |
| 4 | Code references in diagrams should be clickable | `click` to GitHub permalinks pinned to a commit SHA, plus a relative-link table as fallback |
| 5 | Summary: brief, no ambiguous words, few clear words | Aim ~3 sentences; how ≤6 numbered sentences |
| 6 | Wants a simple difit workflow to try | Step-by-step file with exact commands, checked against `difit --help` |
| 7 | Wants to browse the rendered files as tabs, and keep VS Code preview working | Quarto support, see below |

## Quarto support (to add to the skill)

Optional step: one browser page, one tab per output file. The `.md` files stay unchanged, so VS Code and GitHub still render them.

| File | Role |
|---|---|
| `index.qmd` | `::: {.panel-tabset}` with one `{{< include N-name.md >}}` per file; each file's `# ` heading becomes its tab title |
| `_quarto.yml` | `render: [index.qmd]` only, `output-dir: _site`, `code-base-url` = GitHub permalink at the PR commit |
| `mermaid.lua` | ` ```mermaid ` → `<pre class="mermaid">`; `../` links → `code-base-url` |
| `mermaid.html` | Loads mermaid from CDN; draws a tab's diagrams when the tab is first shown |
| `.gitignore` | `_site/`, `.quarto/` |

Run: `cd pr-review && quarto preview`.

Rules this needs from the other output files:

- Exactly one `# ` heading per file, at the top.
- Mermaid as plain ` ```mermaid ` fences, not ` ```{mermaid} ` (GitHub only renders the plain form).
- Code links relative to the repo root via `../`.

Gotchas:

- Without `render: [index.qmd]`, Quarto renders every `.md` to a stray `.html` next to it.
- Mermaid in a hidden tab draws blank; draw on `shown.bs.tab`.
- `securityLevel: "loose"` is needed for `click` links in diagrams.
- `quarto render` fails in the sandbox ("unable to open database file"): it writes `~/Library/Caches/quarto`. Run outside the sandbox.
- Checked with Quarto 1.9.37, mermaid 11.4.1.

## Open ideas for the skill

- Reuse `dev/skills/proposal/scripts/check-mermaid.sh` to validate diagrams.
- Reuse `dev/skills/writing-style` rules for the summary file.
- Optional step: strip comments on the scratch branch (makes the final diff non-empty).
