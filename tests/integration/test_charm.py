# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

import pytest
import yaml


@pytest.fixture(scope="module")
async def charm(ops_test):
    """Fixture for building, deploying, then removing the charm."""

    built_charm = await ops_test.build_charm(".")
    await ops_test.model.deploy(built_charm, trust=True)
    await ops_test.model.wait_for_idle(status="active")

    yield

    for app in ops_test.model.applications.values():
        await app.remove()

    await ops_test.model.block_until(
        lambda: not ops_test.model.applications,
        timeout=600,
    )
    assert ops_test.model.applications == {}


async def test_active(charm, ops_test):
    """Ensures all applications are in ActiveStatus."""

    for app in ops_test.model.applications.values():
        for unit in app.units:
            assert unit.workload_status == "active"


async def test_clusterroles_created(charm, ops_test):
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
