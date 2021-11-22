# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest


@pytest.mark.abort_on_fail
@pytest.mark.skip(reason="Not published to store yet")
async def test_build_and_deploy(ops_test):
    local_charm = await ops_test.build_charm(".")
    await ops_test.model.deploy("ch:kubeflow-roles", trust=True)
    await ops_test.model.wait_for_idle(status="active")

    await ops_test.juju("upgrade-charm", "--path", local_charm)
    await ops_test.model.wait_for_idle(status="active")

    for app in ops_test.model.applications.values():
        for unit in app.units:
            assert unit.workload_status == "active"
