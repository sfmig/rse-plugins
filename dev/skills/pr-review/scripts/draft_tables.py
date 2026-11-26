#!/usr/bin/env python3
"""First drafts of the package's tables, for the agent to edit (it does not judge).

    draft_tables.py [commits | sessions | tests | not-tested | components] [--coverage FILE]

Run from inside the reviewed repo, with the PR branch checked out (or set BRANCH=...).
Read-only: prints Markdown, writes nothing. With none named, prints all five.

  commits     the commits table of 1-atomic-branch.md, from <branch>-atomic: number,
              hash, subject as purpose, files, +/-. Weight is left as TODO.
  sessions    the session plan of 2-code.md: the code files (no tests), a file of
              200+ changed lines on its own, the rest by folder, up to 400 lines a session.
  tests       the test steps of 3-tests.md: each changed test file with the changed
              code file of the same name (test_x.py -> x.py), else the changed code files
              it imports; test files with the same code files share a step.
              Behaviour is left as TODO.
  not-tested  the changed functions of the code whose name no test file has, at the
              tip (a name match: a mention is not a test). With --coverage FILE, a
              coverage.py XML report (pytest --cov --cov-report=xml, run by the user),
              also the added lines that no test ran.
  components  the two component diagrams of 1-aim.md, before (base) and after (tip),
              as mermaid: the top-level functions of the changed code files that the
              PR adds, removes or changes, their direct callers and callees there, and
              the calls between them (found with `ast`, through each file's imports).
              Green = added or changed. Not shown: methods, calls through variables,
              code outside the changed files (scripts, stores, other packages).
"""

import ast
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent / "package"))
from atomic import Branches, git, git_ok, is_test  # noqa: E402
from facts import changes, files_changed, rename_target  # noqa: E402

ALONE = 200  # changed lines from which a file is a session of its own
SESSION = 400  # most changed lines in a session of several files


def lines_of(added, removed):
    return sum(int(x) for x in (added, removed) if x.isdigit())


def short(paths, at_most=3):
    names = [f"`{PurePosixPath(p).name}`" for p in paths]
    return ", ".join(names) if len(names) <= at_most else ", ".join(names[:at_most]) + f", +{len(names) - at_most} more"


def commits_table(b):
    if not b.has_atomic():
        return f"No branch {b.atomic}: build it first (build_atomic.py).\n"
    out = ["| # | Commit | Purpose | Files | +/- | Weight |", "|---|---|---|---|---|---|"]
    for n, sha in enumerate(git("rev-list", "--reverse", f"{b.base}..{b.atomic}").split(), 1):
        rows = [r.split("\t", 2) for r in git("diff", "--numstat", "-M", f"{sha}^", sha).splitlines()]
        added = sum(int(r[0]) for r in rows if r[0].isdigit())
        removed = sum(int(r[1]) for r in rows if r[1].isdigit())
        paths = [rename_target(r[2]) if " => " in r[2] else r[2] for r in rows]
        subject = git("log", "-1", "--format=%s", sha).replace("|", "\\|")
        out.append(f"| {n} | `{sha[:7]}` | {subject} | {short(paths)} | +{added}/-{removed} | TODO |")
    return "\n".join(out) + "\n\nWeight: `🔴 high`, `🟠 med` or `🟢 low`: how much a reviewer must think.\n"


def sessions_table(b):
    files = [(old, new, lines_of(a, r)) for _, old, new, a, r in files_changed(b.base, b.branch)
             if not is_test(new)]
    sessions, small = [], defaultdict(list)
    for old, new, n in sorted(files, key=lambda f: f[1]):
        paths = [new] if old == new else [old, new]
        if n >= ALONE:
            sessions.append((paths, n))
        else:  # Python files by folder; the other files (docs, config, shell) apart
            small[(not new.endswith(".py"), str(PurePosixPath(new).parent))].append((paths, n))
    current, total, kind = [], 0, None
    for key in sorted(small):  # folders in path order, merged up to SESSION lines
        group = small[key]
        n = sum(x[1] for x in group)
        if current and (total + n > SESSION or key[0] != kind):
            sessions.append(([p for paths, _ in current for p in paths], total))
            current, total = [], 0
        current, total, kind = current + group, total + n, key[0]
    if current:
        sessions.append(([p for paths, _ in current for p in paths], total))
    out = ["| Session | Files | Lines | Done |", "|---|---|---|---|"]
    for i, (paths, n) in enumerate(sessions, 1):
        out.append(f"| {i} | {', '.join(f'`{p}`' for p in paths)} | {n} | [ ] |")
    return "\n".join(out) + "\n\nLines: added plus removed. Put related files together; keep sittings at about 50–400 lines.\n"


def module_paths(name, rev):
    """The files a dotted module name can be at rev: a/b.py or a/b/__init__.py."""
    base = name.replace(".", "/")
    return [p for p in (f"{base}.py", f"{base}/__init__.py") if git_ok("cat-file", "-e", f"{rev}:{p}")]


def imported_files(rev, path):
    """The repo files a .py file imports at rev (absolute imports only)."""
    text = git("show", f"{rev}:{path}", check=False)
    try:
        tree = ast.parse(text or "")
    except SyntaxError:
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found.update(module_paths(a.name, rev))
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.update(module_paths(node.module, rev))
            for a in node.names:  # from pkg import module
                found.update(module_paths(f"{node.module}.{a.name}", rev))
    return found


def tests_table(b):
    files = files_changed(b.base, b.branch)
    renamed = {old: new for s, old, new, _, _ in files if s == "R"}
    code = {new for _, _, new, _, _ in files if not is_test(new)} | set(renamed)
    deleted = {old for s, old, _, _, _ in files if s == "D"}
    # test_x.py tests x.py if the PR changes one; else the changed modules it imports.
    steps, shared = defaultdict(list), []
    for status, old, new, _, _ in files:
        if not is_test(new):
            continue
        rev = b.base if status == "D" else b.branch
        stem = PurePosixPath(new).stem.removeprefix("test_").removesuffix("_test")
        under = {p for p in code | deleted if p.endswith(".py") and PurePosixPath(p).stem == stem}
        if not under:  # no module of the same name: the changed modules it imports
            under = {renamed.get(p, p) for p in imported_files(rev, new) if p in code or p in deleted}
        (steps[frozenset(under)].append(new) if under else shared.append(new))
    out = ["| Step | Behaviour | Files | Done |", "|---|---|---|---|"]
    tested = set()
    for i, (under, tests) in enumerate(sorted(steps.items(), key=lambda kv: sorted(kv[0])), 1):
        tested |= under
        modules = ", ".join(f"`{PurePosixPath(p).stem}`" for p in sorted(under))
        paths = ", ".join(f"`{p}`" for p in [*sorted(under), *sorted(tests)])
        out.append(f"| {i} | TODO ({modules}) | {paths} | [ ] |")
    notes = []
    if shared:
        notes.append("Test files that import no changed code (fixtures, helpers): add each to the steps that use it: "
                     + ", ".join(f"`{p}`" for p in shared))
    untested = sorted(p for p in code if p.endswith(".py") and p not in tested and p not in renamed)
    if untested:
        notes.append("Changed .py code files that no changed test imports: " + ", ".join(f"`{p}`" for p in untested))
    return "\n".join(out) + "\n\n" + "".join(f"- {n}\n" for n in notes)


def covered_lines(report):
    """{path: set of line numbers with hits == 0} from a coverage.py XML report."""
    missed = defaultdict(set)
    root = ET.parse(report).getroot()
    sources = [s.text.rstrip("/") for s in root.iter("source") if s.text]
    top = git("rev-parse", "--show-toplevel")
    for cls in root.iter("class"):
        name = cls.get("filename")
        for src in sources or [top]:
            path = os.path.relpath(os.path.join(src, name), top)
            if not path.startswith(".."):
                break
        for line in cls.iter("line"):
            if line.get("hits") == "0":
                missed[path].add(int(line.get("number")))
    return missed


def added_lines(base, tip):
    out, path = defaultdict(set), None
    for row in git("diff", "-U0", "-M", base, tip).splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
        elif row.startswith("@@") and path:
            m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))?", row)
            start, count = int(m[1]), int(m[2] or 1)
            out[path].update(range(start, start + count))
    return out


def ranges(numbers):
    numbers, out = sorted(numbers), []
    for n in numbers:
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return ", ".join(str(a) if a == z else f"{a}-{z}" for a, z in out)


def not_tested_table(b, coverage=None):
    tests = [p for p in git("ls-tree", "-r", "--name-only", b.branch).splitlines() if is_test(p) and p.endswith(".py")]
    out = ["| Function | Change | Code |", "|---|---|---|"]
    for status, old, new, _, _ in files_changed(b.base, b.branch):
        if is_test(new) or status == "D" or not new.endswith(".py"):
            continue
        for change, key, _ in changes(b.base, b.branch, old, new):
            if not key.startswith("def ") or change == "removed":
                continue
            name = key[4:].split(".")[-1]
            if tests and git_ok("grep", "-q", "-w", name, b.branch, "--", *tests):
                continue
            line = next((n for n, l in enumerate(git("show", f"{b.branch}:{new}").splitlines(), 1)
                         if re.match(rf"\s*(async\s+)?def {re.escape(name)}\b", l)), "?")
            out.append(f"| `{key[4:]}` | {change} | `{new}:{line}` |")
    text = "Changed functions whose name no test file has, at the tip:\n\n"
    text += ("\n".join(out) if len(out) > 2 else "None.") + "\n"
    if coverage:
        missed = covered_lines(coverage)
        rows = ["| File | Added lines no test ran |", "|---|---|"]
        for path, added in sorted(added_lines(b.base, b.branch).items()):
            if path in missed and added & missed[path] and not is_test(path):
                rows.append(f"| `{path}` | {ranges(added & missed[path])} |")
        text += f"\nFrom {coverage} (only the files it measured):\n\n"
        text += ("\n".join(rows) if len(rows) > 2 else "None.") + "\n"
    return text


def dotted(path):
    return path[:-3].removesuffix("/__init__").replace("/", ".")


def resolve(module, scope):
    """The path in scope of a dotted module name (also under a src/ layout), or None."""
    for path in scope:
        d = dotted(path)
        if d == module or d.endswith("." + module):
            return path
    return None


def call_graph(rev, scope):
    """({(path, name)}, {(caller, callee)}) of the top-level functions of scope at rev."""
    trees = {}
    for path in scope:
        try:
            trees[path] = ast.parse(git("show", f"{rev}:{path}", check=False) or "")
        except SyntaxError:
            pass
    defs = {path: {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            for path, tree in trees.items()}
    nodes, edges = {(p, n) for p, d in defs.items() for n in d}, set()
    for path, tree in trees.items():
        modules, names = {}, {}  # alias -> path; alias -> (path, name)
        package = dotted(path).split(".")[:-1]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if (target := resolve(a.name, scope)):
                        modules[a.asname or a.name] = target
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:  # relative: from the file's package
                    up = package[: len(package) - node.level + 1]
                    base = ".".join([*up, *([node.module] if node.module else [])])
                for a in node.names:
                    if (target := resolve(f"{base}.{a.name}", scope)):
                        modules[a.asname or a.name] = target
                    elif (target := resolve(base, scope)):
                        names[a.asname or a.name] = (target, a.name)
        for name, fn in defs.get(path, {}).items():
            for call in ast.walk(fn):
                if not isinstance(call, ast.Call):
                    continue
                f, callee = call.func, None
                if isinstance(f, ast.Name):
                    callee = (path, f.id) if f.id in defs[path] else names.get(f.id)
                elif isinstance(f, ast.Attribute) and ast.unparse(f.value) in modules:
                    callee = (modules[ast.unparse(f.value)], f.attr)
                if callee in nodes and callee != (path, name):
                    edges.add(((path, name), callee))
    return nodes, edges


def mermaid(nodes, edges, changed, colour=True):
    """A flowchart LR of the changed functions, their direct callers and callees."""
    keep = {e for e in edges if e[0] in changed or e[1] in changed}
    shown = sorted(changed | {n for e in keep for n in e})
    ident = lambda n: re.sub(r"\W", "_", f"{PurePosixPath(n[0]).stem}_{n[1]}")
    label = lambda n: f'{ident(n)}["{PurePosixPath(n[0]).stem}.{n[1]}"]'
    lines = ["```mermaid", "flowchart LR"]
    linked = set()
    for a, z in sorted(keep):
        lines.append(f"    {label(a) if a not in linked else ident(a)} --> {label(z) if z not in linked else ident(z)}")
        linked |= {a, z}
    lines += [f"    {label(n)}" for n in shown if n not in linked]
    green = [ident(n) for n in shown if n in changed]
    if green and colour:
        lines += ["", "    classDef new fill:#d4edda,stroke:#2e7d32,color:#000", f"    class {','.join(green)} new"]
    return "\n".join(lines + ["```"]), len(shown)


def components_draft(b):
    files = [f for f in files_changed(b.base, b.branch) if not is_test(f[2]) and f[2].endswith(".py")]
    before_scope = [old for s, old, _, _, _ in files if s != "A"]
    after_scope = [new for s, _, new, _, _ in files if s != "D"]
    changed_before, changed_after = set(), set()
    for status, old, new, _, _ in files:
        for change, key, _ in changes(b.base, b.branch, old, new if status != "D" else old):
            if not key.startswith("def ") or "." in key[4:]:
                continue  # methods are not drawn
            if change != "added":
                changed_before.add((old, key[4:]))
            if change != "removed":
                changed_after.add((new, key[4:]))
    out = []
    for title, rev, scope, focus in (("Before", b.base, before_scope, changed_before),
                                     ("After", b.branch, after_scope, changed_after)):
        nodes, edges = call_graph(rev, scope)
        text, n = mermaid(nodes, edges, focus & nodes, colour=title == "After")  # before: no colours
        out.append(f"### {title} (`{git('rev-parse', '--short', rev)}`)\n\n{text}\n\n{n} boxes.")
    out.append("Arrows: caller to callee. Before: the functions the PR removes or changes, with "
               "their callers and callees. After: green = added or changed. Cut to the main path, "
               "add what the code calls outside these files (scripts, stores), and a short note "
               "per box on what changed.")
    return "\n\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    coverage = None
    if "--coverage" in args:
        i = args.index("--coverage")
        coverage = args[i + 1] if i + 1 < len(args) else sys.exit(__doc__)
        coverage = str(Path(coverage).resolve())
        del args[i:i + 2]
    tables = {"commits": commits_table, "sessions": sessions_table,
              "tests": tests_table, "not-tested": lambda b: not_tested_table(b, coverage),
              "components": components_draft}
    if len(args) > 1 or (args and args[0] not in tables):
        sys.exit(__doc__)
    os.chdir(git("rev-parse", "--show-toplevel"))
    b = Branches.from_git()
    for name in args or tables:
        if not args:
            print(f"## {name}\n")
        print(tables[name](b))


if __name__ == "__main__":
    main()
