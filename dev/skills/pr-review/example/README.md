# Example: PR review package (trial PR)

A review package for a PR in `crabs-exploration` (branch `smg/add-ellipse-params-to-tracks`, tip `9942560`), 2026-11-25. Its commands use the default folder name, `pr-review/`. Design choices: [DECISIONS.md](../DECISIONS.md).

| Tab | File |
|---|---|
| Aim and diagrams | `1-general/1-aim.md` |
| Atomic branch | `2-review/1-atomic-branch.md` |
| Review code with difit | `2-review/2-code.md`, `2-review/questions-code.json` |
| Review tests with difit | `2-review/3-tests.md`, `2-review/questions-tests.json` |

`scripts/` is the full example's, changed for two reviews: test files left out of the code modes (`atomic.is_test`), comments in `comments/code/` and `comments/tests/`, and code items shown in difit's git mode through a commit holding only their files.

Known stale parts: the diagrams, line numbers and atomic commits table are as of `1b9c04f`; the questions were re-anchored at `9942560`.

Links like `../../crabs/...` point into the reviewed repo, so they do not resolve here. Not copied: `_site/`, `.quarto/`, `comments/`.
