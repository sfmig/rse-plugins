---
name: release
description: Get a research code repository ready to cite and archive - write or update CITATION.cff, check that the licence is consistent across the repo, and walk through the Zenodo/GitHub steps that mint a DOI.
when_to_use: Use when the user is preparing a paper, a software release or a DOI for their code, or asks about CITATION.cff, how to make their software citable, licence checks before publishing, or archiving on Zenodo.
argument-hint: "[version to release, e.g. v1.2.0]"
---

# Release

The version to release: $ARGUMENTS

If that is empty, use the latest git tag plus a bump the user confirms, or ask.

This skill covers three things, in order: **citation**, **licence**, **DOI**. Pinned environments and data provenance are out of scope; if the user asks for them, say so.

You edit files only in this repo, and only after the user agrees. You never create tags or GitHub releases, push, or touch Zenodo yourself: those are outward-facing and hard to undo. Give the user the exact steps and commands instead.

## 1. Gather the facts

Read, don't guess. Collect these before writing anything:

| Fact | Where to look |
|---|---|
| Title, description, version | `pyproject.toml`, `setup.cfg`, `package.json`, `DESCRIPTION` (R), README |
| Authors | Existing `CITATION.cff`, package metadata, `git shortlog -sne` |
| Licence | `LICENSE` / `COPYING`, the `license` field in package metadata, file headers |
| Repository URL | `git remote get-url origin` |
| Existing DOI | `CITATION.cff`, `.zenodo.json`, README badges |
| Last release | `git describe --tags --abbrev=0` |
| Related paper | README, `CITATION.cff` `preferred-citation`, ask the user |

`git shortlog` lists bots, duplicate identities and people who should not be authors. **Show the user the proposed author list and wait for them to confirm it.** Never invent ORCIDs, affiliations or name spellings: leave them out, or ask.

## 2. Citation: `CITATION.cff`

Write a new file, or update the existing one, at the repo root. Shape:

```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
type: software
title: "my-package"
abstract: "One or two sentences on what it does."
authors:
  - family-names: "Lovelace"
    given-names: "Ada"
    orcid: "https://orcid.org/0000-0000-0000-0000"   # only if the user gave it
    affiliation: "Some Institute"                    # only if the user gave it
version: "1.2.0"
date-released: "2026-11-20"   # the planned release date, ISO 8601
license: BSD-3-Clause         # SPDX identifier, same as LICENSE
repository-code: "https://github.com/org/my-package"
# doi: added after the first Zenodo release; see step 4
# preferred-citation: add a block of type `article` if users should cite a paper instead
```

- `version` and `date-released` must match the release you are preparing.
- If the user wants people to cite a paper, add `preferred-citation` with that paper's metadata. The software stays the top-level entry.
- Validate it. Run `cffconvert --validate -i CITATION.cff`, or `uvx cffconvert --validate -i CITATION.cff` if `cffconvert` isn't installed. Fix the errors before moving on. If neither command works, tell the user it wasn't validated.

## 3. Licence check

Report each row as ✅ / ⚠️ / ❌ in a table, with the file and line:

| Check | Pass when |
|---|---|
| A licence file exists | `LICENSE`, `LICENSE.md` or `COPYING` at the root |
| It's a recognised licence | The text matches a known SPDX licence, unedited |
| Metadata agrees | The package metadata `license` field and `CITATION.cff` `license` use the same SPDX identifier as the file |
| Copyright line is current | Holder and year range look right; ask if unsure who the holder is (often the employer) |
| No vendored code with another licence | No copied files or folders with their own licence headers, or they are acknowledged |
| Direct dependencies are compatible | List the direct dependencies' licences. Flag copyleft ones (GPL, AGPL) in a permissive project |

For dependencies, use what the ecosystem gives you, e.g. `pip-licenses` in the project environment, or the metadata of each package. If you can't get the licences reliably, list the dependencies and say they are unchecked.

Licence findings are prompts for the user to decide, not legal advice. Say so once, in the report.

## 4. DOI: Zenodo

The GitHub–Zenodo integration archives each **GitHub release** (not a bare tag) and mints a DOI for it. Give the user these steps, filled in for their repo:

1. Log in to [zenodo.org](https://zenodo.org) with GitHub. To rehearse first, use [sandbox.zenodo.org](https://sandbox.zenodo.org), whose DOIs are not real.
2. In Zenodo, open *GitHub* settings and switch the repository on. Do this **before** making the release; Zenodo ignores earlier releases.
3. Commit `CITATION.cff` and any licence fixes, then tag and publish a GitHub release, e.g. `gh release create v1.2.0 --generate-notes`.
4. Zenodo reads metadata from `CITATION.cff`. If the repo has a `.zenodo.json`, Zenodo uses that instead: check the two agree, or suggest removing `.zenodo.json`.
5. Zenodo gives two DOIs:
    - the **concept DOI**, which always resolves to the latest version. Use it in the README badge and in `CITATION.cff` `doi`.
    - the **version DOI**, for this exact release. Cite this one in a paper so readers get the code you used.
6. Add the concept DOI to `CITATION.cff` and the README in a follow-up commit.

If the repo already has a DOI, skip steps 1 and 2 and check that the switch in Zenodo is still on.

## Report

End with one short report:

1. **Changes made**: files edited, as a list.
2. **Licence table** from step 3.
3. **Your next steps**: the numbered steps from step 4, with the commands for this repo, and anything the user still has to confirm (authors, copyright holder, flagged dependencies).
