#!/usr/bin/env bash
# Check that every ```mermaid block in one or more Markdown files renders.
#
# Usage: check-mermaid.sh FILE.md [FILE.md ...]
#
# Prints one line per diagram ("ok" or "FAIL" with file:line of the opening
# fence), followed by the renderer's error for each failure.
# Exit status: 0 all diagrams render, 1 at least one fails, 2 usage or
# setup error (no renderer, or its headless browser will not start).
#
# Renderer, in order of preference:
#   $MMDC                       e.g. MMDC="mmdc -p puppeteer.json"
#   mmdc on PATH                npm install -g @mermaid-js/mermaid-cli
#   npx (Node.js)               downloads @mermaid-js/mermaid-cli on first run
# Set MERMAID_CLI_VERSION to change the version npx uses.

set -euo pipefail

MERMAID_CLI_VERSION="${MERMAID_CLI_VERSION:-12.0.0}"

if [[ $# -eq 0 ]]; then
    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi

if [[ -n "${MMDC:-}" ]]; then
    read -r -a mmdc <<< "$MMDC"
elif command -v mmdc > /dev/null; then
    mmdc=(mmdc)
elif command -v npx > /dev/null; then
    mmdc=(npx --yes "@mermaid-js/mermaid-cli@${MERMAID_CLI_VERSION}")
else
    echo "error: needs mmdc or npx (Node.js) to render diagrams" >&2
    exit 2
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/check-mermaid.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

status=0
total=0
file_index=0

for md in "$@"; do
    if [[ ! -f "$md" ]]; then
        echo "error: no such file: $md" >&2
        exit 2
    fi
    file_index=$((file_index + 1))

    # Write each mermaid block to $tmp/<file>-<n>.mmd, with the fence's
    # indentation removed, and print "<n> <line of opening fence>".
    blocks="$(awk -v dir="$tmp" -v f="$file_index" '
        !inside && /^[ \t]*```+[ \t]*mermaid[ \t]*$/ {
            inside = 1; n++
            match($0, /^[ \t]*/); indent = RLENGTH
            out = dir "/" f "-" n ".mmd"
            print n, NR
            next
        }
        inside && /^[ \t]*```+[ \t]*$/ { inside = 0; close(out); next }
        inside { print substr($0, indent + 1) > out }
    ' "$md")"

    while read -r n line; do
        [[ -z "$n" ]] && continue
        total=$((total + 1))
        src="$tmp/$file_index-$n.mmd"
        if err="$("${mmdc[@]}" --quiet -i "$src" -o "${src%.mmd}.svg" 2>&1)"; then
            echo "ok    $md:$line"
        elif grep -q -E 'Could not find (chrome|Chrome)|Failed to launch the browser' <<< "$err"; then
            # The renderer is broken, not the diagram: stop rather than
            # reporting every diagram as failed.
            echo "error: mermaid-cli could not start its headless browser:" >&2
            grep -v -E '^[[:space:]]*$' <<< "$err" | head -3 | sed 's/^/    /' >&2
            echo "hint: npx puppeteer browsers install chrome-headless-shell" >&2
            exit 2
        else
            status=1
            echo "FAIL  $md:$line"
            # Drop blank lines and JavaScript stack frames; keep the parse error.
            grep -v -E '^[[:space:]]*$|^[[:space:]]+at |\(.*:[0-9]+:[0-9]+\)$' <<< "$err" \
                | sed 's/^/      /'
        fi
    done <<< "$blocks"
done

if [[ $total -eq 0 ]]; then
    echo "no mermaid diagrams found"
fi

exit "$status"
