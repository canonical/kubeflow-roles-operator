# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--charm-path",
        help="Path to pre-built charm file",
    )
