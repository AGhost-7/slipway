from os import path
from datetime import datetime, timedelta
from test.util import build_image
from slipway.image import Image
from docker.errors import ImageNotFound
import docker

client = docker.from_env()


class FakeArgs(object):
    def __init__(self, image, data_directory):
        self.image = image
        self.data_directory = data_directory
        self.pull = False
        self.pull_daily = False


def test_initialize(tmp_path):
    try:
        client.images.get('busybox')
        client.images.remove('busybox')
    except ImageNotFound:
        pass
    args = FakeArgs('busybox', tmp_path)
    image = Image(client, args)
    image.initialize()
    assert client.images.get('busybox') is not None


def test_initialize_daily(tmp_path):
    args = FakeArgs('busybox', tmp_path)
    args.pull = True
    args.pull_daily = True
    image = Image(client, args)
    image.initialize()
    assert image._pulled_today()


def test_initialize_daily_stale(tmp_path):
    args = FakeArgs('busybox', tmp_path)
    args.pull = True
    args.pull_daily = True
    image = Image(client, args)
    image.initialize()
    last_pull = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    with open(path.join(tmp_path, 'last_stale_check/busybox'), 'w') as file_descriptor:
        file_descriptor.write(last_pull)
    assert not image._pulled_today()


def test_volumes(tmp_path):
    build_image()
    image = Image(client, FakeArgs('image-fixture', tmp_path))
    assert len(image.volumes) == 1
    assert image.volumes[0] == '/test-volume'


def test_entrypoint(tmp_path):
    build_image()
    image = Image(client, FakeArgs('image-fixture', tmp_path))
    assert image.entrypoint == ['/entrypoint.sh']


def test_user(tmp_path):
    build_image()
    image = Image(client, FakeArgs('image-fixture', tmp_path))
    assert image.user == 'foobar'


def test_home(tmp_path):
    build_image()
    image = Image(client, FakeArgs('image-fixture', tmp_path))
    assert image.home == '/home/foobar'
