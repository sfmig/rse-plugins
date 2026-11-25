#!/usr/bin/env python3
"""Review a PR in difit, with the files of a PR review package (the pr-review/ folder).

  review.py atomic [N|SHA] [--pass N]   one atomic commit at a time, from commit N (or SHA)
  review.py sessions [N]   [--pass N]   the session plan in 2-review/2-difit.md, from session N
  review.py all            [--pass N]   the whole PR, like GitHub's "Files changed"

A review page opens in the browser: the items on the left, the chosen one in difit.
Each run starts a new pass, saved in comments/pass-N/comments.json; --pass N adds to
pass N instead. Stop with the page's Stop button or Ctrl+C.

Needs difit: npm i -g difit@5.0.12
"""

import argparse
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from atomic import Branches, git, git_ok
from comments import Pass, TipLines, content, difit_comments

PACKAGE = Path(__file__).resolve().parent.parent  # pr-review/
COMMENTS = PACKAGE / "comments"
QUESTIONS = PACKAGE / "2-review" / "questions.json"
SESSIONS = PACKAGE / "2-review" / "2-difit.md"  # the session plan table
COMMIT_LIST = (
    PACKAGE / "2-review" / "1-atomic-branch.md"
)  # the atomic commits table, with weights
PAGE = Path(__file__).resolve().parent / "page.html"


# ------------------------------------------------------------------ items
@dataclass
class Item:
    """One thing to review: an atomic commit, a session, or the whole PR."""

    name: str  # e.g. atomic-05-501a731, sessions-02, all
    title: str
    args: list  # what difit shows: a commit, two revisions, or "-" (a diff on stdin)
    sha: str = None  # atomic commit
    files: set = None  # the files of a session (None: all files)
    detail: str = ""  # the rest of the commit message
    weight: str = None  # high, med or low (atomic commits)
    diff: str = field(
        default=None, repr=False
    )  # the diff of a session, sent on stdin


def weights():
    """{short hash: weight} from the commits table of the package."""
    rows = COMMIT_LIST.read_text().splitlines() if COMMIT_LIST.exists() else []
    found = (
        re.match(
            r"^\|\s*\d+\s*\|\s*`([0-9a-f]{7,40})`.*\|\s*\S*\s*(high|med|low)\s*\|\s*$",
            r,
        )
        for r in rows
    )
    return {m.group(1): m.group(2) for m in found if m}


def atomic_items(b):
    w = weights()
    items = []
    for n, sha in enumerate(
        git("rev-list", "--reverse", f"{b.base}..{b.atomic}").split(), 1
    ):
        message = [
            x
            for x in git("log", "-1", "--format=%B", sha).splitlines()
            if not x.startswith("Co-Authored-By:")
        ]
        weight = next((v for k, v in w.items() if sha.startswith(k)), None)
        items.append(
            Item(
                f"atomic-{n:02d}-{sha[:7]}",
                message[0],
                [sha],
                sha=sha,
                detail="\n".join(message[1:]).strip(),
                weight=weight,
            )
        )
    return items


def session_items(b):
    """One item per row of the session table (rows that end in a checkbox)."""
    rows = [
        r
        for r in SESSIONS.read_text().splitlines()
        if re.match(r"^\|.*\| *\[[ x]\] *\|$", r)
    ]
    items = []
    for n, row in enumerate(rows, 1):
        files = [
            p
            for p in re.findall(r"`([^`]*)`", row)
            if git_ok("cat-file", "-e", f"{b.base}:{p}")
            or git_ok("cat-file", "-e", f"{b.branch}:{p}")
        ]
        items.append(
            Item(
                f"sessions-{n:02d}",
                f"Session {n}",
                ["-"],
                files=set(files),
                detail="\n".join(files),
                diff=git("diff", "-M", b.base, b.branch, "--", *files) + "\n",
            )
        )
    return items


# ------------------------------------------------------------------ difit
def free_port():
    with socket.socket() as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


class Difit:
    """A difit server for one item. It starts empty (--clean), then gets the item's saved
    threads, so comments.json is the only record of the comments."""

    def __init__(self, item, comments):
        shown = comments.shown_on(item.sha, item.files)
        self.before = {
            t["id"]: content(t["messages"]) for t, _ in shown
        }  # to see what changes
        imports = [c for t, place in shown for c in difit_comments(t, place)]
        self.url = f"http://localhost:{free_port()}"
        args = [
            "difit",
            *item.args,
            "--port",
            self.url.rsplit(":", 1)[1],
            "--no-open",
            "--keep-alive",
            "--clean",
        ]
        if imports:
            args += ["--comment", json.dumps(imports)]
        self.errors = tempfile.TemporaryFile("w+")
        self.proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE if item.diff else subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=self.errors,
            text=True,
            start_new_session=True,
        )
        if item.diff:
            self.proc.stdin.write(item.diff)
            self.proc.stdin.close()
        while self.threads() is None:  # wait until it answers (about 0.5 s)
            if self.proc.poll() is not None:
                self.errors.seek(0)
                raise RuntimeError(
                    f"difit did not start for {item.name}:\n{self.errors.read()}"
                )
            time.sleep(0.05)

    def threads(self):
        """difit's threads now, or None if it does not answer."""
        try:
            with urlopen(self.url + "/api/comments-json", timeout=2) as r:
                return json.load(r)["threads"]
        except OSError:
            return None

    def stop(self):
        self.proc.terminate()    # no-op if difit already quit
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


# ------------------------------------------------------------------ the review page
class Review:
    """The items, the pass, and the one difit server showing the chosen item."""

    def __init__(self, mode, items, comments, pass_no, start):
        self.mode, self.items, self.comments, self.pass_no, self.start = (
            mode,
            items,
            comments,
            pass_no,
            start,
        )
        self.shown = None  # (item, Difit) on screen
        self.lock = threading.Lock()

    def open(self, i):
        with self.lock:
            if self.shown and self.shown[0] is self.items[i]:
                return self.shown[1].url
            self.close()
            self.shown = (self.items[i], Difit(self.items[i], self.comments))
            return self.shown[1].url

    def save(self):
        """Save what changed in the difit on screen."""
        if not self.shown:
            return
        item, difit = self.shown
        now = difit.threads()
        if now is not None:
            self.comments.apply(item.sha, item.name, difit.before, now)
            difit.before = {d["id"]: content(d["messages"]) for d in now}

    def close(self):
        if self.shown:
            self.save()
            self.shown[1].stop()
            self.shown = None

    def state(self):
        atomic = self.mode == "atomic"
        others = []
        for t in self.comments.not_shown(atomic):
            place = t.get("commit") or t.get("tip")
            line = place["position"]["line"]
            others.append(
                {
                    "file": place["filePath"],
                    "line": line
                    if isinstance(line, int)
                    else f"{line['start']}-{line['end']}",
                    "sha": (t.get("commit") or {}).get("sha"),
                    "body": t["messages"][0]["body"],
                    "replies": len(t["messages"]) - 1,
                }
            )
        return {
            "mode": self.mode,
            "pass": self.pass_no,
            "start": self.start,
            "others": others,
            "othersTitle": "Only on the whole PR"
            if atomic
            else "Outdated: on an earlier commit",
            "items": [
                {
                    "name": it.name,
                    "title": it.title,
                    "detail": it.detail,
                    "weight": it.weight,
                    "sha": it.sha,
                    "threads": len(self.comments.shown_on(it.sha, it.files)),
                }
                for it in self.items
            ],
        }


def serve(review, stopped):
    """The page's server: GET / (the page), GET /api/state, POST /api/open/N, POST /api/stop."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, body, kind="application/json", code=200):
            data = (
                body.encode()
                if isinstance(body, str)
                else json.dumps(body).encode()
            )
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/":
                self.reply(PAGE.read_text(), "text/html; charset=utf-8")
            elif self.path == "/api/state":
                with review.lock:
                    self.reply(review.state())
            else:
                self.reply({"error": "not found"}, code=404)

        def do_POST(self):
            m = re.fullmatch(r"/api/open/(\d+)", self.path)
            if m:
                try:
                    self.reply({"url": review.open(int(m.group(1)))})
                except RuntimeError as e:
                    self.reply({"error": str(e)}, code=500)
            elif self.path == "/api/stop":
                self.reply({"ok": True})
                stopped.set()
            else:
                self.reply({"error": "not found"}, code=404)

    httpd = ThreadingHTTPServer(("localhost", free_port()), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# ------------------------------------------------------------------ main
def passes():
    """{number: comments.json} of the passes so far."""
    return {
        int(d.name[5:]): d / "comments.json"
        for d in COMMENTS.glob("pass-*")
        if d.name[5:].isdigit()
    }


def start_index(start, items):
    """Item number N (from 1), or an atomic commit's hash, as an index."""
    if not start:
        return 0
    if start.isdigit() and len(start) < 7:
        i = int(start) - 1
    else:
        full = git(
            "rev-parse",
            "--verify",
            "--quiet",
            f"{start}^{{commit}}",
            check=False,
        )
        i = next((n for n, it in enumerate(items) if it.sha == full), -1)
    if not 0 <= i < len(items):
        sys.exit(f"No item {start}: there are {len(items)}.")
    return i


def main():
    p = argparse.ArgumentParser(usage=__doc__, add_help=False)
    p.add_argument("mode", choices=["atomic", "sessions", "all"])
    p.add_argument("start", nargs="?")
    p.add_argument("--pass", dest="pass_no", type=int)
    args = p.parse_args()
    sys.stdout.reconfigure(
        line_buffering=True
    )  # print each line at once, also into a log
    os.chdir(git("rev-parse", "--show-toplevel"))
    b = Branches.from_git()
    if not shutil.which("difit"):
        sys.exit("difit is not installed: npm i -g difit@5.0.12")

    # Commit lines can only be followed to the tip if the atomic branch has the PR's files
    tip_lines = None
    if b.has_atomic() and b.atomic_up_to_date():
        tip_lines = TipLines(b.base, git("rev-parse", b.atomic))
    elif b.has_atomic():
        print(
            f"Note: {b.atomic} is behind {b.branch}, so comments written on a commit are not shown at the tip.\n"
            "      To update it: pr-review/scripts/atomic.py extend"
        )
    elif args.mode == "atomic":
        sys.exit(
            f"No branch {b.atomic}: ask the agent to build the atomic branch first."
        )

    found = passes()
    if args.pass_no is not None and args.pass_no not in found:
        sys.exit(f"No pass {args.pass_no}. Passes: {sorted(found) or 'none'}")
    pass_no = (
        args.pass_no if args.pass_no is not None else max(found, default=0) + 1
    )
    comments = Pass(COMMENTS / f"pass-{pass_no}" / "comments.json", tip_lines)
    if QUESTIONS.exists():
        earlier = [
            Pass(path, None)
            for n, path in found.items()
            if n != pass_no and path.exists()
        ]
        comments.add_questions(json.loads(QUESTIONS.read_text()), earlier)

    items = {
        "atomic": atomic_items,
        "sessions": session_items,
        "all": lambda b: [Item("all", "Whole PR", [b.branch, b.base])],
    }[args.mode](b)
    review = Review(
        args.mode, items, comments, pass_no, start_index(args.start, items)
    )

    stopped = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    httpd = serve(review, stopped)
    url = f"http://localhost:{httpd.server_address[1]}/"
    print(
        f"Pass {pass_no}: {comments.path.relative_to(PACKAGE.parent)}\nReview page: {url}\n"
        "Stop with the page's Stop button or Ctrl+C."
    )
    if not os.environ.get("REVIEW_NO_BROWSER"):
        webbrowser.open(url)
    while not stopped.wait(1):  # save the comments every second
        with review.lock:
            review.save()
    with review.lock:
        review.close()
    httpd.shutdown()
    print("Stopped. Comments saved.")


if __name__ == "__main__":
    main()
