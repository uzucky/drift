"""Check for memory files not referenced in any index."""

import os
import re
from drift.scanner import Issue


INDEX_NAMES = ['MEMORY.md', 'INDEX.md', 'README.md']
SKIP_DIRS = {'handovers', 'inbox', '__pycache__', '.git'}
SKIP_FILES = {'ACTIVE_PLAN.md'}


def find_references_in_file(filepath):
    """Extract filenames referenced in a markdown file."""
    refs = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Markdown links: [text](filename.md)
        for match in re.finditer(r'\[.*?\]\(([^)]+)\)', content):
            ref = match.group(1).strip()
            refs.add(os.path.basename(ref))
        # Backtick references: `filename.md`
        for match in re.finditer(r'`([^`]+\.md)`', content):
            refs.add(os.path.basename(match.group(1)))
        # Plain references: - filename.md or filename.md —
        for match in re.finditer(r'[-\s](\w[\w_-]+\.md)', content):
            refs.add(match.group(1))
    except (OSError, UnicodeDecodeError):
        pass
    return refs


def check(ctx):
    """Find memory files not referenced in any index."""
    issues = []
    if not ctx.memory_dir or not os.path.isdir(ctx.memory_dir):
        return issues

    # Walk the memory directory
    for dirpath, dirnames, filenames in os.walk(ctx.memory_dir):
        # Skip certain directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        # Find index files in this directory
        index_refs = set()
        index_found = False
        for idx_name in INDEX_NAMES:
            idx_path = os.path.join(dirpath, idx_name)
            if os.path.isfile(idx_path):
                index_found = True
                index_refs.update(find_references_in_file(idx_path))

        if not index_found:
            continue

        # Check each .md file in this directory
        for fname in filenames:
            if not fname.endswith('.md'):
                continue
            if fname in INDEX_NAMES:
                continue
            if fname in SKIP_FILES:
                continue

            if fname not in index_refs:
                issues.append(Issue(
                    file=os.path.join(dirpath, fname),
                    line=0,
                    severity='info',
                    check='orphan-memory',
                    message="File not referenced in any index",
                ))

    return issues
