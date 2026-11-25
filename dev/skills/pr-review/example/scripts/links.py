"""Links between each test and the functions it tests, for tests mode.

Each changed test gets a comment on its `def` line, "🔗 Tests: [`f`](#...)", and each
function it calls gets one back, "🔗 Tested by: [`test_f`](#...)". Clicking a link
scrolls difit to that line. A "✎" at the end opens the comment's own `def` line in the
editor, through the review page's GET /api/edit (see review.py). That link starts
with `//localhost:PORT`, not `http:`: difit opens http links in a new tab, and others in
the same frame, where the 204 reply leaves difit's page as it is.

A test's calls are found with `ast`, following the helpers of its own test file
(so `test_main` -> `run_main` -> `main`), and kept if they are defined in a source
file of the same step. Only `def` lines that the diff shows get a link.

The links point at difit's line ids, `file-F-chunk-C-line-L`: the file, hunk and
line indices in the diff (unified view). They are not review comments: review.py
adds them to difit each time and never saves them (their ids start with "link-").
"""

import ast
import re
from urllib.parse import urlencode

from atomic import git

PREFIX = "link-"


def line_ids(diff):
    """{(path, new-side line): difit line id} for the lines a diff shows."""
    ids, f, c, l, path, new = {}, -1, -1, 0, None, 0
    for row in diff.splitlines():
        if row.startswith("diff --git"):
            f, c, path = f + 1, -1, None
        elif row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
        elif row.startswith("@@"):
            c, l = c + 1, 0
            new = int(re.match(r"@@ -\S+ \+(\d+)", row)[1])
        elif c >= 0 and row[:1] in (" ", "+", "-"):
            if row[0] != "-":
                ids[(path, new)] = f"file-{f}-chunk-{c}-line-{l}"
                new += 1
            l += 1
    return ids


def functions(rev, path):
    """{name: FunctionDef} of the top-level functions of path in rev ({} if gone)."""
    text = git("show", f"{rev}:{path}", check=False)
    if not text:
        return {}
    tree = ast.parse(text)
    return {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def called(node, helpers, seen=None):
    """The names a function calls, also through the helpers of its own file."""
    seen = seen if seen is not None else set()
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
            if name:
                names.add(name)
                if name in helpers and name not in seen:
                    seen.add(name)
                    names |= called(helpers[name], helpers, seen)
    return names


def link(name, line_id):
    return f"[`{name}`](#{line_id})"


def test_links(diff, files, rev, edit_url=None):
    """The link comments of one step, as difit --comment imports. With edit_url (the
    review page's /api/edit), each comment ends with a link that opens its line in
    the editor."""
    ids = line_ids(diff)
    tests_files = sorted(p for p in files if p.startswith("tests/") and p.endswith(".py"))
    source_files = sorted(p for p in files if not p.startswith("tests/") and p.endswith(".py"))

    # functions of the source files whose def line the diff shows
    under_test = {}  # name: (path, line)
    for path in source_files:
        for name, node in functions(rev, path).items():
            if (path, node.lineno) in ids:
                under_test[name] = (path, node.lineno)

    tests_of = {}  # name under test: [(test name, path, line)]
    comments = []
    for path in tests_files:
        defs = functions(rev, path)
        helpers = {k: v for k, v in defs.items() if not k.startswith("test")}
        for name, node in defs.items():
            if not name.startswith("test") or (path, node.lineno) not in ids:
                continue
            targets = sorted(called(node, helpers) & set(under_test))
            if not targets:
                continue
            for t in targets:
                tests_of.setdefault(t, []).append((name, path, node.lineno))
            body = "🔗 Tests: " + ", ".join(link(t, ids[under_test[t]]) for t in targets)
            comments.append((path, node.lineno, body))

    for name, tests in tests_of.items():
        path, line = under_test[name]
        body = "🔗 Tested by: " + ", ".join(link(t, ids[(p, n)]) for t, p, n in tests)
        comments.append((path, line, body))

    def editor(path, line):
        if not edit_url:
            return ""
        return f" [✎]({edit_url}?{urlencode({'file': path, 'line': line})})"

    return [
        {"type": "thread", "id": f"{PREFIX}{i}", "filePath": path,
         "position": {"side": "new", "line": line}, "body": body + editor(path, line)}
        for i, (path, line, body) in enumerate(comments, 1)
    ]
