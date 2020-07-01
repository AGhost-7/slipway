from slipway.container import Container
from test.util import build_image
import docker
import docker.errors
from subprocess import Popen, TimeoutExpired
import pty
import os
from slipway.client import DockerClient


class FakeArgs(object):
    def __init__(self, workspace):
        self.image = 'image-fixture'
        self.volume = []
        self.environment = []
        self.workspace = workspace
        self.mount_docker = False
        self.runtime = 'docker'


def create_container(tmp_path):
    build_image()
    workspace = tmp_path / 'workspace'
    args = FakeArgs(str(workspace))
    docker_client = docker.from_env()
    client = DockerClient()
    try:
        container = docker_client.containers.get('slipway_image_fixture')
        container.kill()
    except docker.errors.NotFound:
        pass
    master_fd, slave_fd = pty.openpty()
    process = Popen(
        Container(client, args)._run_arguments(),
        preexec_fn=os.setsid,
        stdout=slave_fd,
        stderr=slave_fd,
        stdin=slave_fd
        )
    try:
        process.wait(timeout=2)
        assert process.returncode is None
    except TimeoutExpired:
        pass
    return docker_client.containers.get('slipway_image_fixture')


def test_run(tmp_path):
    container = create_container(tmp_path)
    code, output = container.exec_run('ps aux')
    assert code == 0
    assert 'tmux' in str(output)
    container.kill()


def test_entrypoint(tmp_path):
    container = create_container(tmp_path)
    code, output = container.exec_run('stat -c %U /test-volume')
    assert code == 0
    assert 'foobar' in str(output)
    container.kill()
