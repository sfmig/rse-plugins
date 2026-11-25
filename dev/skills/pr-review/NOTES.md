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

### Output: a `pr-review/` folder in the reviewed repo, 2 blocks and `scripts/`

Revised after feedback (2026-11-20). First draft had 14 flat files; the user cut it to these.

| Block | File | Content |
|---|---|---|
| 1. General (`1-general/`) | `1-aim.md` | Aim, then before/after component diagrams |
| | `2-flow.md` | Flowchart of the main path (legend, click links), then the sequence diagram |
| | `3-signatures.md` | One section per flowchart box: a one-line pipeline with that box highlighted, then its diffs; one sentence on how changes were selected |
| | `4-predict.md` | Optional "predict first" table |
| 2. Review | `1-atomic-branch.md` | Original commits; atomic scratch branch table |
| | `2-difit.md` | Two difit options, how comments are saved, session plan, preloaded questions |
| | `questions.json` | Skeptical questions as difit comments |
| | `3-tests.md` | Step table for `review.py tests` (one module under test per step: its source and test files); behaviours tested and not tested (was block 3, `3-tests/1-tests.md`, until 2026-11-25) |
| | `4-red-flags.md` | AI-specific checks, read last |
| `scripts/` | `review.py` | Review page + difit, saves comments to `comments/pass-N/`; opens files in the editor (`/api/edit`); read-only on git |
| | `links.py` | Tests mode: link comments between each test and the functions it calls |
| | `comments.py` | Comments file of a pass; follows commit lines to the tip with `git blame` |
| | `page.html` | The review page |
| | `atomic.py` | The PR's branches; `atomic.py extend` adds the PR branch's new commits to the atomic branch |

Order inside block 1 goes from general to detailed: aim and components → flow → signatures → optional predict.

### Minimal layout (2026-11-25, feedback 58–61)

The layout to build first. The full layout above is the menu of optional extras (signatures, sequence diagram, predict, red flags). Example: [`example-minimal/`](example-minimal/README.md).

| Tab | File | Content |
|---|---|---|
| Aim and diagrams | `1-general/1-aim.md` | Aim (before / with this PR), component diagrams before → after, flow diagram with its links table |
| Atomic branch | `2-review/1-atomic-branch.md` | As in the full layout, plus which commits each review shows |
| Review code with difit | `2-review/2-code.md` | **Code review**: `review.py all \| atomic \| sessions`, test files left out; review page, comments, passes, after-review prompts, session table, code questions |
| Review tests with difit | `2-review/3-tests.md` | **Tests review**: `review.py tests`, step table, its own passes and questions, not tested, fail-before |
| | `2-review/questions-code.json`, `questions-tests.json` | Preloaded questions, one file per review |
| `scripts/` | as in the full layout | `review.py` picks the review from the mode; comments in `comments/code/pass-N/` and `comments/tests/pass-N/` |

Two reviews, each with its own passes: first the code, without tests, then the tests, next to the code they test. A test file is one in a `tests/` folder, or named `test_*.py`, `*_test.py`, `conftest.py` (`atomic.is_test`). Atomic mode skips commits of tests only, keeping the table's commit numbers; a commit with both shows only its code files.

**Reference example: block 1.** The user approved `1-general/` (2026-11-20) as the model for the other blocks: content, style, section links, back-to-top links. Copy of the full package, as of 2026-11-23: [`example/`](example/README.md).

### Methods that worked

- **Verify every file:line** with `sed -n` / `grep -n` before writing it. Estimated line numbers were often off by a few lines.
- **Atomic scratch branch.** Rebuild the branch as plumbing → core → wiring → tests → docs commits. Build intermediate file versions with exact string replacements. Assert the last stage equals the branch tip. Commit with a temporary index (`GIT_INDEX_FILE`, `commit-tree`, `update-ref`), so the working tree is untouched. Check: `git diff original scratch` is empty. Do not push.
- **Keep the atomic branch current by extending, not rebuilding.** Find the commit on the PR branch whose tree hash equals the atomic tip's (`git log --format='%H %T'`). Replay each later commit as `commit-tree <its tree> -p <atomic tip>`: same files by construction, so no checkout and no conflicts. A rebuild would change every hash, item number and saved comment.
- **difit comments.** Anchor each comment to an *added* line of the diff (new side), or it may not show. Check by parsing `git diff -U0`.
- **Red flags by search.** Duplicate-helper check = grep the repo for each new helper's core call.
- **Rename detection.** Diff the old and new module to confirm moved code is byte-identical; mark it "skim only".

### Gotchas

- zsh: `$VAR:c...` is read as a modifier. Write `"${VAR}:path"`.
- npm in the sandbox: set `npm_config_cache=$TMPDIR/npmcache`. For difit's CLI usage without running it, read the cached `~/.npm/_npx/*/node_modules/difit/README.md`.
- `set -e` + `read -r -a x < <(... | tr '\n' ' ')`: `read` returns 1 at end of input with no final newline, so the script stops. Add `|| true`.
- `set -o pipefail` + `git log | awk '... { exit }'` (or `| head`): git log gets SIGPIPE and the script stops. Let awk read all input.
- macOS ships bash 3.2: no `mapfile`. Use `while read` or word splitting.
- `git worktree add` needs the sandbox off.
- Mermaid breaks on `;` in labels (statement end), and is fragile with `{}`, `%`, `#`.
- GitHub's Mermaid renderer disables `click` links. Add a markdown table of links under the diagram.

## User feedback

Add new feedback here when the user asks. Newest last.
Rows 12–14 and 22–29 describe the first, bash difit runner; it was replaced on 2026-11-24 (rows 30–44).

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
| 18 | Say how the signature changes were selected | One sentence in the file; selection script in `scripts/` |
| 19 | Link the sections listed at the top of a file | `* [Flow diagram](#flow-diagram)`; anchor = GitHub/Pandoc slug of the `##` heading |
| 20 | "Back to top" right under each `##` heading, standard style | `[↑ Back to top](#top)` on the line after the heading; no arrow inside the heading (changes its anchor) |
| 21 | Block 1 (`1-general/`) is a good example to follow | Reference example, see above |
| 22 | Unclear what closing the tab does | "Managing tabs" section: difit exits when its tab closes, then the loop opens the next item; a reload counts as a close |
| 23 | Resume from a commit hash, not only a number | `review.sh atomic <sha>`; an all-digit short hash is read as a position |
| 24 | Option to review the whole PR at once | `review.sh all`: base..branch in one tab. No arguments still prints usage, so the bare command is harmless |
| 25 | How is the atomic branch created, and kept current? | Built once by the agent (needs judgment). `review.sh atomic` warns when it no longer matches the PR branch; `extend-atomic.sh` appends the new commits |
| 26 | Work facts out from git instead of recording them | Matching commit found by tree hash; `BRANCH`, `BASE`, `ATOMIC` worked out in `config.sh`, env overrides |
| 27 | A script that changes branches should be separate from the review runner | `scripts/`: `review.sh` (read-only), `extend-atomic.sh`, shared `config.sh` |
| 28 | Names must say what the code does | "built from" read as "branched off" → "the commit whose files match the atomic tip"; `refresh` read as "rebuild" → `extend-atomic.sh`; function `last_commit_matching_atomic` |
| 29 | Code comments: short; what it does, plus why for the non-obvious part | User cut a 10-line comment to 3 lines: what it prints, the empty case, why awk reads to the end |
| 30 | Leave the tests out of the difit runner for now | `tests` mode removed; `3-tests/` block kept, it points to `review.py all` or a session row |
| 31 | Opening each tab took ~4 s | Causes: npx asked the npm registry on every launch; the script noticed a closed tab only every 2 s. Now difit is installed once (`npm i -g difit@5.0.12`) and an item opens in ~0.1–0.5 s |
| 32 | Easier to move between commits; commit message as the tab name | One **review page**: sidebar of items, the chosen one in difit in an iframe, Prev/Next (Alt+↑/↓). Browser tab title = item title. A tabs mode (close tab = next) was kept for a trial, then dropped |
| 33 | Rename "Risk" to "Weight" and colour high/med/low | Column `Weight` with 🔴 🟠 🟢 in `1-atomic-branch.md`; same colours as dots in the sidebar; legend only in atomic mode |
| 34 | Comments independent of the review mode | One comments file per pass. Each thread has `commit` (sha, file, position) and `tip` (file, position). As on GitHub, comments only move forward: written on a commit → tip line found by `git blame` each run; written on the whole PR → stays at the tip. Tip→commit mapping was built, then dropped for simplicity |
| 35 | Outdated comments: do as GitHub | GitHub hides them in "Files changed" and lists them in "Conversation" with an Outdated label. Here: inline only on their commit; listed in the sidebar elsewhere. No "open its commit" button (GitHub has none) and no old code line |
| 36 | One comments file per pass; a reviewer may do several passes | `comments/pass-N/comments.json`. Each run = new pass; `--pass N` adds to pass N; old passes stay loadable. Questions are re-added to a new pass unless an earlier pass resolved or deleted them. Tried and dropped: `--continue`, lazy pass creation (only on first comment) |
| 37 | "Delete all comments" should delete | Not possible: difit's API shows resolve and delete-all the same way (threads gone). Kept as resolve. A reply `delete` moves the thread to a `deleted` list (recoverable), not dropped |
| 38 | Logs under each pass | Done, then dropped with the move to one difit server: the port is chosen by the script (`--port`), so no log is needed |
| 39 | Minimal top bar | Only the buttons: « (hide sidebar), Prev, Next, Stop. Atomic mode adds the commit subject (hover = full message); sidebar shows only the short hash. No subtitle under the heading |
| 40 | Collapsible sidebar | « / » button and Alt+B; choice kept in localStorage |
| 41 | Keep the plumbing simple and minimal; drop features if needed | Dropped: bash wrapper, npx lookup, logs, lock file and `stop`, pool of difit servers and prefetch, tabs mode, `--continue`, lazy passes, rename following, tip→commit mapping |
| 42 | Readable by a human and modular; HTML separate | 3 files in `scripts/`: `review.py` (command, branches, items, difit, page server), `comments.py` (no difit or HTTP: pass file, saving, commit→tip), `page.html` (plain HTML/CSS/JS, data from `/api/state`). Kept under `scripts/`, not a new `review/` folder |
| 44 | Where does extending the atomic branch belong? | Own file `atomic.py` (branches + `extend`), as row 27: it maintains the atomic branch (block 2, documented in `1-atomic-branch.md`), and it is the only code that changes a branch. `review.py` imports `Branches` from it and never changes a branch. Room for the other deterministic atomic-branch steps (zero-diff check, commit list) |
| 43 | Scripts independent of the PR to review | Branches from git (checked-out branch, `<branch>-atomic`, origin's default branch; `BRANCH`/`MAIN` override). Inputs only from the package's files: session table, commits table, `questions.json` |
| 45 | Revisit reviewing tests: difit on test files only, information given gradually (reverses row 30) | `review.py tests`: one step per behaviour, rows from the step table in `3-tests.md`; the step's diff uses `git diff --function-context`, so each test is shown whole; bar shows "Step n/N · behaviour" |
| 46 | Test by test, or grouped? | Grouped. Test by test = ~30 page loads and split fixtures. First 7 behaviour steps; steps that ended up showing the same diff were merged, leaving one step per module under test (4 in the trial) |
| 47 | Guess first ("how would you test this?" before the diff) and a "Claims / Check" comment on each test | Both built, both dropped by the user. Kept instead: the code under test next to its tests, by adding the source files to the step's *Files* (no code change) |
| 48 | Keep the "not tested" and "fail-before" tables as they were (visible, not held back to the end) | Unchanged at the bottom of `3-tests.md` |
| 49 | "Open in editor" missing on hover in sessions and tests modes | Cause: difit hides it for a diff on stdin (`openInEditorAvailable: !options.stdinDiff`), and git mode has no file filter. Solved by rows 53–54 |
| 50 | Click a test's name to go to the function it tests, inside difit | `links.py`: "🔗 Tests: [`f`](#file-F-chunk-C-line-L)" on each test's `def` line, "🔗 Tested by: …" on each function. Calls found with `ast`, through the test file's helpers; kept if defined in the step's source files. Both directions kept: Back does not scroll back. Not saved (ids `link-…`), re-added each time a step opens |
| 51 | Link comments collapsed by default, or in another colour | Neither possible in difit 5.0.12 (see facts). A 🔗 prefix instead. One direction only was offered to cut the count; user kept both |
| 52 | Open the test review in unified view by default | Already so: difit keeps `diffViewMode` in `~/.difit/config.json`, which every difit server reads (its browser storage is per port, so it is lost between runs). One setting for all modes; a tests-only setting would be ~5 lines (`DIFIT_CONFIG_DIR` to a copied config), not done |
| 53 | A simple way to open the file in the editor | Tried: a "✎" at the end of each 🔗 comment, opening its `def` line through the review page's `GET /api/edit` (a `//localhost:PORT` link, so difit opens it in the same frame; the 204 reply leaves difit's page as it is). Removed by the user: the editor list of row 54 is enough. The route stays, for that list |
| 54 | Link the editor to the file being reviewed, inside a collapsible | Sidebar `<details>` "✎ Open in editor (n)": the files of the item on screen, each opened at its first changed line through `GET /api/edit?file&line`, which runs the editor set in difit's settings (`code -g %file:%line`) and replies 204; only files tracked in the repo. Every mode (tests, sessions, commits, whole PR); deleted files left out; open/closed kept in localStorage |
| 55 | Save test comments separately? | No: one file per pass, and comments follow the code (row 34), so a comment on a test file shows in every mode. A tests run is a pass of its own anyway; `--pass N` joins it to another. To pick them out, filter on `tip.filePath` starting `tests/`: `item` is where a thread was *last* changed, so it moves if a reply is written in another mode |
| 56 | Delete the passes that are not needed | Kept only passes with reviewer content (written, replied, resolved or deleted threads); the others held untouched copies of the preloaded questions. Questions resolved in an earlier pass stay skipped, as that is read only from passes that resolved them |
| 57 | Per-test "behaviours the tests check" table in the tests file is not worth having | Dropped: it repeats the difit `def`-line links, and its line numbers go stale. Keep only the gap sections (not tested; bug-fix fail-before test); put one-off notes (unchanged test, renamed test) in the step table's Behaviour column |
| 58 | A minimal version: aim and diagrams in one tab, atomic branch, review with difit, review tests with difit | Minimal layout, see above; trial in `crabs-exploration/pr-review-minimal/`. Dropped from the tabs: signatures, sequence diagram, predict, red flags |
| 59 | Leave the tests out of the first difit review; keep code comments and test comments apart, as two reviews with their own passes (reverses row 55) | Code modes (`all`, `atomic`, `sessions`) never show a test file; `tests` mode is the tests review. Passes in `comments/code/` and `comments/tests/`, numbered apart; questions split into `questions-code.json` and `questions-tests.json`. A comment written on a source file during the tests review stays in the tests review |
| 60 | Keep difit's own "Open in editor" (lost when the test files were filtered out with a diff on stdin) | difit's git mode has no path filter, so `review.py` makes a commit object with the base's files plus only the item's files (temporary index, `commit-tree`; no ref changed) and passes `<commit> <base>`. Used for sessions, the whole PR and atomic commits with test files; checked: same diff as `git diff -- files` for all 41 items, refs unchanged. Tests mode stays on stdin: its link ids come from the `--function-context` diff it sends |
| 61 | (found while building 58) Preloaded questions go stale as the PR moves on | Re-anchored each question at the tip, checked with `sed -n`; dropped those that later commits settled (5 of 10) |
| 62 | Flags to include the tests in the code review, and to leave out the preloaded questions | `--with-tests` (code modes only; tests-only commits come back in atomic mode; comments stay in `comments/code/`; sessions show only test files listed in the table) and `--no-questions` (both reviews; questions already in a reopened pass stay). `tests --with-tests` exits with an error |
| 63 | No list of section links at the top of a file; show the sections below the first one collapsed | Minimal layout: each file's first `##` section stays open, each later one is a `<details>` with a bold `<summary>` (no `##` heading, no back-to-top link; replaces rows 19–20 there). Links to a section became its name in italics, as a link cannot open a closed `<details>`. `mermaid.html` also draws on `toggle` (captured, as it does not bubble): diagrams in a closed `<details>` come out blank otherwise. `review.py` still reads the tables inside them |
| 64 | Drop resuming from item N or a commit hash (row 23) | Minimal layout: removed the `start` argument, `start_index` and the page's `state.start`; the page opens the first item. The sidebar already opens any item in one click and greys out the ones opened in the pass, and comments are saved per pass. The rule had grown fiddly: digits vs hash, and the numbers of skipped test-only commits. `Item.number` kept for the sidebar |

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
- In-page anchors as `<a id="sig-x"></a>`: works in VS Code, GitHub and Quarto. Put them under a `##` heading, never above a file's `# ` heading (see gotchas).
- Back to top: `[↑ Back to top](#top)`, no anchor anywhere. With no `id="top"` on the page, browsers (HTML spec) and GitHub scroll to the page top.

Gotchas:

- Without `render: [index.qmd]`, Quarto renders every `.md` to a stray `.html` next to it.
- Mermaid in a hidden tab draws blank; draw on `shown.bs.tab`. Same in a closed `<details>`: also draw on `toggle`, listened with capture.
- `securityLevel: "loose"` is needed for `click` links in diagrams.
- `quarto render` fails in the sandbox ("unable to open database file"): it writes `~/Library/Caches/quarto`. Run outside the sandbox.
- Quarto marks diff `+` lines `span.va` and `-` lines `span.st`; colour the parent line span with `:has()`. Use `inline-block; width:100%`, not `block` (doubles line spacing).
- Diamonds make tall diagrams; use plain boxes when the diagram is an index.
- A file's `# ` heading becomes a tab label, not a scroll target: `#workflow` goes nowhere.
- Anything above a file's `# ` heading lands in the *previous* file's tab. An `<a id="top">` there sits in a hidden tab, so links to it do nothing.
- Do not add `id="top"` anywhere (e.g. `[]{#top}` in `index.qmd`): it overrides the browser's built-in page-top for `#top`.
- Checked with Quarto 1.9.37, mermaid 11.4.1.

## difit runner (`scripts/`)

Rewritten 2026-11-24 (feedback 30–44); tests mode and editor links added 2026-11-25 (feedback 45–56). Example: `example/scripts/`, about 1,250 lines in 5 files.

```
review.py atomic   [--pass N]   code review: one atomic commit at a time
review.py sessions [--pass N]   code review: rows of the session table
review.py all      [--pass N]   code review: base..branch, like "Files changed"
review.py tests    [--pass N]   tests review: the test steps of 3-tests.md (feedback 45–51)
(full layout only: a start item, [N|SHA] or [N], dropped in the minimal layout, feedback 64)
atomic.py extend                      add the PR branch's new commits to the atomic branch

options: --with-tests (code review: show test files too), --no-questions (no preloaded questions)
```

How it works:

| Need | How |
|---|---|
| Move between items easily | A review page (`page.html`) served by `review.py` on a free local port: sidebar of items, the chosen item's difit in an iframe |
| Low memory | One difit server at a time (~65 MB each); choosing another item saves, stops it, starts the next (~0.5 s) |
| Know difit's port without logs | Script picks a free port and passes `--port` (difit tries port+1 only if it is taken) |
| Comments as the only record | difit starts `--clean`, then gets the item's saved threads with `--comment` (ids kept, so saving matches by id) |
| Save as you go | Every 1 s: `GET /api/comments-json`; compare with the last look (ids and bodies only, difit adds other fields); write only changes |
| Resolve / delete | Thread gone from difit → `resolved`; a reply `delete` → `deleted` |
| Comments in every mode | `commit` place for threads written on a commit; `tip` place found each run with `git blame base..rev`: a line is named by (commit that last changed it, line there), same name in every revision |
| Outdated | No tip line → shown inline only on the commit; listed in the sidebar in tip modes |
| Questions on the right commit | `git blame` the tip line on the atomic branch → (commit, line there) |
| Atomic branch behind the PR branch | Tip mapping off for the run, one note printed, suggests `atomic.py extend` |
| Session diffs | `git diff -M base branch -- files` on stdin (`difit -`). Minimal layout: a commit with only the item's files, in git mode (feedback 60) |
| Test files out of the code review | `atomic.is_test(path)`; items keep their table numbers (`Item.number`), so `atomic 16` still means commit 16 |
| Testing without a browser | `REVIEW_NO_BROWSER=1`; act as the reviewer with `POST /api/comments` on difit; a copy of `pr-review/` keeps real comments safe |

Facts checked in difit 5.0.12 source:

- `GET /api/comments-json` returns the threads; `POST /api/comments` replaces them (the page uses it).
- `--comment` imports accept `id`, `createdAt`, `updatedAt`, `author`; replies attach by file and position.
- Closing the tab ends the server 100 ms later, unless `--keep-alive`.
- The server keeps comments per (base, target) and has an in-page revision picker, but the page does not read base/target from its URL and lists any commits, without our titles: not used.
- The page never sets `document.title`, and nothing stops it being framed: so the wrapper page sets the tab title.
- "Delete all comments" and resolve look the same through the API (threads gone).
- `npx -y difit@X` contacts the npm registry on every start, even when cached (~2–4 s).
- "Open in editor" is off for a diff on stdin (`openInEditorAvailable: !options.stdinDiff`, and `POST /api/open-in-editor` refuses); the CLI has no path filter for git mode (`--help` of 5.0.12). Workaround: a commit holding only the files to show (feedback 60).
- Diff line ids are `file-F-chunk-C-line-L` (indices in the diff; `-old`/`-new` added in split view), so they can be worked out from the diff the script sends. A markdown link `[x](#id)` in a comment keeps its href (no new tab) and scrolls to the line, even ~14,000 px away. Back clears the hash but does not scroll back. Checked in headless Chrome over CDP (Node's built-in `WebSocket`), unified view only.
- Comments are markdown (remark-gfm), raw HTML dropped: no colours. A thread's collapsed state is internal (`useState(false)`), not settable from the import.
- Links in comments: `http…` opens in a new tab (`target="_blank"`); any other allowed form (`#id`, `//host/path`) opens in the same frame. `vscode:` and other schemes are dropped. A 204 reply to a same-frame link leaves the page as it is.
- User settings live in `~/.difit/config.json` (or `$DIFIT_CONFIG_DIR/config.json`): `diffViewMode`, theme, and the editor (`appearance.editor.command`, `argsTemplate` with `%file`, `%line`). Browser storage is per origin, so per port.

Gotchas from this round:

- Python buffers stdout when it is not a terminal: `sys.stdout.reconfigure(line_buffering=True)`.
- A CSS `display: flex` overrides the `hidden` attribute: add `[hidden] { display: none !important; }`.
- A blame header line must be matched strictly (`^[0-9a-f]{40} \d+ \d+`): a long commit summary can look like one.
- When a run stops, stop the difit on screen too, or it is left running.

UNSURE: replies of two threads on the same line may attach to the wrong thread on import.

## Deterministic or LLM?

| Step | Deterministic option | Status |
|---|---|---|
| File triage (+/-, bucket) | `git diff --numstat -M`; bucket by path rules | used |
| Line anchors correct | script: each `file:line` exists and matches a name | idea |
| Signature diff | `scripts/signature_changes.py BASE TIP [PATH]` (`ast` compare); or `griffe check` | used; found the same 23 changes as the hand-made list |
| Component diagram | import graph at base and tip (`pydeps`, or `ast` imports) → mermaid | idea; LLM picks what to show |
| Flow diagram | call graph from `main` (`pyan3`, `code2flow`) | idea; noisy, LLM picks the path and labels |
| Box ↔ signature link | function name in box ↔ def name in diff | idea, needs boxes named by function |
| Mermaid valid | `mmdc`, or `check-mermaid.sh` | idea |
| Atomic branch mechanics | temp index + `commit-tree`; final-tree equality check | used |
| Atomic branch grouping | none; needs judgment | LLM |
| Atomic branch update | tree-hash match + `commit-tree` per new commit (`atomic.py extend`) | used |
| Question → commit | `git blame` on atomic branch | used |
| Test file or code file | path rule `atomic.is_test` | used (minimal layout) |
| Code review without tests, in git mode | commit with only the item's files (temp index + `commit-tree`) | used (minimal layout) |
| Test → function it tests | `ast` calls of the test, through its file's helpers, matched to defs in the step's source files (`links.py`) | used; some extra links (calls made to compute expected values, arg parsers) |
| difit runs and saving | `review.py` | used |
| Comment place, commit → tip | `git blame base..rev` line names | used |
| Tests added/removed | `pytest --collect-only -q` at base vs tip, diff the lists | idea |
| Changed lines not tested | `pytest --cov` + `diff-cover` | idea; replaces the grep-based "not tested" table |
| CI and skip/xfail changes | `git diff -- .github`; grep `skip\|xfail` in test diff | used |
| Duplicate helpers | clone detection (`pylint --enable=duplicate-code`, `jscpd`) | idea; LLM still judges "same intent" |
| Aim, questions, red-flag reading | none | LLM |

## Signatures view: how changes are selected

- `scripts/signature_changes.py BASE TIP [PATH ...]` lists top-level defs and UPPER_CASE constants that are added, removed or changed. Output: tab-separated file, status, name, signature.
- Trial PR: the script found 23 changes; the hand-made list had all 23.
- Still by hand (LLM or reviewer): config keys and script arguments; behaviour-only changes with the same signature; grouping changes under flowchart boxes.
- Not covered by the script: class methods, nested functions.
- State the selection rule in one sentence at the top of the signatures file (user feedback 18).

## Open ideas for the skill

- Reuse `dev/skills/proposal/scripts/check-mermaid.sh` to validate diagrams.
- Reuse `dev/skills/writing-style` rules for the summary file.
- Optional step: strip comments on the scratch branch (makes the final diff non-empty).
- Signatures view as two panes: flowchart fixed on the left, hover a box to show its diff on the right (custom JS in Quarto).
- Save the atomic grouping (which original change went to which commit), so a full rebuild after a big PR change can reuse it. The trial's `build_stages.py` was one-off string replacements in a session scratchpad.
- Give the agent one prompt per pass: `comments/pass-N/comments.json` (open threads with their tip lines) at the end of block 2.
