import tarfile
from os import path
from io import BytesIO
from docker.errors import ImageNotFound
import docker
import subprocess
from typing import Optional
import sys
import subprocess
import json


class DockerClient(object):
    def __init__(self):
        self.client = docker.from_env()
        self.runtime = "docker"

    def list_volume_names(self):
        return map(lambda volume: volume.name, self.client.volumes.list())

    def volume_host_path(self, name):
        if sys.platform != "linux":
            # there is no host storage for volumes on docker for mac due to
            # it being virtualized
            return None
        volume = self.client.volumes.get(name)
        return volume.attrs["Mountpoint"]

    def create_volume(self, name):
        self.client.volumes.create(name)

    def remove_volume(self, name):
        self.client.volumes.get(name).remove()

    def pull_image(self, name):
        subprocess.run(["docker", "pull", name])


    def inspect_image(self, name):
        result = subprocess.run(
            ["docker", "image", "inspect", "--format", "{{json .}}", name],
            capture_output=True,
        )
        images = json.loads(str(result.stdout, "utf8").strip())
        if isinstance(images, list):
            return images[0]

        return images
    def image_exists(self, name):
        result = subprocess.run(
            ["docker", "image", "inspect", name], capture_output=True
        )
        return result.returncode == 0

    def list_all_containers(self):
        return [container.name for container in self.client.containers.list(all=True)]

    def has_uidmap(self):
        return False

    def is_rootless(self):
        return "name=rootless" in self.client.info()["SecurityOptions"]

    def image_file(self, name: str, file_path: str) -> Optional[str]:
        result = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "/bin/cat", name, file_path],
            capture_output=True,
        )

        return str(result.stdout, "utf-8")
