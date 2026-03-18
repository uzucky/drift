"""Check if the latest handover is too old."""

import os
import re
from datetime import datetime, timedelta
from drift.scanner import Issue


DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')


def check(ctx, max_age_days=3):
    """Check handover freshness."""
    issues = []
    if not ctx.handover_dir or not os.path.isdir(ctx.handover_dir):
        return issues

    # Find the most recent date in handover filenames
    latest_date = None
    latest_file = None

    for fname in os.listdir(ctx.handover_dir):
        match = DATE_PATTERN.search(fname)
        if match:
            try:
                d = datetime.strptime(match.group(1), '%Y-%m-%d')
                if latest_date is None or d > latest_date:
                    latest_date = d
                    latest_file = fname
            except ValueError:
                continue

    if latest_date is None:
        issues.append(Issue(
            file=ctx.handover_dir,
            line=0,
            severity='warning',
            check='stale-handover',
            message="No handover files with dates found",
        ))
        return issues

    age = datetime.now() - latest_date
    if age > timedelta(days=max_age_days):
        issues.append(Issue(
            file=os.path.join(ctx.handover_dir, latest_file),
            line=0,
            severity='warning',
            check='stale-handover',
            message="Latest handover is {} days old (threshold: {} days)".format(
                age.days, max_age_days),
        ))

    return issues
