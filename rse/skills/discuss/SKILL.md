---
name: discuss
description: Discuss a saved proposal with the user in a fresh conversation - answer questions about it, weigh alternatives it does not cover, and suggest clarifications to the proposal, made only when the user agrees, under the same writing rules as the first draft.
when_to_use: Use when the user wants to read, question, review or refine a proposal in claude-plans/, typically in a new conversation after /with-diagrams:proposal wrote it.
argument-hint: "[path to proposal]"
allowed-tools:
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/proposal/scripts/check-mermaid.sh *)
  - Bash(git branch --show-current)
  - Bash(git status *)
# Edit guard, kept identical in the proposal skill. Skill hooks stay registered
# for the rest of the session: only claude-plans/ is editable, except by the
# with-diagrams:implementer agent, which works in its own worktree.
# Only Edit/Write/MultiEdit/NotebookEdit are guarded, not Bash.
hooks:
  PreToolUse:
    - matcher: "Edit|Write|MultiEdit|NotebookEdit"
      hooks:
        - type: command
          command: |
            i=$(cat)
            case "$(printf '%s' "$i" | jq -r '.agent_type // empty')" in with-diagrams:implementer|implementer) exit 0 ;; esac
            p=$(printf '%s' "$i" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
            d="${CLAUDE_PROJECT_DIR:-$PWD}"
            case "$p" in ""|"$d"/claude-plans/*) exit 0 ;; "$d"/*) ;; *) exit 0 ;; esac
            echo "Blocked by with-diagrams: in a proposal session only files in claude-plans/ can be edited. Code is changed only by the with-diagrams:implementer agent, which the user starts by asking to implement the proposal (see the with-diagrams:discuss skill). Do not work around this block; tell the user." >&2
            exit 2
---

# Discuss a proposal

The proposal to discuss: $ARGUMENTS

If that is empty, list `claude-plans/proposal-*.md`. Use the only one if there is one; otherwise ask the user which.

You are the user's partner in reviewing one proposal. Your context is the proposal and the code, nothing else.

- **That is the point of a fresh conversation.** A question you cannot answer from the proposal alone marks a possible gap in the proposal. Offer to fill it, as *Suggest clarifications* below describes.

## Before the first reply

1. Read the proposal.
2. Read the writing rules: `${CLAUDE_PLUGIN_ROOT}/skills/writing-style/SKILL.md`.
3. Read the *Sections*, *Writing rules* and *During the discussion* parts of `${CLAUDE_PLUGIN_ROOT}/skills/proposal/SKILL.md`.

Then tell the user in one line that you have read the proposal and are ready.

## How to respond

- **The user often selects a passage in the editor** before asking. Treat the selection as the part of the proposal the question is about.

- **Questions about the proposal.** Answer with the conclusion first, then the reason, with `path:line` anchors. Check the code rather than relying on what the proposal says.

- **Alternatives the proposal does not include.** Weigh them against the codebase and the proposal's goal. Give a recommendation, not a survey.

- **Suggest clarifications; do not make them unasked.** Answering a question never edits the proposal by itself. When the answer shows that part of the proposal is unclear, or the user reaches a conclusion, end the reply with a suggestion and wait:
    - name the section it would go in;
    - give the exact text to add or replace, in a quote or code block;
    - ask whether to add it.

    Make the edit only when the user agrees, with their changes to the wording. If they decline, leave the proposal as it is. If the answer shows nothing unclear, suggest nothing.

- **Edits the user asks for directly** are made without the suggestion step.

- **Every edit** follows the writing rules and *During the discussion*:
    - fold the answer into the right section;
    - record a decided point in the *Conclusion* column of *Points to discuss*;
    - put a rejected alternative in that step's *Alternatives rejected* table;
    - never mention earlier drafts.

- **Edits the user made themselves.** Re-read the file before each edit, because the user may have changed it. Keep their wording unless it breaks a writing rule or contradicts the code; if so, say which and suggest a fix.

- **After editing a diagram**, run `${CLAUDE_PLUGIN_ROOT}/skills/proposal/scripts/check-mermaid.sh <proposal>` and fix every `FAIL`.

- **If the proposal was published as an Artifact**, republish it after every edit, as *Publishing for comment* in the proposal skill describes.

## Implementing it

Only when the user explicitly asks. The `with-diagrams:implementer` agent does the work in its own git worktree, so the user's checkout is free while it runs.

1. **Check the branch.** Run `git branch --show-current`.
    - If it is the default branch, stop. Ask the user to create a feature branch for the proposal, or offer to create one with a name you suggest.

2. **Commit the proposal** on that branch. Only committed work reaches the agent's worktree.
    - Show the user the file and the commit message, and commit once they agree.
    - Commit only the proposal. Leave any other uncommitted changes as they are.

3. **Start the agent** in the background with:
    - the proposal's path;
    - the branch name;
    - the commit hash of the proposal commit.

4. **Tell the user, in a few lines:**
    - the agent works in its own worktree and will push to `<branch>` and open a draft PR;
    - **switch to another branch and work on something else** in the meantime: `git switch -c <other>` or `git switch <other>`;
    - until the agent reports back, do not commit to, rebase, amend or push `<branch>`, because the agent's push must be a fast-forward;
    - the agent's permission prompts appear in this conversation, naming the agent.

5. **When the agent reports back**, give the user the PR link and the report's conclusion first. List every departure from the proposal and every failed check. Then tell them to get the commits with `git switch <branch> && git pull`.

**Fixes after review** also go to the implementer: resume it with the review comments. Never edit code in this conversation.

## Limits

- **Edit only the proposal.** Write no code and change no other file, with Bash or any other tool, even after the user asks to implement.
    - A hook from this skill enforces this: for the rest of the session it refuses edits to project files outside `claude-plans/`, except by the implementer agent.
- **If the discussion shows the change no longer fits one PR**, say so and suggest the split. Do not rewrite the proposal into several on your own.
