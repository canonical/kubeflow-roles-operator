# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

from lightkube import Client
from lightkube.resources.rbac_authorization_v1 import ClusterRole
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


async def test_clusterroles_created():
    """Ensures ClusterRoles were successfully created."""

    lightkube_client = Client()

    clusterroles = []
    clusterrole_names = [
        "kubeflow-admin",
        "kubeflow-edit",
        "kubeflow-view",
        "kubeflow-kubernetes-admin",
        "kubeflow-kubernetes-edit",
        "kubeflow-kubernetes-view",
    ]

    for clusterrole_name in clusterrole_names:
        clusterroles.append(lightkube_client.get(ClusterRole, name=clusterrole_name))

    created_rules = {c.metadata.name: c.rules for c in clusterroles}

    expected = yaml.safe_load_all(Path("src/manifests/kubeflow-roles.yaml").read_text())
    expected_rules = {e["metadata"]["name"]: e["rules"] for e in expected}

    assert list(created_rules.keys()) == list(expected_rules.keys())
