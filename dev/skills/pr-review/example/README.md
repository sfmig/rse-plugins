# Example: PR review package (trial PR)

A review package for a PR in `crabs-exploration` (branch `smg/add-ellipse-params-to-tracks`, tip `9942560`), 2026-11-25. Its commands use the default folder name, `pr-review/`. Design choices: [DECISIONS.md](../DECISIONS.md).

| Tab | File |
|---|---|
| Aim and diagrams | `1-general/1-aim.md` |
| Atomic branch | `2-review/1-atomic-branch.md` |
| Review code with difit | `2-review/2-code.md`, `2-review/questions-code.json` |
| Review tests with difit | `2-review/3-tests.md`, `2-review/questions-tests.json` |

Only the pages that describe the PR are here. `init_package.py` adds the rest to each package: the Quarto page from [`../template/`](../template/) and the difit scripts from [`../scripts/package/`](../scripts/package/).

Known stale parts: the diagrams, line numbers and atomic commits table are as of `1b9c04f`; the questions were re-anchored at `9942560`.

Links like `../../crabs/...` point into the reviewed repo, so they do not resolve here. The package's `code-base-url` was `https://github.com/SainsburyWellcomeCentre/crabs-exploration/blob/1b9c04f9c0860b94912ca4d11730964029235ca2/`. Not copied: `_site/`, `.quarto/`, `comments/`.
