
# RSE plugins

This repo is a collection of plugins, also called a  **marketplace**. "RSE" in the name stands for "Research Software Engineering". 

The marketplace currently collects Claude plugins that may useful in software development for research ("dev" plugins), or that support researches in their code development ("science" plugins).

> [!NOTE] Some concepts
> A **plugin** is a package that bundles skills that share some resources (e.g. subagents) and install, update and switch on or off together. 
>
> **Skills** can be exposed to the user or not. A useful way to frame this can be:
> - user-invocable skills represent a *workflow*, as a set of instructions the main Claude follows itself, in the conversation that triggers the skill. 
> - non-user-invocable skills represent a packet of *know-how* (e.g. this is how we write proposals), that the main Claude or subagents can access.
>
> An agent (or **subagent** here) is a separate worker the main Claude can delegate to. The two often pair well in one plugin. E.g.: a skill can describe a workflow that includes “hand the draft to the fact-checker agent” as one of its steps. Users do not need to trigger this delegation: it is defined in the corresponding skill.


## Installation
First add the marketplace, then install the plugins you want from it.

From Claude Code:
```
/plugin marketplace add sfmig/rse-plugins

# To install the dev plugins:
/plugin install dev@rse-plugins

# To install the science plugins:
/plugin install science@rse-plugins
```

From a local clone:
```
git clone https://github.com/sfmig/rse-plugins.git
```
then, in Claude Code:
```
/plugin marketplace add /path/to/rse-plugins

# To install the dev plugins:
/plugin install dev@rse-plugins

# To install the science plugins:
/plugin install science@rse-plugins
```

You can also run `/plugin` and pick the plugins from the **Discover** tab. Run `/reload-plugins` (or start a new session) to load them. 

In the chat interface, you can click `/` and select "Manage plugins" > select the Marketplaces tab, and paste the path to the `rse-plugins` clone.



## The `dev` plugin

The skills in this plugin aim to support developers that write software for research. They share three goals:

- Make agent output easy for humans to digest.
- Keep a human in the loop.
- Show it visually first. Wherever they fit, documents use mermaid diagrams, signatures, diffs and tables rather than paragraphs. 

Currently, the plugin has two workflows:

| Skill | What it does |
|---|---|
| `proposal` | Given a feature request, it researches a codebase and writes a proposal for you to review |
| `discuss` | Answers your questions about a proposal, refines it with your agreement, and finally hands it to an agent to implement. |


You can start a workflow explicitly with `/dev:<skill>` (e.g. `/dev:proposal`). The main Claude agent can also start one itself when the conversation matches the skill's `when_to_use` description.





### User workflow

0. Checkout a branch for the feature.

1. **Describe** the desired feature to Claude and prompt it to draft a proposal.
    - If you want to be explicit, you can trigger it with `/dev:proposal`.

2. The main Claude agent will follow the workflow described in the `proposal` skill, delegating to subagents when necessary. It will **produce a proposal markdown file** with diagrams, code snippets, bullet-point lists and collapsible sections. 
    - The goal is to transmit clearly a detailed implementation of a feature while avoiding dense prose, providing more details gradually, and using visual communication where possible and relevant.
    - The proposal will be added to a `claude-plans` subdirectory, under the current directory.

3. Once the proposal is ready, **start a new Claude conversation with `/dev:discuss`**, and ask questions and clarifications about the proposal by selecting specific sections of it.
    - Where the proposal is confusing, Claude suggests a clarification, and adds it only if you agree. 
    - In the "Points to discuss" section, you can add your conclusions that you want the agent to take into account when implementing.
    - Feel free to make edits on the proposal yourself, to make the description of the implementation as clear as possible to future you or others. I find that by rephrasing some of the sections and checking with Claude if I understood correctly I often get a better understanding.

4. Once you are happy with the proposal and feel like you have a clear idea of how the feature is designed, ask Claude to implement it and open a draft PR.
    - Claude commits the proposal on your feature branch (after asking). This way the proposal is kept in the PR history.
    - Then it hands the proposal to the `implementer` agent. The agent works in its own git worktree, pushes its commits to your feature branch and opens the draft PR.
    - Meanwhile, **switch to another branch and work on something else.** The agent's worktree is separate, so your checkout does not affect it.
    - Until the agent reports back, don't commit to, rebase or push the feature branch: the agent's push must be a fast-forward.
    - When it's done, Claude gives you the PR link. Run `git switch <feature-branch> && git pull` to get the commits locally.
    - After implementing the PR, the proposal is deleted (but will remain in the PR history for reference).



### Agentic workflow

When the `proposal` workflow is triggered, this is what happens under the hood:

1. An edit guard is enabled, that makes only `claude-plans` writable (bash is not covered). 
    - This is because during the drafting of the proposal, we do not want code to be edited.

2. The main Claude agent delegates to an `investigator` agent (Sonnet), that collects relevant facts for the proposal and reports back to the main agent.

3. Using the gathered information, the main agent generates a draft proposal.

4. The draft proposal is then checked in three ways:
    - First, we check that the mermaid diagrams render correctly with a bash script.
    - Then, it is passed to two subagents:
        - One of them checks the style matches the guidelines under `writing-style`
        - Another one acts as a cold-reader and checks for confusing points.

5. The main Claude agent receives the review reports and makes the necessary edits 

6. After the final edits, the proposal is presented to the user for discussion.

7. The user discusses the proposal in a conversation with a new agent, started with `/dev:discuss <path>`


8. When the user asks to implement the proposal, the "discuss" conversation commits the proposal on the feature branch and starts the `implementer` subagent in the background:
    - The subagent runs in its own git worktree, on a new branch. It points that branch at the feature branch's latest commit with `git reset --hard <branch>`, without checking the feature branch out (this is so the feature branch can stay checked out in your main checkout).
    - The subagent then makes one commit per step of the proposal, runs the proposal's verifications, and deletes the proposal in a last commit.
    - It pushes to the (remote) feature branch as a fast-forward and opens a draft PR. It never force-pushes.
    - Once the push and the PR have succeeded, it deletes its worktree's own local branch. If it stops early, it keeps that branch, because its commits exist only there.
    - If the proposal doesn't match the code, it stops and reports instead of guessing, because a subagent can't ask the user questions.


In the repo you work on, you may want to gitignore `.claude/worktrees/`, where the agent's worktree is created.


## The `science` plugin

The skills in this plugin aim to support scientists and researchers who write code.

| Skill | What it does |
|---|---|
| `release` | Gets a repo ready to cite and archive: writes or updates `CITATION.cff`, checks the licence is consistent, and lists the Zenodo/GitHub steps that mint a DOI. |

Start it with `/science:release [version]`. It edits files only after you agree. It never tags, pushes, or creates GitHub releases: it gives you the commands to run instead.


## Contributing

### Develop with live edits

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

### Release a change

Users who install the plugin from the marketplace get a copy of the `version` in [plugin.json](dev/.claude-plugin/plugin.json). So to pass on any updates, we need to bump that version:

1. Bump `version` in `dev/.claude-plugin/plugin.json`.
2. Validate, as in step 5 above, and push.
3. Users update with `/plugin marketplace update rse-plugins`.

### To test the edit guard and the implementer

The skills' hook blocks edits outside `claude-plans/`, except by the `implementer` agent. To check it, in a test repo on a feature branch:

1. Run `/dev:discuss <proposal>`.
2. Ask Claude to edit a source file. The edit should be refused, with a message naming the `dev` plugin.
3. Ask Claude to implement. It should commit the proposal, start the `implementer` agent, and tell you to switch branch.
4. Check that the agent's edits go through. If they're refused too, the agent's `agent_type` isn't what the hook expects:
    - Add `printf '%s\n' "$i" | jq -c '{agent_type}' >> "$TMPDIR/guard.log"` after the first line of the hook to see the real value.
    - Then fix the `case` pattern in both skills.
5. Check that the draft PR is opened from the feature branch, with one commit per step and the proposal deleted in the last one.

If the hook never fires, check `/hooks` and the debug log.

### Notes for developers
* Files a skill reads should live inside that skill's folder. Claude resolves paths in SKILL.md relative to the skill directory


## Inspo
* https://github.com/timholy/claude_config/tree/main
* https://github.com/erlichlab/delab-skills