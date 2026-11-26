# pr-review

A Claude Code skill that builds a review package for a large pull request: the aim and diagrams, an atomic copy of the branch, and two reviews in difit (code, then tests) with preloaded questions. It maps and indexes the PR; the reviewer judges the code.

Start it with `/pr-review [branch, PR number or URL]`, from inside the reviewed repo.

## How it runs

```mermaid
flowchart TD
    subgraph legend [Legend]
        LA["agent judges"]:::agent
        LS["script, same every time"]:::script
        LU["user"]:::user
    end

    PR(["PR branch"]) --> F["1. facts.py<br/>commits, files, changed functions"]:::script
    F --> G["2. group the commits<br/>plan.json and stage files"]:::agent
    G --> BA["build_atomic.py<br/>commits, zero-diff check"]:::script
    BA --> AB(["branch-atomic, local"])
    AB --> IP["3. init_package.py<br/>copies template/ and scripts/package/"]:::script
    IP --> D["4. draft_tables.py<br/>commits, sessions, tests, not tested, components"]:::script
    D --> W["write the pages<br/>aim, diagrams, weights, behaviours"]:::agent
    W --> DL["diagram_links.py<br/>click lines and links table"]:::script
    DL --> Q["5. preloaded questions<br/>questions-code.json, questions-tests.json"]:::agent
    Q --> C["6. check_package.py and check-mermaid.sh"]:::script
    C -- FAIL --> W
    C -- ok --> P["7. present the package<br/>quarto preview"]:::agent
    P --> RC["review.py all, atomic or sessions<br/>code review, no test files"]:::user
    RC --> RT["review.py tests<br/>tests next to their code"]:::user
    RT --> CM(["comments/code/pass-N<br/>comments/tests/pass-N"])
    CM --> A["answer the threads<br/>replies in comments.json"]:::agent
    A --> RC
    A -- resolved and asked --> IM["implement on the PR branch<br/>atomic commits"]:::agent
    PR -. new commits .-> EX["atomic.py extend"]:::script
    EX -.-> AB

    classDef agent fill:#fff3cd,stroke:#b8860b,color:#000
    classDef script fill:#d4edda,stroke:#2e7d32,color:#000
    classDef user fill:#d6e4f5,stroke:#1f5fa8,color:#000
```

Arrows are steps in order, numbered as in [SKILL.md](SKILL.md). Rounded boxes are what the steps make. Dotted arrows: when the PR branch gains commits.

## Files

| Path | Holds | Read or run by |
|---|---|---|
| [`SKILL.md`](SKILL.md) | The steps | The agent, at the start |
| [`DECISIONS.md`](DECISIONS.md) | Why each choice was made | The agent, when a rule seems arbitrary |
| [`MAINTAINING.md`](MAINTAINING.md) | difit and Quarto facts, traps, ideas not done | Whoever changes the fixed files |
| [`example/`](example/README.md) | The pages written for one real PR | The agent, as the model for each page |
| [`template/`](template/) | The Quarto page | `init_package.py`, copied into each package |
| [`scripts/package/`](scripts/package/) | The difit scripts: `review.py`, `atomic.py`, … | `init_package.py`, copied into each package; the reviewer runs `review.py` |
| [`scripts/`](scripts/) | `facts.py`, `build_atomic.py`, `init_package.py`, `draft_tables.py`, `diagram_links.py`, `check_package.py` | The agent |
