
# RSE plugins

Claude plugins useful in software development for research.


A plugin is a package that bundles several related pieces (here, skills and subagents) so they install, update and switch on or off together.


## Included skills

| Name | When is it triggered? |
| --- | --- |
|`/plan-with-diagrams` | |
|`/review-with-diagrams`| |
| ... | ... |


## Installation
From Claude code:
```
/plugin marketplace add ...
```


## Usage
...

## Notes for developers
* Files a skill reads should live inside that skill's folder. Claude resolves paths in SKILL.md relative to the skill directory


## Inspo
* https://github.com/timholy/claude_config/tree/main
* https://github.com/erlichlab/delab-skills