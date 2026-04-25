---
name: drift
description: Detect when an AI agent's configuration has drifted from reality. Scans CLAUDE.md, ACTIVE_PLAN.md, and memory directories for dead file references, stale environment claims, orphan memory files, stale handovers, outdated in-progress tasks, and oversized config files. Install with `pip install drift-ai`, invoke with `drift check`.
---

# drift — Configuration drift detector

Use this skill when the user suspects their AI agent's setup files have fallen out of sync with reality, or as part of a weekly hygiene routine on an AI-driven repository. `drift` is a deterministic scanner (no LLM calls) that reports 6 kinds of drift in under 2 seconds on typical repos.

## When to invoke

- User asks "is my config still accurate?" / "check CLAUDE.md" / "find stale tasks" / "audit memory"
- Start of a fresh session on a long-lived project
- After environment changes (tool installs, path changes, plan rewrites)
- Weekly routine on an AI-driven repo

## How to run

```bash
# First-time install
pip install drift-ai

# Auto-detect CLAUDE.md / ACTIVE_PLAN.md / memory dir
drift check

# Explicit paths
drift check --config CLAUDE.md --plan ACTIVE_PLAN.md --memory-dir soul/memory

# Filter by severity
drift check --severity warning   # error + warning only

# Machine-readable output
drift check --json
```

## What it detects

| Check | What | Example |
|---|---|---|
| `dead-ref` | File paths in config that don't exist | `IMPROVEMENT_PROTOCOL.md` was moved |
| `stale-env` | Environment claims that are false | "jq is not available" but jq is installed |
| `stale-task` | In-progress tasks with no git activity | Task marked 🟠 for 2 weeks, zero commits |
| `orphan-memory` | Memory files not referenced in any index | `research.md` exists but isn't in `MEMORY.md` |
| `stale-handover` | Handovers too old | Latest handover is 5 days ago |
| `config-size` | Config files too large | `CLAUDE.md` 300+ lines (token cost per session) |

## Example output

```
WARNING CLAUDE.md:49 Claims 'Homebrew' is not available but found at /usr/local/bin/brew
INFO    ACTIVE_PLAN.md:31 Task 'タイトル改善' is in progress but no related git activity in 7 days
INFO    soul/memory/intelligence/metrics_tracker.md File not referenced in any index

3 issues: 1 warning, 2 info
```

## Exit codes

- `0` — no errors found (info/warning may still be present unless `--severity error` is set)
- `1` — errors found

## Interpretation guidelines for Claude

- **Report findings as-is.** Don't auto-fix.
- **Let the user decide which drift to resolve.** Some drift is intentional (e.g. a task legitimately paused).
- **Group by file** when presenting to the user, not by drift type.
- **Suggest the specific line edit** when a `dead-ref` or `stale-env` is obvious (e.g. "remove line 49 or update to 'Homebrew is available'").
- If `--json` output is requested, parse and summarize; don't just dump raw JSON.

## Options

```
drift check
  --config PATH       Config file (default: auto-detect CLAUDE.md)
  --plan PATH         Plan file (default: auto-detect ACTIVE_PLAN.md)
  --memory-dir PATH   Memory directory
  --severity LEVEL    Minimum: error, warning, info (default: info)
  --json              Machine-readable output
  --no-color          Disable colors
  -q, --quiet         Minimal output
```

## Why this exists

Built to solve a recurring pain on a production AI-driven repo:
- Config files claimed "Homebrew is not available" for weeks after install
- 30+ memory files accumulated without being indexed
- Tasks sat "in progress" for weeks with no one noticing
- The AI made decisions based on stale instructions, and nobody spotted it until much later

`drift` is deterministic, fast, and opinionated about what counts as drift. It's not trying to be a general linter — it's a specialized detector for the **agent-configuration-vs-reality** gap.

## License

MIT. Source: <https://github.com/uzucky/drift>
