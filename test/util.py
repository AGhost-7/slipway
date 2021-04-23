import subprocess
import docker
from docker.errors import ImageNotFound, NotFound
from os import path, environ
from slipway.client import PodmanClient, DockerClient


def test_runtime():
    return environ.get("TEST_RUNTIME", "podman")


class TestDockerClient(DockerClient):
    def remove_image(self, tag):
        try:
            self.client.images.get(tag)
            self.client.images.remove(tag)
        except ImageNotFound:
            pass

    def force_kill_container(self):
        try:
            container = self.client.containers.get('slipway_image_fixture')
            container.kill()
        except NotFound:
            pass


class TestPodmanClient(PodmanClient):

    def remove_image(self, tag):
        subprocess.check_output([
            "podman", "rmi", tag
        ])

    def force_kill_container(self, container):
        pass


def create_client():
    if test_runtime() == "docker":
        return TestDockerClient()
    else:
        return TestPodmanClient()
