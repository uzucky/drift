"""CLI entry point for drift."""

import argparse
import json
import sys
from drift import __version__
from drift.scanner import resolve_context, scan

# Colors
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
DIM = '\033[2m'
BOLD = '\033[1m'
RESET = '\033[0m'

SEVERITY_COLORS = {
    'error': RED,
    'warning': YELLOW,
    'info': CYAN,
}

SEVERITY_ORDER = {'error': 0, 'warning': 1, 'info': 2}


def format_issue(issue, use_color=True):
    """Format a single issue for terminal output."""
    color = SEVERITY_COLORS.get(issue.severity, '')
    reset = RESET if use_color else ''
    color = color if use_color else ''
    dim = DIM if use_color else ''
    bold = BOLD if use_color else ''

    loc = issue.file
    if issue.line:
        loc = '{}:{}'.format(issue.file, issue.line)

    return '{}{}{} {}{}{} {}{}{}'.format(
        color, issue.severity.upper(), reset,
        dim, loc, reset,
        bold, issue.message, reset,
    )


def cmd_check(args):
    """Run all drift checks."""
    ctx = resolve_context(
        config=args.config,
        plan=args.plan,
        memory_dir=args.memory_dir,
    )

    # Show what we're scanning
    if not args.quiet and not args.json_output:
        found = []
        if ctx.config_path:
            found.append('config: ' + ctx.config_path)
        if ctx.plan_path:
            found.append('plan: ' + ctx.plan_path)
        if ctx.memory_dir:
            found.append('memory: ' + ctx.memory_dir)
        if ctx.handover_dir:
            found.append('handovers: ' + ctx.handover_dir)
        if found:
            print('Scanning: {}'.format(', '.join(found)))
        else:
            print('No config files found. Use --config to specify.')
            return 0

    issues = scan(ctx)

    # Filter by severity
    min_severity = SEVERITY_ORDER.get(args.severity, 2)
    issues = [i for i in issues if SEVERITY_ORDER.get(i.severity, 2) <= min_severity]

    # JSON output
    if args.json_output:
        summary = {}
        for i in issues:
            summary[i.severity] = summary.get(i.severity, 0) + 1
        output = {
            'issues': [i.to_dict() for i in issues],
            'summary': summary,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 1 if summary.get('error', 0) > 0 else 0

    # Terminal output
    use_color = not args.no_color and sys.stdout.isatty()

    if not issues:
        if not args.quiet:
            print('No issues found.')
        return 0

    for issue in issues:
        print(format_issue(issue, use_color))

    # Summary
    if not args.quiet:
        summary = {}
        for i in issues:
            summary[i.severity] = summary.get(i.severity, 0) + 1
        parts = []
        for sev in ['error', 'warning', 'info']:
            if sev in summary:
                parts.append('{} {}'.format(summary[sev], sev))
        print('\n{} issues: {}'.format(len(issues), ', '.join(parts)))

    return 1 if any(i.severity == 'error' for i in issues) else 0


def main():
    parser = argparse.ArgumentParser(
        prog='drift',
        description='Detect drift in AI agent configuration files.',
    )
    parser.add_argument('--version', action='version',
                        version='drift {}'.format(__version__))

    sub = parser.add_subparsers(dest='command')

    check_parser = sub.add_parser('check', help='Run all drift checks')
    check_parser.add_argument('--config', help='Path to config file (default: auto-detect CLAUDE.md)')
    check_parser.add_argument('--plan', help='Path to plan file (default: auto-detect ACTIVE_PLAN.md)')
    check_parser.add_argument('--memory-dir', help='Path to memory directory')
    check_parser.add_argument('--severity', default='info',
                              choices=['error', 'warning', 'info'],
                              help='Minimum severity to report (default: info)')
    check_parser.add_argument('--json', dest='json_output', action='store_true',
                              help='Output as JSON')
    check_parser.add_argument('--no-color', action='store_true',
                              help='Disable colored output')
    check_parser.add_argument('-q', '--quiet', action='store_true',
                              help='Minimal output')

    args = parser.parse_args()

    if args.command == 'check':
        sys.exit(cmd_check(args))
    else:
        # Default to check if no subcommand
        args.config = None
        args.plan = None
        args.memory_dir = None
        args.severity = 'info'
        args.json_output = False
        args.no_color = False
        args.quiet = False
        sys.exit(cmd_check(args))


if __name__ == '__main__':
    main()
