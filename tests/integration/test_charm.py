# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

import yaml


async def test_build_and_deploy(ops_test):
    """Build, deploy and ensure application is in ActiveStatus."""

    built_charm = await ops_test.build_charm(".")
    await ops_test.model.deploy(built_charm, trust=True)
    await ops_test.model.wait_for_idle(
        status="active",
        raise_on_blocked=True,
        timeout=60,
    )
    assert (
        ops_test.model.applications["kubeflow-roles"].units[0].workload_status
        == "active"
    )


async def test_clusterroles_created(ops_test):
    """Ensures ClusterRoles were successfully created."""

    names = [
        "kubeflow-admin",
        "kubeflow-edit",
        "kubeflow-view",
        "kubeflow-kubernetes-admin",
        "kubeflow-kubernetes-edit",
        "kubeflow-kubernetes-view",
    ]

    result = await ops_test.run(
        "kubectl",
        "get",
        "clusterroles",
        "-oyaml",
        *names,
        check=True,
    )
    created = yaml.safe_load(result[1])["items"]
    created = {c["metadata"]["name"]: c["rules"] for c in created}

    expected = yaml.safe_load_all(Path("src/manifests/kubeflow-roles.yaml").read_text())
    expected = {e["metadata"]["name"]: e["rules"] for e in expected}

    assert list(created.keys()) == list(expected.keys())

    for name, rules in expected.items():
        assert rules <= created[name]
