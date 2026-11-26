# pr-review: maintaining the fixed files

Facts and traps for changing the files `init_package.py` copies into each package: the difit scripts in [`scripts/package/`](scripts/package/) and the Quarto page in [`template/`](template/).

- Running the skill does not need this file. The reasons behind the design are in [DECISIONS.md](DECISIONS.md).
- Checked with difit 5.0.12, Quarto 1.9.37 and mermaid 11.4.1.

## difit

What `scripts/package/` relies on, checked in the difit 5.0.12 source:

| Fact | Used by |
|---|---|
| `GET /api/comments-json` returns the threads; `POST /api/comments` replaces them | `review.py` saves every second; tests act as the reviewer through `POST` |
| `--comment` imports keep `id`, `createdAt`, `updatedAt`, `author`; replies attach by file and position | Saved threads reloaded with their ids, so saving matches by id |
| Started with `--clean`, then the item's threads with `--comment` | The pass file is the only record |
| Closing the tab ends the server 100 ms later, unless `--keep-alive` | One server per item; choosing another item stops it |
| `--port N` tries `N+1` only if `N` is taken | `review.py` picks a free port, so no log is needed |
| Resolve and "Delete all comments" look the same through the API: threads gone | Both saved as `resolved`; a reply `delete` moves a thread to `deleted` |
| "Open in editor" is off for a diff on stdin; git mode has no path filter | Code review passes a commit holding only the item's files, in git mode |
| Diff line ids are `file-F-chunk-C-line-L` (`-old` / `-new` in split view) | `links.py` works them out from the diff it sends, so tests mode stays on stdin |
| `[x](#id)` in a comment scrolls to that line in the same frame; `http…` opens a new tab; `vscode:` is dropped | 🔗 links between tests and functions; `//localhost:PORT/api/edit` returning 204 leaves the page as it is |
| Comments are markdown (remark-gfm), raw HTML dropped; a thread's collapsed state cannot be set on import | No coloured or collapsed link comments: a 🔗 prefix instead |
| The page never sets `document.title` and can be framed | `page.html` frames it and sets the tab title |
| Settings in `~/.difit/config.json` (or `$DIFIT_CONFIG_DIR`): `diffViewMode`, theme, editor `command` and `argsTemplate` with `%file`, `%line` | Unified view kept across runs; `/api/edit` runs the same editor |
| `npx -y difit@X` contacts the npm registry on every start (~2–4 s) | Installed once with `npm i -g difit@5.0.12` |

UNSURE: replies of two threads on the same line may attach to the wrong thread on import.

Traps in the scripts:

- Python buffers stdout when it is not a terminal: `sys.stdout.reconfigure(line_buffering=True)`.
- CSS `display: flex` overrides the `hidden` attribute: add `[hidden] { display: none !important; }`.
- Match a `git blame --porcelain` header strictly (`^[0-9a-f]{40} \d+ \d+`): a long commit summary can look like one.
- When a run stops, stop the difit on screen too, or it is left running.
- npm in the sandbox: `npm_config_cache=$TMPDIR/npmcache`.
- Test without a browser: `REVIEW_NO_BROWSER=1`, on a copy of the package so real comments stay safe.

## Quarto page

The `.md` pages stay the source. Quarto only includes them, so VS Code and GitHub still render them.

| File | Role |
|---|---|
| `index.qmd` | `{.panel-tabset}` with one `{{< include … >}}` per page; each page's `# ` heading becomes its tab |
| `_quarto.yml` | `render: [index.qmd]`, `output-dir: _site`, `code-base-url` pinned to the PR commit |
| `mermaid.lua` | ` ```mermaid ` → `<pre class="mermaid">`; `../` links → `code-base-url` |
| `tab-sections.lua` | One row of tabs, coloured by section; runs at `pre-ast`, before Quarto builds the tabs |
| `gh-alerts.lua` | GitHub alerts (`> [!NOTE]` …) → Quarto callouts |
| `mermaid.html` | Loads mermaid; draws a diagram when its tab or `<details>` is first shown |
| `styles.css` | Diff lines coloured like GitHub |

Traps:

- Without `render: [index.qmd]`, Quarto writes a stray `.html` next to every `.md`.
- Mermaid draws blank in a hidden tab or closed `<details>`. Draw on `shown.bs.tab`, and on `toggle` listened with capture (it does not bubble).
- `click` links in diagrams need `securityLevel: "loose"`.
- Quarto marks diff `+` lines `span.va` and `-` lines `span.st`. Colour the parent line with `:has()`, as `inline-block; width: 100%` (`block` doubles the line spacing).
- Anything above a page's `# ` heading lands in the previous tab.
- A tab's heading is not a scroll target: `#workflow` goes nowhere.
- Never add `id="top"`: it overrides the browser's own page top for `#top`.
- `quarto render` fails in the sandbox ("unable to open database file"): it writes `~/Library/Caches/quarto`.

## Ideas not done

- Steps that could be scripts instead of LLM work:
    - `file:line` anchors in prose checked against the code (only `` `path:N` `` is checked now).
    - Component diagram from the import graph at base and tip (`pydeps`, or `ast` imports).
    - Tests added or removed: `pytest --collect-only -q` at base and tip, then diff.
    - Changed lines not tested: `pytest --cov` with `diff-cover`, to replace the grep-based *Not tested* table.
    - Duplicate helpers: `pylint --enable=duplicate-code` or `jscpd`.
- Save the atomic grouping (which change went to which commit), so a rebuild after a rebased PR can reuse it.
- Give the agent one prompt per pass, built from the open threads of `comments/*/pass-N/comments.json`.
- `signature_changes.py` misses class methods and nested functions.
