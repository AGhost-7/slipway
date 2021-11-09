import pytest
from slipway.container import Container
from subprocess import Popen, TimeoutExpired
import pty
import os
from .util import create_client, test_runtime

client = create_client()


class FakeArgs(object):
    def __init__(self, workspace, runtime_dir, cache_directory, logs_directory):
        self.image = "image-fixture"
        self.volume = []
        self.environment = []
        self.workspace = workspace
        self.mount_docker = False
        self.runtime = client.runtime
        self.runtime_dir = runtime_dir
        self.log_directory = logs_directory
        self.cache_directory = cache_directory
        self.network = "slirp4netns"
        self.device = []


@pytest.fixture
def container_fixture(tmp_path, image_fixture):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "slipway").mkdir()
    cache_directory = tmp_path / "cache_directory"
    cache_directory.mkdir(parents=True)
    logs_directory = tmp_path / "logs"
    logs_directory.mkdir(parents=True)
    args = FakeArgs(
        workspace=str(workspace),
        runtime_dir=str(runtime_dir),
        cache_directory=str(cache_directory),
        logs_directory=logs_directory,
    )
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


@pytest.mark.skipif(
    test_runtime() == "docker", reason="uidmap doesnt work on rootless docker"
)
def test_permission(container_fixture):
    output = client.exec_container(
        container_fixture, ["stat", "-c", "%U", "/test-volume"]
    )
    assert "foobar" in output


def test_sudo(container_fixture):
    client.exec_container(container_fixture, ["sudo", "apt-get", "update"])


def test_strace(container_fixture):
    client.exec_container(container_fixture, ["sudo", "strace", "ls"])


def test_nmap(container_fixture):
    output = client.exec_container(
        container_fixture, ["sudo", "nmap", "-p", "81", "jenkins.jonathan-boudreau.com"]
    )
    assert "closed" in output
