#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from functools import wraps
from glob import glob
from pathlib import Path

from lightkube import ApiError, Client, codecs
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus


def only_leader(handler):
    """Ensures method only runs if unit is a leader."""

    @wraps(handler)
    def wrapper(self, event):
        if not self.unit.is_leader():
            self.model.unit.status = WaitingStatus("Waiting for leadership")
        else:
            handler(self, event)

    return wrapper


class Operator(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)

        for event in [
            self.on.install,
            self.on.upgrade_charm,
            self.on.config_changed,
        ]:
            self.framework.observe(event, self.main)

        self.framework.observe(self.on.remove, self.remove)

    @only_leader
    def main(self, _):
        self.model.unit.status = MaintenanceStatus("Calculating manifests")

        try:
            manifests = self.get_manifests()
        except Exception as err:
            self.model.unit.status = BlockedStatus(str(err))
            return

        self.model.unit.status = MaintenanceStatus("Applying manifests")
        errors = self.set_manifests(manifests)

        if errors:
            self.model.unit.status = BlockedStatus(
                f"There were {len(errors)} errors while applying manifests. "
                f"Do you need to run `juju trust {self.model.app.name}`?"
            )
            log = logging.getLogger(__name__)
            for error in errors:
                log.error(error)
        else:
            self.model.unit.status = ActiveStatus()

    @only_leader
    def remove(self, _):
        """Remove charm."""

        self.model.unit.status = MaintenanceStatus("Calculating manifests")

        manifests = self.get_manifests()

        self.model.unit.status = MaintenanceStatus("Removing manifests")

        self.remove_manifests(manifests)

    def get_manifests(self):
        return [
            obj
            for path in self._get_manifest_files()
            for obj in codecs.load_all_yaml(Path(path).read_text(), context={})
        ]

    def remove_manifests(self, manifests):
        client = Client()

        for manifest in manifests:
            try:
                client.delete(type(manifest), manifest.metadata.name)
            except ApiError as err:
                if err.status.code in (401, 403):
                    print("Error deleting object: " "https://bugs.launchpad.net/bugs/1941655")
                else:
                    raise

    @staticmethod
    def _get_manifest_files():
        return glob("src/manifests/*.yaml")

    @staticmethod
    def set_manifests(manifests):
        client = Client()
        errors = []

        for manifest in manifests:
            try:
                client.create(manifest)
            except ApiError as err:
                if err.status.code == 409:
                    client.patch(type(manifest), manifest.metadata.name, manifest)
                else:
                    errors.append(err)

        return errors


if __name__ == "__main__":
    main(Operator)
