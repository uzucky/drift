# drift

Detect when your AI agent's configuration has drifted from reality.

## The Problem

You write a `CLAUDE.md` with rules and constraints. Sessions pass. Things change. But the config stays the same.

- "jq is not available" — but you installed it last week
- 5 tasks are "in progress" with no commits in 10 days
- 30 memory files exist that nobody indexes
- The latest handover is a week old

Your AI agent makes decisions based on stale instructions. Nobody notices.

## Install

```bash
pip install drift-ai
```

## Quick Start

```bash
# Auto-detect CLAUDE.md, ACTIVE_PLAN.md, memory dir
drift check

# Specify files explicitly
drift check --config CLAUDE.md --plan ACTIVE_PLAN.md

# Only warnings and errors
drift check --severity warning

# Machine-readable output
drift check --json
```

## What It Checks

| Check | What It Detects | Example |
|-------|----------------|---------|
| `dead-ref` | File paths in config that don't exist | `IMPROVEMENT_PROTOCOL.md` was moved |
| `stale-env` | Environment claims that are wrong | "jq is not available" but jq is installed |
| `stale-task` | In-progress tasks with no git activity | Task marked 🟠 for 2 weeks, zero commits |
| `orphan-memory` | Memory files not in any index | `research.md` exists but isn't in MEMORY.md |
| `stale-handover` | Handovers that are too old | Latest handover is 5 days ago |
| `config-size` | Config files that are too large | CLAUDE.md is 300 lines (costs tokens every session) |

## Example Output

```
WARNING CLAUDE.md:49 Claims 'Homebrew' is not available but found at /usr/local/bin/brew
INFO ACTIVE_PLAN.md:31 Task 'タイトル改善' is in progress but no related git activity in 7 days
INFO soul/memory/intelligence/metrics_tracker.md File not referenced in any index

3 issues: 1 warning, 2 info
```

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

## Exit Codes

- `0` — No errors
- `1` — Errors found

## Born from Real Pain

This tool exists because:
- A product philosophy discussed in conversation was never recorded — discovered months later
- CLAUDE.md claimed "Homebrew is not available" for weeks after it was installed
- 30 intelligence files accumulated without being indexed, invisible to future sessions
- Tasks sat "in progress" for weeks with no one noticing

We built drift for ourselves first. Now it's yours.

## Claude Code Plugin

Install drift as a Claude Code plugin (no pip required — skill invocable directly from Claude):

```
/plugin marketplace add uzucky/drift
```

Then invoke with `/drift` inside any Claude Code session.

## License

MIT
