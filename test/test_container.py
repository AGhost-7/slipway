from slipway.container import Container
from test.util import build_image
import docker
import docker.errors
from subprocess import Popen, TimeoutExpired
import subprocess


class FakeArgs(object):
    def __init__(self):
        self.image = 'image-fixture'
        self.volume = []
        self.environment = []


def create_container():
    build_image()
    args = FakeArgs()
    client = docker.from_env()
    try:
        container = client.containers.get('slipway_image_fixture')
        container.kill()
    except docker.errors.NotFound:
        pass
    process = Popen(
        Container(client, args)._run_arguments(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    try:
        process.wait(timeout=2)
        assert process.returncode is None
    except TimeoutExpired:
        pass
    return client.containers.get('slipway_image_fixture')


def test_run():
    container = create_container()
    code, output = container.exec_run('ps aux')
    assert code == 0
    assert 'tmux' in str(output)
    container.kill()


def test_entrypoint():
    container = create_container()
    code, output = container.exec_run('stat -c %U /test-volume')
    assert code == 0
    assert 'foobar' in str(output)
    container.kill()
