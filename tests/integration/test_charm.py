# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path

import pytest
import yaml
from charmed_kubeflow_chisme.testing import (
    assert_security_context,
    generate_container_securitycontext_map,
    get_pod_names,
)
from lightkube import Client
from lightkube.resources.rbac_authorization_v1 import ClusterRole
from pytest_operator.plugin import OpsTest

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
CHARM_NAME = METADATA["name"]
CONTAINERS_SECURITY_CONTEXT_MAP = generate_container_securitycontext_map(METADATA)


@pytest.fixture(scope="session")
def lightkube_client() -> Client:
    """Returns lightkube Kubernetes client"""
    client = Client(field_manager=f"{CHARM_NAME}")
    return client


async def test_build_and_deploy(ops_test: OpsTest):
    """Build, deploy and ensure application is in ActiveStatus."""

    built_charm = await ops_test.build_charm(".")
    await ops_test.model.deploy(built_charm, trust=True)
    await ops_test.model.wait_for_idle(
        status="active",
        raise_on_blocked=True,
        timeout=60,
    )
    assert ops_test.model.applications[CHARM_NAME].units[0].workload_status == "active"


async def test_clusterroles_created(ops_test: OpsTest, lightkube_client: Client):
    """Ensures ClusterRoles were successfully created."""

    clusterroles = []
    clusterrole_names = [
        "kubeflow-admin",
        "kubeflow-edit",
        "kubeflow-view",
        "kubeflow-kubernetes-admin",
        "kubeflow-kubernetes-edit",
        "kubeflow-kubernetes-view",
        "kubeflow-tokens-edit",
    ]

    for clusterrole_name in clusterrole_names:
        clusterroles.append(lightkube_client.get(ClusterRole, name=clusterrole_name))

    created_rules = {c.metadata.name: c.rules for c in clusterroles}

    expected = yaml.safe_load_all(Path("src/manifests/kubeflow-roles.yaml").read_text())
    expected_rules = {e["metadata"]["name"]: e["rules"] for e in expected}

    assert list(created_rules.keys()) == list(expected_rules.keys())


@pytest.mark.parametrize("container_name", list(CONTAINERS_SECURITY_CONTEXT_MAP.keys()))
async def test_container_security_context(
    ops_test: OpsTest,
    lightkube_client: Client,
    container_name: str,
):
    """Test container security context is correctly set.

    Verify that container spec defines the security context with correct
    user ID and group ID.
    """
    pod_name = get_pod_names(ops_test.model.name, CHARM_NAME)[0]
    assert_security_context(
        lightkube_client,
        pod_name,
        container_name,
        CONTAINERS_SECURITY_CONTEXT_MAP,
        ops_test.model.name,
    )
