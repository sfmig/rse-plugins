"""The comments of one review pass: pr-review/comments/pass-N/comments.json.

The file has three lists of threads: "threads" (open), "resolved" and "deleted".
A thread is difit's thread (id, messages, createdAt, updatedAt) plus where it sits:

    "commit": {"sha", "filePath", "position"}   the atomic commit it was written on, or null
    "tip":    {"filePath", "position"}          its line at the tip of the PR branch, or null

As on GitHub, comments only move forward:
  * A thread written on a commit gets its tip line from git blame on every run. If a
    later commit changed the line, it has no tip line: it is "outdated".
  * A thread written on the whole PR (or a session) has a tip line and no commit.
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone

LISTS = ("threads", "resolved", "deleted")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def lines_of(position):
    """The first and last line of a position (a single line, or a range)."""
    line = position["line"]
    return [line] if isinstance(line, int) else [line["start"], line["end"]]


def with_lines(position, lines):
    line = lines[0] if len(lines) == 1 else {"start": lines[0], "end": lines[1]}
    return {"side": position["side"], "line": line}


class TipLines:
    """Find where a line of an atomic commit is at the tip, with git blame.

    git blame base..rev says, for each line of a file in rev, which commit last
    changed it and its line number there; lines older than the PR get the base
    commit. That (commit, line) pair names the line in every revision, so a line
    is at the tip if the tip's blame has the same pair.
    """

    def __init__(self, base, atomic):
        self.base, self.atomic = base, atomic
        self.cache = {}

    def blame(self, rev, path):
        """[(commit, line there), ...] for each line of path in rev."""
        if (rev, path) not in self.cache:
            out, head = [], None
            for row in git("blame", "--line-porcelain", f"{self.base}..{rev}", "--", path).splitlines():
                if row.startswith("\t"):
                    out.append((head[0], int(head[1])))
                elif re.match(r"[0-9a-f]{40} \d+ \d+", row):   # "<commit> <line there> <line here>"
                    head = row.split()
            self.cache[(rev, path)] = out
        return self.cache[(rev, path)]

    def origin(self, rev, path, line):
        if rev == self.base:
            return (self.base, line)
        rows = self.blame(rev, path)
        return rows[line - 1] if 0 < line <= len(rows) else None

    def tip_of(self, commit):
        """The tip place of a thread written on a commit, or None if its line changed later."""
        side = commit["position"]["side"]
        rev = commit["sha"] if side == "new" else f"{commit['sha']}^"
        path = commit["filePath"]
        origins = [self.origin(git("rev-parse", rev).strip(), path, n) for n in lines_of(commit["position"])]
        if None in origins:
            return None
        at_tip = {o: n for n, o in enumerate(self.blame(self.atomic, path), 1)}
        if all(o in at_tip for o in origins):
            return {"filePath": path, "position": with_lines({"side": "new"}, [at_tip[o] for o in origins])}
        # a line from before the PR that the PR deleted: on the old side of the whole-PR diff
        if all(o[0] == self.base for o in origins) and not any(o in at_tip for o in origins):
            return {"filePath": path, "position": with_lines({"side": "old"}, [o[1] for o in origins])}
        return None

    def commit_of(self, tip):
        """The commit that added a tip line, and the line there (for the preloaded questions)."""
        if tip["position"]["side"] != "new":
            return None
        origins = [self.origin(self.atomic, tip["filePath"], n) for n in lines_of(tip["position"])]
        if None in origins or len({o[0] for o in origins}) != 1 or origins[0][0] == self.base:
            return None
        return {"sha": origins[0][0], "filePath": tip["filePath"],
                "position": with_lines(tip["position"], [o[1] for o in origins])}


class Pass:
    """One pass's comments.json. tip_lines is None if the atomic branch is missing or
    out of date: then threads written on a commit get no tip line this run."""

    def __init__(self, path, tip_lines):
        self.path, self.tip_lines = path, tip_lines
        data = json.loads(path.read_text()) if path.exists() else {}
        self.data = {k: data.get(k, []) for k in LISTS}
        for t in self.data["threads"]:
            self.place(t)

    def place(self, t):
        if t.get("commit"):
            t["tip"] = self.tip_lines.tip_of(t["commit"]) if self.tip_lines else None

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2))
        os.replace(tmp, self.path)    # a Ctrl+C mid-write can't leave a half-written file

    def first_bodies(self, lists):
        return {t["messages"][0]["body"] for k in lists for t in self.data[k] if t["messages"]}

    def add_questions(self, questions, earlier):
        """Add the preloaded questions as open threads: on the commit that added their
        line when possible, else on the tip. Skip those already in this pass, or
        resolved or deleted in an earlier pass."""
        skip = self.first_bodies(LISTS)
        for other in earlier:
            skip |= other.first_bodies(("resolved", "deleted"))
        for i, q in enumerate(questions, 1):
            if q["body"] in skip:
                continue
            tip = {"filePath": q["filePath"], "position": q["position"]}
            t = {"id": f"question-{i}", "createdAt": now(), "updatedAt": now(),
                 "commit": self.tip_lines.commit_of(tip) if self.tip_lines else None, "tip": tip,
                 "messages": [{"id": f"question-{i}", "body": q["body"], "createdAt": now(), "updatedAt": now()}]}
            self.place(t)
            self.data["threads"].append(t)
        self.save()

    def shown_on(self, sha=None, files=None):
        """The open threads one item shows, each with its place there: on a commit (sha),
        or at the tip on some files (files=None: all files)."""
        out = []
        for t in self.data["threads"]:
            place = t.get("commit") if sha else t.get("tip")
            if place and (place.get("sha") == sha if sha else files is None or place["filePath"] in files):
                out.append((t, place))
        return out

    def not_shown(self, atomic_mode):
        """Open threads that no item of the mode shows inline: in atomic mode those
        written on the whole PR; in the other modes the outdated ones."""
        return [t for t in self.data["threads"] if not t.get("commit" if atomic_mode else "tip")]

    def apply(self, sha, item, before, after):
        """Save what changed in one difit since the last look.
        before: {id: messages} when last looked; after: difit's threads now.
        A thread gone from difit was resolved; a reply "delete" deletes a thread."""
        changed = False
        for d in after:
            if before.get(d["id"]) == content(d["messages"]):
                continue
            changed = True
            t = self.pop(d["id"])
            if t is None:     # new: written on this item
                place = {"filePath": d["filePath"], "position": d["position"]}
                t = {"id": d["id"], "createdAt": d.get("createdAt", now()),
                     "commit": {"sha": sha, **place} if sha else None, "tip": None if sha else place}
                self.place(t)
            t.update(messages=d["messages"], updatedAt=d.get("updatedAt", now()), item=item)
            if any(m["body"].strip().lower() == "delete" for m in d["messages"]):
                self.data["deleted"].append({**t, "deletedAt": now()})
            else:
                self.data["threads"].append(t)
        gone = set(before) - {d["id"] for d in after}
        for t in [t for t in self.data["threads"] if t["id"] in gone]:
            changed = True
            self.data["threads"].remove(t)
            self.data["resolved"].append({**t, "resolvedAt": now()})
        if changed:
            self.save()

    def pop(self, thread_id):
        for k in LISTS:
            for t in self.data[k]:
                if t["id"] == thread_id:
                    self.data[k].remove(t)
                    t.pop("resolvedAt", None)
                    t.pop("deletedAt", None)
                    return t
        return None


def content(messages):
    """What the reviewer can change in a thread (difit may add other fields)."""
    return [(m.get("id"), m["body"]) for m in messages]


def difit_comments(thread, place):
    """A thread as difit --comment imports: the thread, then its replies."""
    out = []
    for i, m in enumerate(thread["messages"]):
        out.append({k: v for k, v in {
            "type": "reply" if i else "thread", "id": thread["id"] if i == 0 else m.get("id"),
            "filePath": place["filePath"], "position": place["position"], "body": m["body"],
            "author": m.get("author"), "createdAt": m.get("createdAt"), "updatedAt": m.get("updatedAt"),
        }.items() if v})
    return out
