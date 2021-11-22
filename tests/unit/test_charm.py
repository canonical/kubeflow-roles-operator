# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from pathlib import Path
from unittest.mock import call, patch

import pytest
from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness

from charm import Operator


@pytest.fixture
def harness():
    return Harness(Operator)


def test_not_leader(harness):
    harness.begin_with_initial_hooks()
    assert isinstance(harness.charm.model.unit.status, WaitingStatus)


@patch("charm.codecs")
@patch("charm.Client")
def test_main_no_relation(mock_client, mock_codecs, harness):
    mock_codecs.load_all_yaml.return_value = [42]

    harness.set_leader(True)
    harness.begin_with_initial_hooks()

    # Ensure that manifests were loaded
    manifests = [Path("src/manifests/kubeflow-roles.yaml").read_text()]
    expected = [call(m, context={}) for m in manifests] * 2

    assert mock_codecs.load_all_yaml.call_args_list == expected

    # And that they were created
    assert mock_client().create.call_args_list == [call(42)] * 2

    # And everything worked
    assert isinstance(harness.charm.model.unit.status, ActiveStatus)
