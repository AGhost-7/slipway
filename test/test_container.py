import pytest
from slipway.container import Container
import docker
import docker.errors
from subprocess import Popen, TimeoutExpired
import pty
import os
from .util import create_client

client = create_client()


class FakeArgs(object):
    def __init__(self, workspace, runtime_dir, cache_directory):
        self.image = 'image-fixture'
        self.volume = []
        self.environment = []
        self.workspace = workspace
        self.mount_docker = False
        self.runtime = client.runtime
        self.runtime_dir = runtime_dir
        self.cache_directory = cache_directory
        self.network = 'host'


def create_container(tmp_path):
    workspace = tmp_path / 'workspace'
    runtime_dir = tmp_path / 'runtime'
    cache_directory = tmp_path / 'cache_directory'
    args = FakeArgs(str(workspace), str(runtime_dir), str(cache_directory))
    docker_client = docker.from_env()
    client = create_client()
    client.force_kill_container("slipway_image_fixture")
    master_fd, slave_fd = pty.openpty()
    args = Container(client, args)._run_arguments()
    process = Popen(
        args,
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


def test_run(tmp_path, image_fixture):
    container = create_container(tmp_path)
    code, output = container.exec_run('ps aux')
    assert code == 0
    assert 'tmux' in str(output)
    container.kill()


def test_entrypoint(tmp_path, image_fixture):
    container = create_container(tmp_path)
    code, output = container.exec_run('stat -c %U /test-volume')
    assert code == 0
    assert 'foobar' in str(output)
    container.kill()


@pytest.mark.skip
def test_uidmap():
    pass
