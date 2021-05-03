import tarfile
from os import path
from io import BytesIO
from docker.errors import ImageNotFound
import docker
import subprocess
from typing import Optional


class DockerClient(object):
    def __init__(self):
        self.client = docker.from_env()
        self.runtime = "docker"

    def list_volume_names(self):
        return map(lambda volume: volume.name, self.client.volumes.list())

    def create_volume(self, name):
        self.client.volumes.create(name)

    def remove_volume(self, name):
        self.client.volumes.get(name).remove()

    def pull_image(self, name):
        subprocess.run(["docker", "pull", name])

    def image_exists(self, name):
        try:
            self.client.images.get(name)
            return True
        except ImageNotFound:
            return False

    def inspect_image(self, name):
        return self.client.images.get(name).attrs

    def list_all_containers(self):
        return [container.name for container in self.client.containers.list(all=True)]

    def has_uidmap(self):
        return False

    def is_rootless(self):
        return "name=rootless" in self.client.info()["SecurityOptions"]

    def image_file(self, name: str, file_path: str) -> Optional[str]:
        container = self.client.containers.create(name)
        try:
            chunks, stat = container.get_archive(file_path)
            aggregate = bytearray()
            for chunk in chunks:
                aggregate += chunk
            tar = tarfile.open(fileobj=BytesIO(aggregate))
            file_content = tar.extractfile(path.basename(file_path))

            return (
                file_content
                if file_content is None
                else str(file_content.read(), "utf-8")
            )
        finally:
            container.remove()
