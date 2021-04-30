from typing import List
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

    def force_kill_container(self, container: str):
        try:
            self.client.containers.get(container).kill()
        except NotFound:
            pass

    def exec_container(self, container, command) -> str:
        container = self.client.containers.get(container)
        code, output = container.exec_run(command)
        assert code == 0
        return str(output, "utf-8")


class TestPodmanClient(PodmanClient):
    def remove_image(self, tag):
        subprocess.check_output(["podman", "rmi", tag])

    def force_kill_container(self, container):
        try:
            subprocess.check_output(["podman", "kill", container])
        except:
            pass

    def exec_container(self, container: str, command: List[str]) -> str:
        output = subprocess.check_output(["podman", "exec", container] + command)
        return str(output, "utf-8")


def create_client():
    if test_runtime() == "docker":
        return TestDockerClient()
    else:
        return TestPodmanClient()
