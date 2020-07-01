
from docker.errors import ImageNotFound
import docker
import subprocess


class DockerClient(object):
    def __init__(self):
        self.client = docker.from_env()

    def list_volume_names(self):
        return map(lambda volume: volume.name, self.client.volumes.list())

    def create_volume(self, name):
        self.client.volumes.create(name)

    def remove_volume(self, name):
        self.client.volumes.get(name).remove()

    def pull_image(self, name):
        subprocess.run(['docker', 'pull', name])

    def image_exists(self, name):
        try:
            self.client.images.get(name)
            return True
        except ImageNotFound:
            return False

    def inspect_image(self, name):
        return self.client.images.get(name).attrs
