# battle_tested_skills

Open-source [Claude Code](https://claude.com/claude-code) skills for the
**CFA / quant community** — battle-tested helpers for investment research,
strategy stress-testing, and disciplined agentic engineering. Each skill is
self-contained: clone it, drop it into your Claude Code `skills/` directory,
and go.

## Skills

| Skill | What it does | Audience |
|---|---|---|
| [`roast-me`](roast-me/) | Coach-mode Socratic challenger that stress-tests an investment thesis, signal logic, backtest, or config. Runs a required quant-guardrail checklist (lookahead, survivorship, leakage, costs, overfitting) and ends with a written red-flag summary plus prioritized next moves. | CFA charterholders, quants, engineers |
| [`scaffold`](scaffold/) | Verifies or creates a project's context system — `docs/context/` working memory (memory, lessons, todo, results, session log), a `CLAUDE.md` that reads it on demand, size caps enforced by a hook plus `/compact-context`, state-capture hooks, and companion skills (`python-standards`, `excel-standards`). Idempotent. | Anyone building with Claude Code |
| [`excel-standards`](excel-standards/) | Financial-model discipline, CFI-based: inputs/calcs/outputs separation, blue/black/green font convention, one formula per row, balance-sheet and cash-flow tie-outs, scenario switches, sensitivities. Fires on any `.xlsx` model work; pairs with the `xlsx` skill, which does the file mechanics. | CFA charterholders, analysts, quants |
| [`python-standards`](python-standards/) | Python coding bar: enums, frozen dataclasses, Protocols, dependency injection, composition, mandatory type hints, pytest plus Hypothesis and mutation testing, with a mechanical verification per rule. Fires on any Python work. | Engineers, quants |
| [`map-project-architecture`](map-project-architecture/) | Maps a Python or TypeScript repo into one evidence-backed HTML architecture page — import layers, contracts, storage, external connections, user flow, infra. Every claim carries a `file:line` from `scripts/inventory.py`; a lens with no evidence says so instead of guessing. Published as an Artifact. | Engineers onboarding onto a codebase |
| [`color-palette`](color-palette/) | Builds a self-contained, live-editable design-system editor at `docs/business/brand/color-palette.html` — palette, type, buttons, charts, 10 slide templates, plus a derived dark theme — with WCAG contrast measured on every decision. `scripts/build.py` derives scales from four colors (paper, ink, accent, signal) and prints the same contrast audit the editor exports (runs the editor's engine with node; partial check without it); the editor exports CSS, a full `DESIGN.md`, YAML, JSON and a reference HTML. Skill text is in Spanish. | Founders, designers, anyone shipping a brand or deck |

## Install

Clone the repo, then run the installer. It copies every skill folder (any
folder with a `SKILL.md`) into your Claude Code skills directory.

```bash
git clone https://github.com/alanvaa06/battle_tested_skills.git
cd battle_tested_skills
```

**macOS / Linux**

```bash
./install.sh                 # → ~/.claude/skills (personal, all projects)
./install.sh .claude/skills  # → into the current project's skills dir
```

**Windows (PowerShell)**

```powershell
./install.ps1                 # → ~\.claude\skills (personal, all projects)
./install.ps1 .claude\skills  # → into the current project's skills dir
```

Restart Claude Code (or start a new session) so it picks up the new skill.
Claude discovers it from `SKILL.md` and triggers it from the `description` —
e.g. say *"roast my thesis"* to fire `roast-me`.

### Manual install (one skill)

```bash
cp -r roast-me ~/.claude/skills/roast-me      # personal
cp -r roast-me .claude/skills/roast-me        # per-project
```

### scaffold and map-project-architecture

Both are regular skills with a `SKILL.md`, so the installers pick them up.
`scaffold` ships its project files under `scaffold/templates/` and copies them
into a project when invoked (its companion skills `python-standards` and
`excel-standards` are top-level skills here, installed by the same installer); `map-project-architecture` ships its inventory
scripts and tests under `map-project-architecture/scripts/`.

## Skill anatomy

```
<skill-name>/
├── SKILL.md          # name + description frontmatter, then instructions
├── references/       # optional deeper material loaded on demand
├── templates/        # optional files the skill copies into a project
└── scripts/          # optional helper scripts the skill runs
```

## Contributing

This is a community container — PRs adding or improving skills are welcome.
Keep each skill self-contained, give it a clear trigger `description`, and add
a row to the Skills table above.

> Nothing here is investment advice.
