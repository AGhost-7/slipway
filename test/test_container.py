import pytest
from slipway.container import Container
from slipway.argument_parser import parse_args
from slipway.configuration import Configuration
from subprocess import Popen, TimeoutExpired
import pty
import os
from .util import create_client, test_runtime

client = create_client()


@pytest.fixture
def container_fixture(tmp_path, image_fixture):
    home = tmp_path / "home"
    workspace = home / "workspace"
    workspace.mkdir(parents=True)
    runtime_dir = home / "runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "slipway").mkdir()
    (home / ".local" / "share").mkdir(parents=True)
    (home / ".cache").mkdir(parents=True)

    configuration = Configuration(
        {
            "HOME": home,
            "XDG_RUNTIME_DIR": runtime_dir,
        }
    )
    args = parse_args(
        configuration, ["start", "--network", "slirp4netns", image_fixture]
    )

    client = create_client()
    client.force_kill_container("slipway_image_fixture")
    master_fd, slave_fd = pty.openpty()

    container = Container(client, args)
    run_args = Container(client, args)._run_arguments()

    process = Popen(
        run_args, preexec_fn=os.setsid, stdout=slave_fd, stderr=slave_fd, stdin=slave_fd
    )
    try:
        process.wait(timeout=2)
        process.communicate()
        print(process.stdout, process.stderr)
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
