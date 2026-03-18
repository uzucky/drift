"""Check environment claims in config against actual system state."""

import os
import re
import subprocess
from drift.scanner import Issue


# Patterns: (regex, group_index_for_tool_name)
TOOL_ABSENCE_PATTERNS = [
    (re.compile(r'(\w+)は無い'), 1),
    (re.compile(r'(\w+)は無い'), 1),
    (re.compile(r'no\s+(\w+)', re.IGNORECASE), 1),
    (re.compile(r'(\w+)\s+is not available', re.IGNORECASE), 1),
    (re.compile(r"(\w+)に頼るな"), 1),
]

# Common words that match but aren't tools
NOT_TOOLS = {'the', 'a', 'an', 'it', 'is', 'not', 'are', 'was', 'has',
             'this', 'that', 'there', 'any', 'all', 'more', 'need',
             'install', 'use', 'run', 'set', 'get', 'make', 'test',
             'build', 'start', 'stop', 'open', 'close', 'read', 'write'}

# Known tool name mappings (Japanese/alias -> binary name)
TOOL_ALIASES = {
    'homebrew': 'brew',
    'Homebrew': 'brew',
}


def which(tool_name):
    """Check if a tool is available on the system."""
    try:
        result = subprocess.run(
            ['which', tool_name],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def check_os_version(claimed_version, line_num, config_path):
    """Check if OS version claim matches reality."""
    try:
        result = subprocess.run(
            ['sw_vers', '-productVersion'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            actual = result.stdout.strip()
            # Compare major version
            claimed_major = claimed_version.split('.')[0]
            actual_major = actual.split('.')[0]
            if claimed_major != actual_major:
                return Issue(
                    file=config_path,
                    line=line_num,
                    severity='warning',
                    check='stale-env',
                    message="Claims macOS {} but actual version is {}".format(
                        claimed_version, actual),
                )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def check(ctx):
    """Check environment claims against reality."""
    issues = []
    if not ctx.config_path or not os.path.isfile(ctx.config_path):
        return issues

    with open(ctx.config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    seen_tools = set()
    for i, line in enumerate(lines, 1):
        # Check tool absence claims
        for pattern, group_idx in TOOL_ABSENCE_PATTERNS:
            for match in pattern.finditer(line):
                tool = match.group(group_idx).strip()

                if tool.lower() in NOT_TOOLS:
                    continue

                # Map aliases
                binary = TOOL_ALIASES.get(tool, tool.lower())

                # Deduplicate
                if binary in seen_tools:
                    continue
                seen_tools.add(binary)

                path = which(binary)
                if path:
                    issues.append(Issue(
                        file=ctx.config_path,
                        line=i,
                        severity='warning',
                        check='stale-env',
                        message="Claims '{}' is not available but found at {}".format(
                            tool, path),
                    ))

        # Check macOS version claims
        mac_match = re.search(r'macOS\s+(\d+(?:\.\d+)?)', line)
        if mac_match:
            issue = check_os_version(mac_match.group(1), i, ctx.config_path)
            if issue:
                issues.append(issue)

    return issues
