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

### Output: a `pr-review/` folder in the reviewed repo, 3 blocks

Revised after feedback (2026-11-20). First draft had 14 flat files; the user cut it to these.

| Block | File | Content |
|---|---|---|
| 1. Understand | `1-aim.md` | Aim (~3 sentences); optional "predict first" table |
| | `2-components.md` | Before/after component diagrams |
| | `3-flow.md` | Flowchart of the main path (legend, click links), then the sequence diagram |
| | `4-signatures.md` | Same flowchart; each box links to its signature diff, tooltip summarises it |
| 2. Review | `1-atomic-branch.md` | Original commits; atomic scratch branch table |
| | `2-difit.md` | Two difit options, how comments are saved, session plan, preloaded questions |
| | `questions.json` | Skeptical questions as difit comments |
| | `3-red-flags.md` | AI-specific checks, read last |
| 3. Tests | `1-tests.md` | Test plan table for difit; behaviours tested and not tested |
| root | `review.sh` | Runs difit one item per tab, saves comments to `notes/` |

Order inside block 1 goes from general to detailed: aim → components → flow → signatures.

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
| 8 | Keep both: Quarto in the browser, plain markdown in VS Code as backup | `.md` files stay source; Quarto only includes them |
| 9 | Structure in 3 blocks: understand, review with difit, review tests with difit | Block folders; outer and inner tabs in Quarto |
| 10 | Block 1 from general to detailed; drop "How" from the summary | aim → components → flow → signatures |
| 11 | Relate each signature diff to a box in the flow diagram | Flowchart on top of the signatures file; click jumps to the section, hover shows a summary |
| 12 | Reviewer should not run difit once per commit; comments saved to JSON as they go | `review.sh`: close tab = next item; polls the difit API every 2 s |
| 13 | Two review options: commit by commit on the atomic branch, or a session plan | `review.sh atomic` and `review.sh sessions` |
| 14 | Tests reviewed in difit, file by file for now | `review.sh tests`, rows from the table in `1-tests.md` |
| 15 | Check which steps can be deterministic, not LLM calls | Table below |
| 16 | Keep the concise style | Tables, short bullets, file:line |
| 17 | Aim as "Before this PR / With this PR"; plain English | Two bold-led paragraphs: before = what the store held and how runs behaved; with = what is added, what it aligns with, run changes. Name real variables (`attrs.mask_config`); say what *changed* (e.g. where config is saved), not just what exists |

## Quarto support (to add to the skill)

Optional step: one browser page, one tab per output file. The `.md` files stay unchanged, so VS Code and GitHub still render them.

| File | Role |
|---|---|
| `index.qmd` | Outer `::::: {.panel-tabset}` with one `# Block` heading per block; inner `:::: {.panel-tabset}` with one `{{< include block/N-name.md >}}` per file; each file's `# ` heading becomes its tab title |
| `_quarto.yml` | `render: [index.qmd]` only, `output-dir: _site`, `code-base-url` = GitHub permalink at the PR commit |
| `mermaid.lua` | ` ```mermaid ` → `<pre class="mermaid">`; `../` and `../../` links → `code-base-url` |
| `styles.css` | Diff blocks coloured per line, like GitHub; small path headings |
| `mermaid.html` | Loads mermaid from CDN; draws a tab's diagrams when the tab is first shown |
| `.gitignore` | `_site/`, `.quarto/` |

Run: `cd pr-review && quarto preview`.

Rules this needs from the other output files:

- Exactly one `# ` heading per file, at the top.
- Mermaid as plain ` ```mermaid ` fences, not ` ```{mermaid} ` (GitHub only renders the plain form).
- Code links relative to the file (`../../crabs/...` from a block folder).
- In-page anchors as `<a id="sig-x"></a>`: works in VS Code, GitHub and Quarto.

Gotchas:

- Without `render: [index.qmd]`, Quarto renders every `.md` to a stray `.html` next to it.
- Mermaid in a hidden tab draws blank; draw on `shown.bs.tab`.
- `securityLevel: "loose"` is needed for `click` links in diagrams.
- `quarto render` fails in the sandbox ("unable to open database file"): it writes `~/Library/Caches/quarto`. Run outside the sandbox.
- Quarto marks diff `+` lines `span.va` and `-` lines `span.st`; colour the parent line span with `:has()`. Use `inline-block; width:100%`, not `block` (doubles line spacing).
- Diamonds make tall diagrams; use plain boxes when the diagram is an index.
- Checked with Quarto 1.9.37, mermaid 11.4.1.

## difit runner (`review.sh`)

Facts checked in difit 5.0.12 source and by a live run:

- Comments live in browser localStorage, per diff. Also POSTed to the server (`/api/comments`).
- `GET /api/comments-json` returns the open diff's threads. `difit comment get --port N --format json` wraps it.
- On Ctrl+C or tab close, difit prints all comments as text, then exits.
- Closing (or reloading) the tab ends the server, unless `--keep-alive`.
- The revision selector lists only the last 20 commits of the checked-out branch.
- Stdin diffs (`git diff ... | difit -`) all share one browser storage key.

How `review.sh` uses them:

| Need | How |
|---|---|
| One commit per tab, no manual runs | loop over `git rev-list --reverse base..atomic`; wait for difit to exit |
| File groups per tab | `git diff -M base branch -- files \| difit - --clean` |
| Save as you go | poll `/api/comments-json` every 2 s into `notes/<item>.json` |
| Do not lose saved notes | overwrite only after a change; stdin items re-import saved notes via `--comment` |
| Preload questions on the right commit | `git blame` the question's line on the atomic branch |
| Item lists editable by the reviewer | parse markdown table rows that end in `[ ]` / `[x]` |
| Testing without a browser | `DIFIT_EXTRA="--no-open"`, add comments with `difit comment add` |

UNSURE: whether imported questions duplicate when the browser also restores them from localStorage (README says duplicates are skipped).

## Deterministic or LLM?

| Step | Deterministic option | Status |
|---|---|---|
| File triage (+/-, bucket) | `git diff --numstat -M`; bucket by path rules | used |
| Line anchors correct | script: each `file:line` exists and matches a name | idea |
| Signature diff | `ast` compare of defs at base vs tip; or `griffe check` | idea, untested |
| Component diagram | import graph at base and tip (`pydeps`, or `ast` imports) → mermaid | idea; LLM picks what to show |
| Flow diagram | call graph from `main` (`pyan3`, `code2flow`) | idea; noisy, LLM picks the path and labels |
| Box ↔ signature link | function name in box ↔ def name in diff | idea, needs boxes named by function |
| Mermaid valid | `mmdc`, or `check-mermaid.sh` | idea |
| Atomic branch mechanics | temp index + `commit-tree`; final-tree equality check | used |
| Atomic branch grouping | none; needs judgment | LLM |
| Question → commit | `git blame` on atomic branch | used |
| difit runs and saving | `review.sh` | used |
| Tests added/removed | `pytest --collect-only -q` at base vs tip, diff the lists | idea |
| Changed lines not tested | `pytest --cov` + `diff-cover` | idea; replaces the grep-based "not tested" table |
| CI and skip/xfail changes | `git diff -- .github`; grep `skip\|xfail` in test diff | used |
| Duplicate helpers | clone detection (`pylint --enable=duplicate-code`, `jscpd`) | idea; LLM still judges "same intent" |
| Aim, questions, red-flag reading | none | LLM |

## Open ideas for the skill

- Reuse `dev/skills/proposal/scripts/check-mermaid.sh` to validate diagrams.
- Reuse `dev/skills/writing-style` rules for the summary file.
- Optional step: strip comments on the scratch branch (makes the final diff non-empty).
- Signatures view as two panes: flowchart fixed on the left, hover a box to show its diff on the right (custom JS in Quarto).
- Merge all `notes/*.json` into one prompt for the agent at the end of block 2.
