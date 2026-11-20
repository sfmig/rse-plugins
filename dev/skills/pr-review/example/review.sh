#!/usr/bin/env bash
# Review the PR in difit, one item per browser tab.
#
#   ./review.sh atomic [N]     atomic branch, one commit per tab, from commit N
#   ./review.sh sessions [N]   session plan in 2-review/2-difit.md, from session N
#   ./review.sh tests [N]      test plan in 3-tests/1-tests.md, from row N
#
# Close the tab to open the next item. Ctrl+C stops.
# Comments are saved to comments/<item>.json every 2 s while a tab is open.
# Questions in 2-review/questions.json are preloaded where their line is in the item.
set -euo pipefail

BRANCH=smg/add-ellipse-params-to-tracks
ATOMIC=$BRANCH-atomic
BASE=d005d99
DIFIT=${DIFIT:-npx -y difit@5.0.12}
DIFIT_EXTRA=${DIFIT_EXTRA:-}   # e.g. "--no-open --keep-alive" for testing

HERE=$(cd "$(dirname "$0")" && pwd)
NOTES=$HERE/comments
QUESTIONS=$HERE/2-review/questions.json
mkdir -p "$NOTES"
cd "$(git -C "$HERE" rev-parse --show-toplevel)"

# Questions whose line was added by commit $1 (git blame on the atomic branch)
questions_for_commit() {
  python3 - "$QUESTIONS" "$ATOMIC" "$1" <<'EOF'
import json, subprocess, sys
qs, branch, sha = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
def added_by(q):
    line = q["position"]["line"]
    out = subprocess.run(["git", "blame", "--porcelain", "-L", f"{line},{line}",
                          branch, "--", q["filePath"]], capture_output=True, text=True).stdout
    return out.startswith(sha)
print(json.dumps([q for q in qs if added_by(q)]))
EOF
}

# Questions on files $2..; plus comments saved earlier in notes file $1
questions_for_files() {
  python3 - "$QUESTIONS" "$@" <<'EOF'
import json, os, sys
qs, saved, files = json.load(open(sys.argv[1])), sys.argv[2], set(sys.argv[3:])
out = [q for q in qs if q["filePath"] in files]
if os.path.exists(saved):
    for t in json.load(open(saved))["threads"]:
        for i, m in enumerate(t["messages"]):
            out.append({"type": "reply" if i else "thread", "filePath": t["filePath"],
                        "position": t["position"], "body": m["body"]})
print(json.dumps(out))
EOF
}

# Rows of a markdown table that end in a checkbox; prints the backticked paths of each row
table_rows() {
  grep -E '^\|.*\| *\[[ x]\] *\|$' "$1" | while read -r row; do
    grep -o '`[^`]*`' <<<"$row" | tr -d '`' | while read -r p; do
      git cat-file -e "$BASE:$p" 2>/dev/null || git cat-file -e "$BRANCH:$p" 2>/dev/null && printf '%s ' "$p"
    done
    echo
  done
}

# Run difit for one item; save its comments while it runs.
#   run_one <name> <comments-json> <stdin-file> <difit args...>
run_one() {
  local name=$1 comments=$2 input=$3; shift 3
  local log=$NOTES/$name.log json=$NOTES/$name.json args=("$@")
  [ "$comments" != "[]" ] && args+=(--comment "$comments")
  echo ">> $name   (close the tab for the next item)"
  # shellcheck disable=SC2086
  $DIFIT "${args[@]}" $DIFIT_EXTRA <"$input" >"$log" 2>&1 &
  local pid=$! port="" first=""
  trap 'kill $pid 2>/dev/null; exit 130' INT TERM
  while [ -z "$port" ] && kill -0 $pid 2>/dev/null; do
    port=$(grep -o 'localhost:[0-9]*' "$log" | head -1 | cut -d: -f2 || true)
    sleep 0.5
  done
  while kill -0 $pid 2>/dev/null; do
    local now
    now=$(curl -sf "http://localhost:$port/api/comments-json" || true)
    if [ -n "$now" ]; then
      # overwrite saved notes only after a change, so a slow browser start loses nothing
      [ -z "$first" ] && first=$now
      if [ "$now" != "$first" ] || [ ! -e "$json" ]; then printf '%s\n' "$now" >"$json"; fi
    fi
    sleep 2
  done
  trap - INT TERM
}

mode=${1:-}
start=${2:-1}
case $mode in
  atomic)
    i=0
    for sha in $(git rev-list --reverse --abbrev-commit "$BASE..$ATOMIC"); do
      i=$((i + 1)); [ $i -lt "$start" ] && continue
      run_one "atomic-$(printf %02d $i)-$sha" "$(questions_for_commit "$sha")" /dev/null "$sha"
    done ;;
  sessions | tests)
    table=$HERE/2-review/2-difit.md; [ "$mode" = tests ] && table=$HERE/3-tests/1-tests.md
    i=0
    while read -r -a files; do
      i=$((i + 1)); [ $i -lt "$start" ] && continue
      name=$mode-$(printf %02d $i)
      diff=$NOTES/$name.diff
      git diff -M "$BASE" "$BRANCH" -- "${files[@]}" >"$diff"
      # stdin diffs share one browser key, so start clean and reload saved notes
      run_one "$name" "$(questions_for_files "$NOTES/$name.json" "${files[@]}")" "$diff" - --clean
    done < <(table_rows "$table") ;;
  *)
    sed -n '2,10p' "$HERE/$(basename "$0")"; exit 1 ;;
esac
echo "Done. Notes: $NOTES"
