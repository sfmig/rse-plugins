# pr-review: design decisions

The final choices behind [SKILL.md](SKILL.md), one line each, with the reason.

- Numbers in brackets are rows of the *User feedback* table in the design notes, deleted in `61d084d`: `git show 61d084d^:dev/skills/pr-review/NOTES.md`.
- [MAINTAINING.md](MAINTAINING.md) holds the difit and Quarto facts, for changing the fixed files.

## Aim

- **Maps and indexes, not judgments.** The reviewer reads the code and decides. The skill only orders the PR and points at what needs a second look.
- **Four tabs** [58]: aim and diagrams, atomic branch, code review, tests review.
    - Left out: signatures, sequence diagram, "predict first", red flags. Each one was extra reading for little gain.
    - They stay possible extras, in an earlier example with more tabs, deleted in `aa709dc`: `git show aa709dc^:dev/skills/pr-review/example/README.md`.

## Pages

| Decision | Reason |
|---|---|
| Aim as **Before this PR** / **With this PR**, naming real variables and files [17] | Plain words; says what *changed*, not only what exists |
| Flowchart, not sequence diagram [2] | Sequence diagrams were hard to read |
| Legend subgraph, `click` links pinned to a commit, plus a links table [3, 4] | GitHub strips `click`, so the table keeps links reachable |
| General to detailed: aim → components → flow [10] | A reader who stops early still knows what the PR does |
| First `##` open, later sections in `<details>` [63] | Short page at a glance; no section list or back-to-top links |
| Refer to a section by name in italics [63] | A link cannot open a closed `<details>` |
| Tables, short bullets, `file:line`; no quality words [5, 16] | Concise; the reviewer judges |
| `.md` is the source; Quarto only includes it [7, 8] | Tabs in the browser, and plain Markdown still works in VS Code and GitHub |
| One `# ` heading per page, on line 1 | It becomes the Quarto tab name; anything above it lands in the previous tab |

## Atomic branch

- **Grouped by the agent, built by `build_atomic.py`** [25]. Grouping needs judgment; the commits and the zero-diff check do not, so a script makes them the same way every time.
- **Order: plumbing → core → wiring → tests → docs.** Tests in their own commits, so the code review can skip them [59].
- **Temporary index and `commit-tree`.** The working tree and the PR branch are never touched.
- **Zero diff with the PR tip** is the only check, and `build_atomic.py` creates no branch without it. Middle commits are not run.
- **Extend, do not rebuild** [25, 44]. `atomic.py extend` finds the commit with the same tree and replays later ones. A rebuild changes every hash, item number and saved comment.
- **Only `build_atomic.py` and `atomic.py extend` write a branch, and only `<branch>-atomic`** [27, 44]. `review.py` is read-only on git.

## The two reviews

- **Code first, without tests; then tests, next to the code they test** [59]. Two reviews, each with its own passes and its own questions file.
- **Test file rule:** `tests/` folder, or `test_*.py`, `*_test.py`, `conftest.py`. Shared by the skill and the scripts.
- **Code review modes:** `all` (like "Files changed"), `atomic` (one commit at a time), `sessions` (50–400 changed lines per sitting) [13, 24].
- **Tests review: one step per module under test**, with its source files [46, 47]. Test by test meant ~30 page loads and split fixtures.
- **Kept on the tests page:** not tested, bug-fix fail-before [48]. Dropped: per-test "behaviours checked" table [57], guess-first and claim/check comments [47].
- **Weight column 🔴 🟠 🟢** [33]. How much a reviewer must think, not the line count.
- **Flags:** `--with-tests`, `--no-questions` [62]. No resume from item N [64]: the sidebar opens any item in one click.

## Comments and questions

- **One comments file per pass**, kept as the only record [36]. Saved every second.
- **Comments follow the code to the tip** with `git blame`, as on GitHub [34, 35]. Outdated ones show inline only on their commit.
- **Resolve and delete-all look the same** in difit's API [37]. Both are kept as resolve; a reply `delete` moves a thread to `deleted`.
- **Questions anchored on added lines, new side, at the tip.** difit may not show a comment on another line.
- **Re-check questions at the tip** [61]. Later commits settle some of them.
- **Ask about what the diff does not show:** concurrency, reruns, partial failure, untested paths, input assumptions.
- **The agent answers in the comments file, not the chat**, and changes no code until the reviewer resolves a thread.

## Scripts

- **Plain and modular, HTML apart** [41, 42]: `review.py`, `comments.py`, `atomic.py`, `links.py`, `page.html`.
- **Facts from git, not recorded** [26, 43]. Branch, base and atomic branch are worked out; inputs are only the package's tables and question files.
- **One review page with a sidebar; difit in an iframe** [32]. One difit server at a time, installed once: an item opens in under 0.5 s [31].
- **Code review in difit's git mode**, with a commit holding only the item's files [60]. Keeps difit's "Open in editor"; a diff on stdin disables it.
- **Deterministic where possible** [15]: `facts.py`, `build_atomic.py`, `draft_tables.py`, `check_package.py`, `check-mermaid.sh`. Drafts judge nothing: the agent edits them. The LLM writes the aim, the diagrams, the atomic grouping and the questions.
