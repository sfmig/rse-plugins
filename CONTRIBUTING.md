# Contributing

## Develop with live edits

During development of the plugin, you can load the plugin straight from this repo, so Claude Code reads your working copy instead of an installed one.

1. **Load the plugin folder** in a new session. Use one of these:
    - Terminal:

        ```bash
        claude --plugin-dir /path/to/rse-plugins/dev
        ```

    - VS Code, or anywhere you can't pass a flag: add the folder to your *user* settings, `~/.claude/settings.json`, then open a new session. Project settings can't set this variable.

        ```json
        { "env": { "CLAUDE_CODE_PLUGIN_DIRS": "/path/to/rse-plugins/dev" } }
        ```

    Pointing either option at `rse-plugins/` instead loads every plugin folder in it.

2. **Check that it loaded.** 
    - `/dev:proposal` should autocomplete, 
    - `/plugin` lists the plugin under **Installed**. Load errors appear under **Errors**.

3. **Edit the files**
    - After editing, run `/reload-plugins` in the session to apply the changes.

4. **Re-run the skill after editing its frontmatter.** 
    - Skill hooks are registered when the skill runs, so run `/dev:proposal` again, then check `/hooks`.

5. **Validate before committing**:

    ```bash
    claude plugin validate ./dev    # plugin manifest and skill/agent frontmatter
    claude plugin validate .        # marketplace manifest
    ```

6. **To check the diagrams render**:

    ```bash
    dev/skills/proposal/scripts/check-mermaid.sh README.md
    ```

    It needs `mmdc` or Node.js (`npx`). On first use, also install the headless browser that mermaid-cli renders with: `npx puppeteer browsers install chrome-headless-shell`.

> [!WARNING]
> Don't also install the plugin from the marketplace while developing. Two plugins with the same name would be loaded.

## Release a change

Users who install the plugin from the marketplace get a copy of the `version` in [plugin.json](dev/.claude-plugin/plugin.json). So to pass on any updates, we need to bump that version:

1. Bump `version` in `dev/.claude-plugin/plugin.json`.
2. Validate, as in step 5 above, and push.
3. Users update with `/plugin marketplace update rse-plugins`.

## To test the edit guard and the implementer

The skills' hook blocks edits outside `claude-plans/`, except by the `implementer` agent. To check it, in a test repo on a feature branch:

1. Run `/dev:discuss <proposal>`.
2. Ask Claude to edit a source file. The edit should be refused, with a message naming the `dev` plugin.
3. Ask Claude to implement. It should commit the proposal, start the `implementer` agent, and tell you to switch branch.
4. Check that the agent's edits go through. If they're refused too, the agent's `agent_type` isn't what the hook expects:
    - Add `printf '%s\n' "$i" | jq -c '{agent_type}' >> "$TMPDIR/guard.log"` after the first line of the hook to see the real value.
    - Then fix the `case` pattern in both skills.
5. Check that the draft PR is opened from the feature branch, with one commit per step and the proposal deleted in the last one.

If the hook never fires, check `/hooks` and the debug log.

## Notes for developers
* Files a skill reads should live inside that skill's folder. Claude resolves paths in SKILL.md relative to the skill directory
