"""Check if config file is getting too large."""

import os
from drift.scanner import Issue


def check(ctx, max_lines=200, max_words=3000):
    """Check config file size."""
    issues = []
    if not ctx.config_path or not os.path.isfile(ctx.config_path):
        return issues

    with open(ctx.config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.count('\n') + 1
    words = len(content.split())

    if lines > max_lines:
        issues.append(Issue(
            file=ctx.config_path,
            line=0,
            severity='warning',
            check='config-size',
            message="Config is {} lines (recommended max: {})".format(
                lines, max_lines),
        ))

    if words > max_words:
        issues.append(Issue(
            file=ctx.config_path,
            line=0,
            severity='info',
            check='config-size',
            message="Config is {} words — large configs cost more tokens per session".format(
                words),
        ))

    return issues
