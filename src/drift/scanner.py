"""Core scanner: Issue model, ProjectContext, and orchestration."""

import os
import subprocess


class Issue:
    __slots__ = ('file', 'line', 'severity', 'check', 'message')

    def __init__(self, file, line, severity, check, message):
        self.file = file
        self.line = line
        self.severity = severity
        self.check = check
        self.message = message

    def to_dict(self):
        return {
            'file': self.file,
            'line': self.line,
            'severity': self.severity,
            'check': self.check,
            'message': self.message,
        }


class ProjectContext:
    """Resolved paths and metadata for the project being scanned."""

    def __init__(self, root, config_path=None, plan_path=None,
                 memory_dir=None, handover_dir=None):
        self.root = root
        self.config_path = config_path
        self.plan_path = plan_path
        self.memory_dir = memory_dir
        self.handover_dir = handover_dir


def find_git_root():
    """Find git repository root, or return cwd."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return os.getcwd()


def resolve_context(config=None, plan=None, memory_dir=None):
    """Auto-detect or use explicit paths."""
    root = find_git_root()

    # Auto-detect CLAUDE.md
    if config is None:
        for name in ['CLAUDE.md', 'claude.md', '.claude.md']:
            candidate = os.path.join(root, name)
            if os.path.isfile(candidate):
                config = candidate
                break

    # Auto-detect ACTIVE_PLAN.md
    if plan is None:
        candidates = [
            os.path.join(root, 'soul', 'memory', 'ACTIVE_PLAN.md'),
            os.path.join(root, 'ACTIVE_PLAN.md'),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                plan = candidate
                break

    # Auto-detect memory directory
    if memory_dir is None:
        candidates = [
            os.path.join(root, 'soul', 'memory'),
            os.path.join(root, '.claude', 'memory'),
            os.path.join(root, 'memory'),
        ]
        for candidate in candidates:
            if os.path.isdir(candidate):
                memory_dir = candidate
                break

    # Auto-detect handover directory
    handover_dir_resolved = None
    if memory_dir:
        candidate = os.path.join(memory_dir, 'handovers')
        if os.path.isdir(candidate):
            handover_dir_resolved = candidate

    return ProjectContext(
        root=root,
        config_path=config,
        plan_path=plan,
        memory_dir=memory_dir,
        handover_dir=handover_dir_resolved,
    )


def scan(ctx):
    """Run all applicable checks and return list of Issues."""
    from drift.checks import ALL_CHECKS
    issues = []
    for check_fn in ALL_CHECKS:
        try:
            issues.extend(check_fn(ctx))
        except Exception:
            pass
    return issues
