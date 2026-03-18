"""Check for stale in-progress tasks with no recent git activity."""

import os
import re
import subprocess
from drift.scanner import Issue


IN_PROGRESS_MARKERS = ['🟠 進行中', '🟠', 'in progress', 'In Progress']


def get_recent_commits(days=7):
    """Get recent commit messages."""
    try:
        result = subprocess.run(
            ['git', 'log', '--since={} days ago'.format(days),
             '--oneline', '--all', '--no-merges'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ''


def extract_keywords(task_text):
    """Extract searchable keywords from a task description."""
    keywords = []
    # Extract task IDs like C-07, P-01, W5-3
    ids = re.findall(r'[A-Z]-\d+|W\d+-\d+', task_text)
    keywords.extend(ids)
    # Extract English words (3+ chars)
    words = re.findall(r'[a-zA-Z]{3,}', task_text)
    keywords.extend(w.lower() for w in words)
    # Extract tool/product names
    names = re.findall(r'[a-z]+-[a-z]+', task_text.lower())
    keywords.extend(names)
    return keywords


def check(ctx):
    """Find in-progress tasks with no recent git activity."""
    issues = []
    if not ctx.plan_path or not os.path.isfile(ctx.plan_path):
        return issues

    with open(ctx.plan_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    recent_commits = get_recent_commits(7).lower()
    if not recent_commits:
        return issues

    for i, line in enumerate(lines, 1):
        is_in_progress = any(marker in line for marker in IN_PROGRESS_MARKERS)
        if not is_in_progress:
            continue

        # Parse table row: | ID | Task | Status | Notes |
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if len(cells) < 2:
            continue

        task_desc = ' '.join(cells[:3])
        keywords = extract_keywords(task_desc)

        if not keywords:
            continue

        # Check if any keyword appears in recent commits
        found = any(kw in recent_commits for kw in keywords)
        if not found:
            task_name = cells[1] if len(cells) > 1 else task_desc[:50]
            issues.append(Issue(
                file=ctx.plan_path,
                line=i,
                severity='info',
                check='stale-task',
                message="Task '{}' is in progress but no related git activity in 7 days".format(
                    task_name.strip()),
            ))

    return issues
