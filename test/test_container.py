import pytest
from slipway.container import Container
from subprocess import Popen, TimeoutExpired
import pty
import os
from .util import create_client

client = create_client()


class FakeArgs(object):
    def __init__(self, workspace, runtime_dir, cache_directory):
        self.image = "image-fixture"
        self.volume = []
        self.environment = []
        self.workspace = workspace
        self.mount_docker = False
        self.runtime = client.runtime
        self.runtime_dir = runtime_dir
        self.cache_directory = cache_directory
        self.network = "host"


@pytest.fixture
def container_fixture(tmp_path, image_fixture):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "slipway").mkdir()
    cache_directory = tmp_path / "cache_directory"
    cache_directory.mkdir(parents=True)
    args = FakeArgs(str(workspace), str(runtime_dir), str(cache_directory))
    client = create_client()
    client.force_kill_container("slipway_image_fixture")
    master_fd, slave_fd = pty.openpty()
    container = Container(client, args)
    args = Container(client, args)._run_arguments()

    process = Popen(
        args, preexec_fn=os.setsid, stdout=slave_fd, stderr=slave_fd, stdin=slave_fd
    )
    try:
        process.wait(timeout=2)
        process.communicate()
        assert process.returncode is None
    except TimeoutExpired:
        pass

    yield "slipway_image_fixture"

    client.force_kill_container("slipway_image_fixture")


def test_run(container_fixture):
    output = client.exec_container(container_fixture, ["ps", "aux"])
    assert "bash" in output


def test_permission(container_fixture):
    output = client.exec_container(
        container_fixture, ["stat", "-c", "%U", "/test-volume"]
    )
    assert "foobar" in output
