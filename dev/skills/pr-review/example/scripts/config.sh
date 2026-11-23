# Shared by review.sh and extend-atomic.sh: the PR's branches, and how to find
# the commit on the PR branch whose files match the atomic tip. Source it from the repo root.
#
# Each name is worked out from git; set it in the environment to override, e.g.
#   BRANCH=other-pr pr-review/scripts/review.sh all
# shellcheck shell=bash

# ------- Constants --------------
# The PR branch: the checked-out one 
BRANCH=${BRANCH:-$(git branch --show-current)}

# If the atomic copy is checked out, point to the PR branch it copies.
# (Only if that branch exists, so a PR branch that really ends in -atomic is kept)
if [[ $BRANCH == *-atomic ]] && git rev-parse --verify --quiet "refs/heads/${BRANCH%-atomic}" >/dev/null; then
  BRANCH=${BRANCH%-atomic}
fi
MAIN=${MAIN:-main}
[ -n "$BRANCH" ] || { echo "No branch checked out: check out the PR branch, or set BRANCH=<branch>"; exit 1; }
[ "$BRANCH" != "$MAIN" ] || { echo "On $MAIN: check out the PR branch, or set BRANCH=<branch>"; exit 1; }

# The atomic copy of the PR, built by the agent (see 2-review/1-atomic-branch.md)
ATOMIC=${ATOMIC:-$BRANCH-atomic}

# Where the PR branch split off from main
BASE=${BASE:-$(git merge-base "$MAIN" "$BRANCH")}

# ------- Helper functions ------------------
# Stop with a clear message if the PR has no atomic branch yet
require_atomic() {
  git rev-parse --verify --quiet "refs/heads/$ATOMIC" >/dev/null ||
    { echo "No branch $ATOMIC: ask the agent to build the atomic branch first."; exit 1; }
}

# The atomic branch was built so its last commit has exactly the same files as one
# commit on $BRANCH. Print that commit (the newest, if several), or nothing if none.
# awk reads to the end on purpose: exiting early breaks git log under pipefail.
last_commit_matching_atomic() {
  git log --format='%H %T' "$BASE..$BRANCH" |
    awk -v t="$(git rev-parse "$ATOMIC^{tree}")" '$2 == t && !found { print $1; found = 1 }'
}
