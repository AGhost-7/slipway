from test.util import build_image
from slipway.image import Image
from docker.errors import ImageNotFound
import docker

client = docker.from_env()


class FakeArgs(object):
    def __init__(self, image):
        self.image = image


def test_initialize():
    try:
        client.images.get('busybox')
        client.images.remove('busybox')
    except ImageNotFound:
        pass
    args = FakeArgs('busybox')
    image = Image(client, args)
    image.initialize()
    assert client.images.get('busybox') is not None


def test_volumes():
    build_image()
    image = Image(client, FakeArgs('image-fixture'))
    assert len(image.volumes) == 1
    assert image.volumes[0] == '/test-volume'


def test_entrypoint():
    build_image()
    image = Image(client, FakeArgs('image-fixture'))
    assert image.entrypoint == ['/entrypoint.sh']


def test_user():
    build_image()
    image = Image(client, FakeArgs('image-fixture'))
    assert image.user == 'foobar'


def test_home():
    build_image()
    image = Image(client, FakeArgs('image-fixture'))
    assert image.home == '/home/foobar'
