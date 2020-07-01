
from docker.errors import ImageNotFound
import docker
import subprocess


class DockerClient(object):
    def __init__(self):
        self._client = docker.from_env()

    def list_volume_names(self):
        return map(lambda volume: volume.name, self._client.volumes.list())

    def create_volume(self, name):
        self.client.volumes.create(name)

    def pull_image(self, name):
        subprocess.run(['docker', 'pull', name])

    def image_exists(self, name):
        try:
            self.client.image.get(name)
            return True
        except ImageNotFound:
            return False

    def inspect_image(self, name):
        return self._client.images.get(name).attrs
