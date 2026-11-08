"""Host CPU telemetry and team view admin gating (types regen cc5d17b / INF-1244).

``SystemInfo.host_cpu`` carries cpufreq/SMT/hugepage knobs the engine reads from
/sys for host diagnostics. ``TeamViewDTO.needs_admin_access`` lists capabilities
a staff session would hold only after step-up admin renewal — UIs must show
those actions instead of hiding them.
"""

from typing import List, Optional, get_type_hints

from inferencesh.types import (
    CPUScore,
    HostCPU,
    SystemInfo,
    TeamCapability,
    TeamViewDTO,
)


def test_system_info_host_cpu_is_optional_nested_telemetry():
    hints = get_type_hints(SystemInfo)
    assert hints["host_cpu"] == Optional[HostCPU]


def test_host_cpu_exposes_sysfs_and_benchmark_fields():
    hints = get_type_hints(HostCPU)
    assert set(hints) >= {
        "governor",
        "driver",
        "boost",
        "cur_mhz",
        "max_mhz",
        "smt",
        "threads_per_core",
        "hugepages_2m_total",
        "hugepages_2m_free",
        "thp",
        "kvm",
        "cpu_score",
    }
    assert hints["governor"] is str
    assert hints["boost"] == Optional[bool]
    assert hints["smt"] == Optional[bool]
    assert hints["cur_mhz"] is float
    assert hints["cpu_score"] == Optional[CPUScore]


def test_cpu_score_benchmark_shape():
    hints = get_type_hints(CPUScore)
    assert hints["single_ops_per_sec"] is float
    assert hints["all_ops_per_sec"] is float
    assert hints["threads"] is int

    score: CPUScore = {
        "single_ops_per_sec": 1.25e6,
        "all_ops_per_sec": 8.0e6,
        "threads": 8,
    }
    assert score["threads"] == 8


def test_system_info_accepts_host_cpu_snapshot():
    payload: SystemInfo = {
        "hostname": "gpu-node",
        "host_cpu": {
            "governor": "performance",
            "driver": "intel_pstate",
            "boost": True,
            "cur_mhz": 3200.0,
            "max_mhz": 5000.0,
            "smt": True,
            "threads_per_core": 2,
            "hugepages_2m_total": 512,
            "hugepages_2m_free": 480,
            "thp": "madvise",
            "kvm": True,
            "cpu_score": {
                "single_ops_per_sec": 2e6,
                "all_ops_per_sec": 12e6,
                "threads": 16,
            },
        },
    }
    host = payload["host_cpu"]
    assert host is not None
    assert host["thp"] == "madvise"
    assert host["cpu_score"]["threads"] == 16


def test_team_view_needs_admin_access_lists_capabilities():
    hints = get_type_hints(TeamViewDTO)
    assert hints["can"] == List[TeamCapability]
    assert hints["needs_admin_access"] == List[TeamCapability]


def test_team_view_separates_active_and_admin_renewable_capabilities():
    """Capabilities in needs_admin_access must not duplicate granted ``can``."""
    view: TeamViewDTO = {
        "team_id": "team_1",
        "can": [TeamCapability.VIEW_MEMBERS, TeamCapability.CREATE_KEYS],
        "needs_admin_access": [
            TeamCapability.MANAGE_MEMBERS,
            TeamCapability.MANAGE_KEYS,
        ],
    }
    granted = set(view["can"])
    step_up = set(view["needs_admin_access"])
    assert granted.isdisjoint(step_up)
    assert TeamCapability.MANAGE_KEYS in step_up
