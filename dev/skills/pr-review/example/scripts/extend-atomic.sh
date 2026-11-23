#!/usr/bin/env bash
# Add the commits made on the PR branch after the one whose files match the atomic tip
# to the end of the atomic branch, with the same message, author and date.
#
#   ./extend-atomic.sh
#
# Doesn't touch the working tree. Stops if no commit on the PR branch matches the atomic tip
# (the PR branch was rebased or amended): then ask the agent to rebuild it.
set -euo pipefail

SCRIPTS=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$SCRIPTS" rev-parse --show-toplevel)"
# shellcheck source=config.sh
source "$SCRIPTS/config.sh"
require_atomic

match=$(last_commit_matching_atomic)
[ -n "$match" ] || { echo "No commit on $BRANCH has the same files as $ATOMIC (rebased?). Ask the agent to rebuild it."; exit 1; }
new=$(git rev-list --reverse "$match..$BRANCH")
[ -n "$new" ] || { echo "$ATOMIC is up to date with $BRANCH."; exit 0; }

old=$(git rev-parse "$ATOMIC") tip=$old
for c in $new; do
  # the atomic tip has the same files as c's parent, so c's tree is the replayed result
  tip=$(GIT_AUTHOR_NAME=$(git log -1 --format=%an "$c") GIT_AUTHOR_EMAIL=$(git log -1 --format=%ae "$c") \
        GIT_AUTHOR_DATE=$(git log -1 --format=%aI "$c") \
        git commit-tree "$c^{tree}" -p "$tip" -m "$(git log -1 --format=%B "$c")")
done
git update-ref "refs/heads/$ATOMIC" "$tip" "$old"

# number the new commits as review.sh atomic does
first=$(( $(git rev-list --count "$BASE..$old") + 1 ))
echo "Added to $ATOMIC (was $(git rev-parse --short "$old"); undo: git branch -f $ATOMIC $(git rev-parse --short "$old")):"
git log --reverse --format='%h %s' "$old..$ATOMIC" | awk -v f="$first" '{ printf "  %2d  %s\n", f + NR - 1, $0 }'
