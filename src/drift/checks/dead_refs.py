"""Check for file path references in config that no longer exist."""

import os
import re
from drift.scanner import Issue


# Patterns that look like file paths in markdown
PATH_PATTERNS = [
    re.compile(r'`([^`]+\.\w{1,5})`'),           # `path/to/file.ext`
    re.compile(r'`([^`]+/[^`]+)`'),               # `path/to/dir/`
    re.compile(r'\[.*?\]\(([^)]+\.md)\)'),         # [text](file.md)
    re.compile(r'\[.*?\]\(([^)]+\.py)\)'),         # [text](file.py)
    re.compile(r'\[.*?\]\(([^)]+\.yaml)\)'),       # [text](file.yaml)
    re.compile(r'\[.*?\]\(([^)]+\.json)\)'),       # [text](file.json)
]

# Skip these patterns
SKIP_PATTERNS = [
    re.compile(r'^https?://'),       # URLs
    re.compile(r'\*'),               # Globs
    re.compile(r'XX|YYYY'),          # Templates
    re.compile(r'^\$'),              # Variables
    re.compile(r'^\.env'),           # .env files (secrets)
    re.compile(r'^#'),               # Anchors
    re.compile(r'<'),                # HTML/XML
    re.compile(r'^\w+\.\w+\('),     # function calls like path.join()
]


def should_skip(path_str):
    """Return True if this reference should not be checked."""
    for pat in SKIP_PATTERNS:
        if pat.search(path_str):
            return True
    # Skip if no extension and no slash (likely a keyword, not a path)
    if '/' not in path_str and '.' not in path_str:
        return True
    return False


def find_file_recursive(root, filename):
    """Search for filename anywhere under root."""
    for dirpath, _, filenames in os.walk(root):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


def check(ctx):
    """Scan config file for dead file references."""
    issues = []
    if not ctx.config_path or not os.path.isfile(ctx.config_path):
        return issues

    with open(ctx.config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    seen = set()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue

        # Skip inside code blocks (examples/templates)
        if in_code_block:
            continue

        for pattern in PATH_PATTERNS:
            for match in pattern.finditer(line):
                ref = match.group(1).strip()

                if should_skip(ref):
                    continue

                if ref in seen:
                    continue
                seen.add(ref)

                # Try resolving the path
                abs_path = os.path.join(ctx.root, ref)
                if os.path.exists(abs_path):
                    continue

                # Try just the basename recursively
                basename = os.path.basename(ref)
                found = find_file_recursive(ctx.root, basename)
                if found:
                    continue

                issues.append(Issue(
                    file=ctx.config_path,
                    line=i,
                    severity='warning',
                    check='dead-ref',
                    message="Referenced path '{}' does not exist".format(ref),
                ))

    return issues
