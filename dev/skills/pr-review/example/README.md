# Example: PR review package (trial PR)

A copy of the `pr-review/` folder made for the trial PR in `crabs-exploration`
(branch `smg/add-ellipse-params-to-tracks`, tip `516c6c4`). Copied 2026-11-20; updated 2026-11-23
(scripts moved to `scripts/`, see NOTES.md feedback 22–29) and 2026-11-24 (difit runner
rewritten as a review page in Python, see NOTES.md feedback 30–44) and 2026-11-25
(tests and red flags moved into `2-review/`, `tab-sections.lua` colours the Quarto tabs by block).

| Block | State |
|---|---|
| `1-general/` | **Good example.** Approved by the user; follow it for content, style, section links and back-to-top links |
| `2-review/` | Draft; `1-atomic-branch.md` (commits with weights) `2-difit.md` (how to use the scripts), `3-tests.md`, `4-red-flags.md` |
| `scripts/` | **Good example.** `review.py` (command, review page server, difit; read-only on git), `comments.py` (comments of a pass, commit→tip lines), `page.html` (the review page), `atomic.py` (branches, `atomic.py extend`). Not tied to this PR |

Links like `../../crabs/...` point into the reviewed repo, so they do not resolve here.
In the Quarto page they go to GitHub through `code-base-url` in `_quarto.yml`.
Not copied: `_site/`, `.quarto/` (build output), `comments/` (reviewer notes).
