from os import path
from .util import snake_case
from typing import List


class Volume(object):
    def __init__(self, client, name, path):
        self.name = name
        self.path = path
        self._client = client

    @property
    def host_path(self) -> str:
        return self._client.volume_host_path(self.name)


class Volumes(object):
    def __init__(self, client, args, image):
        self.client = client
        self.args = args
        self.image = image

    def list(self) -> List[Volume]:
        """
        Lists all volumes
        """
        volumes = []
        for image_volume in self.image.volumes:
            base = "slipway_" + snake_case(self.image.name)
            volumes.append(
                Volume(
                    self.client,
                    base + "_" + snake_case(image_volume),
                    image_volume,
                ),
            )
        if self.args.unshare_workspace:
            workspace_base = path.basename(self.args.workspace)
            workspace_path = path.join(self.image.home, workspace_base)
            volumes.append(
                Volume(
                    self.client,
                    "slipway_workspace",
                    workspace_path,
                )
            )
        return volumes

    def purge(self) -> None:
        """
        Clears all volumes tied to the given arguments
        """
        current_volumes = self.client.list_volume_names()
        for volume in self.list():
            found = None
            for volume_name in current_volumes:
                if volume.name == volume_name:
                    found = volume_name
            if found is not None:
                self.client.remove_volume(found)

    def initialize(self) -> None:
        """
        Checks if the required volume are present and creates them if missing.
        """
        current_volume_names = self.client.list_volume_names()
        for volume in self.list():
            exist = False
            for volume_name in current_volume_names:
                if volume.name == volume_name:
                    exist = True
            if not exist:
                self.client.create_volume(volume.name)
