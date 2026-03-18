from drift.checks.dead_refs import check as check_dead_refs
from drift.checks.stale_env import check as check_stale_env
from drift.checks.stale_tasks import check as check_stale_tasks
from drift.checks.orphan_memory import check as check_orphan_memory
from drift.checks.stale_handover import check as check_stale_handover
from drift.checks.config_size import check as check_config_size

ALL_CHECKS = [
    check_dead_refs,
    check_stale_env,
    check_stale_tasks,
    check_orphan_memory,
    check_stale_handover,
    check_config_size,
]
