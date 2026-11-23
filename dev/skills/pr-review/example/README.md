# Example: PR review package (trial PR)

A copy of the `pr-review/` folder made for the trial PR in `crabs-exploration`
(branch `smg/add-ellipse-params-to-tracks`, tip `516c6c4`). Copied 2026-11-20; updated 2026-11-23
(scripts moved to `scripts/`, see NOTES.md feedback 22–29).

| Block | State |
|---|---|
| `1-general/` | **Good example.** Approved by the user; follow it for content, style, section links and back-to-top links |
| `2-review/` | Draft; `1-atomic-branch.md` and `2-difit.md` describe the scripts |
| `3-tests/` | Draft |
| `scripts/` | `review.sh` (difit runner), `extend-atomic.sh` (add new commits to the atomic branch), `config.sh` (branch names from git) |

Links like `../../crabs/...` point into the reviewed repo, so they do not resolve here.
In the Quarto page they go to GitHub through `code-base-url` in `_quarto.yml`.
Not copied: `_site/`, `.quarto/` (build output), `comments/` (reviewer notes).
