"""Tests for drift checks."""

import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from drift.scanner import Issue, ProjectContext
from drift.checks.dead_refs import check as check_dead_refs
from drift.checks.stale_env import check as check_stale_env
from drift.checks.stale_tasks import check as check_stale_tasks
from drift.checks.orphan_memory import check as check_orphan_memory
from drift.checks.stale_handover import check as check_stale_handover
from drift.checks.config_size import check as check_config_size

passed = 0
failed = 0


def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print('  PASS: {}'.format(name))
    else:
        failed += 1
        print('  FAIL: {}'.format(name))


def make_temp_dir():
    return tempfile.mkdtemp(prefix='drift_test_')


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


# === dead_refs tests ===
print('Testing dead_refs...')

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    write_file(config, '- Read `existing.md` first\n- Then `nonexistent.md`\n')
    write_file(os.path.join(tmpdir, 'existing.md'), 'hello')
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_dead_refs(ctx)
    test('detects missing file reference', len(issues) == 1)
    test('correct check name', issues[0].check == 'dead-ref' if issues else False)
    test('mentions nonexistent.md', 'nonexistent.md' in issues[0].message if issues else False)
finally:
    shutil.rmtree(tmpdir)

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    write_file(config, '```bash\ncat some_file.md\n```\n')
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_dead_refs(ctx)
    test('skips paths inside code blocks', len(issues) == 0)
finally:
    shutil.rmtree(tmpdir)

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    write_file(config, 'Visit https://example.com/file.md for docs\n')
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_dead_refs(ctx)
    test('skips URLs', len(issues) == 0)
finally:
    shutil.rmtree(tmpdir)

# === stale_env tests ===
print('Testing stale_env...')

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    # python3 should be available on any system running these tests
    write_file(config, '- **python3は無い** → 使うな\n')
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_stale_env(ctx)
    test('detects available tool claimed absent', len(issues) >= 1)
    test('mentions python3', any('python3' in i.message for i in issues))
finally:
    shutil.rmtree(tmpdir)

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    write_file(config, '- **zzz_nonexistent_toolは無い**\n')
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_stale_env(ctx)
    test('no false positive for missing tool', len(issues) == 0)
finally:
    shutil.rmtree(tmpdir)

# === stale_tasks tests ===
print('Testing stale_tasks...')

tmpdir = make_temp_dir()
try:
    plan = os.path.join(tmpdir, 'PLAN.md')
    write_file(plan, '| W1 | Some Task | 🟠 進行中 | notes |\n| W2 | Done Task | 🟢 完了 | done |\n')
    ctx = ProjectContext(root=tmpdir, plan_path=plan)
    issues = check_stale_tasks(ctx)
    # Without git, should return empty (graceful fallback)
    test('handles no git gracefully', isinstance(issues, list))
finally:
    shutil.rmtree(tmpdir)

# === orphan_memory tests ===
print('Testing orphan_memory...')

tmpdir = make_temp_dir()
try:
    mem_dir = os.path.join(tmpdir, 'memory')
    write_file(os.path.join(mem_dir, 'MEMORY.md'), '# Index\n- [tracked.md](tracked.md)\n')
    write_file(os.path.join(mem_dir, 'tracked.md'), 'content')
    write_file(os.path.join(mem_dir, 'orphan.md'), 'content')
    ctx = ProjectContext(root=tmpdir, memory_dir=mem_dir)
    issues = check_orphan_memory(ctx)
    test('detects orphan file', len(issues) == 1)
    test('orphan is correct file', 'orphan.md' in issues[0].file if issues else False)
finally:
    shutil.rmtree(tmpdir)

tmpdir = make_temp_dir()
try:
    mem_dir = os.path.join(tmpdir, 'memory')
    write_file(os.path.join(mem_dir, 'MEMORY.md'), '# Index\n- [a.md](a.md)\n- [b.md](b.md)\n')
    write_file(os.path.join(mem_dir, 'a.md'), 'content')
    write_file(os.path.join(mem_dir, 'b.md'), 'content')
    ctx = ProjectContext(root=tmpdir, memory_dir=mem_dir)
    issues = check_orphan_memory(ctx)
    test('no orphans when all indexed', len(issues) == 0)
finally:
    shutil.rmtree(tmpdir)

# === stale_handover tests ===
print('Testing stale_handover...')

tmpdir = make_temp_dir()
try:
    ho_dir = os.path.join(tmpdir, 'handovers')
    os.makedirs(ho_dir)
    write_file(os.path.join(ho_dir, '2020-01-01_old.md'), 'old')
    ctx = ProjectContext(root=tmpdir, handover_dir=ho_dir)
    issues = check_stale_handover(ctx)
    test('detects old handover', len(issues) == 1)
    test('mentions days old', 'days old' in issues[0].message if issues else False)
finally:
    shutil.rmtree(tmpdir)

tmpdir = make_temp_dir()
try:
    from datetime import datetime
    ho_dir = os.path.join(tmpdir, 'handovers')
    os.makedirs(ho_dir)
    today = datetime.now().strftime('%Y-%m-%d')
    write_file(os.path.join(ho_dir, '{}_fresh.md'.format(today)), 'fresh')
    ctx = ProjectContext(root=tmpdir, handover_dir=ho_dir)
    issues = check_stale_handover(ctx)
    test('no issue for fresh handover', len(issues) == 0)
finally:
    shutil.rmtree(tmpdir)

# === config_size tests ===
print('Testing config_size...')

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    write_file(config, 'short\n' * 10)
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_config_size(ctx)
    test('no issue for small config', len(issues) == 0)
finally:
    shutil.rmtree(tmpdir)

tmpdir = make_temp_dir()
try:
    config = os.path.join(tmpdir, 'CLAUDE.md')
    write_file(config, 'line\n' * 250)
    ctx = ProjectContext(root=tmpdir, config_path=config)
    issues = check_config_size(ctx)
    test('warns for large config', any(i.check == 'config-size' for i in issues))
finally:
    shutil.rmtree(tmpdir)

# === Summary ===
print('\n{}/{} tests passed.'.format(passed, passed + failed))
if failed:
    sys.exit(1)
