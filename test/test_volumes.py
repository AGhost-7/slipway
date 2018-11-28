import docker
from slipway.volumes import Volumes
from slipway.image import Image
from test.util import build_image

client = docker.from_env()
image_name = build_image()


class FakeArgs(object):
    def __init__(self, image):
        self.image = image


def test_volumes_init():
    for volume in client.volumes.list():
        if volume.name == 'slipway_image_fixture_test_volume':
            volume.remove()
    args = FakeArgs('image-fixture')
    image = Image(client, args)
    volumes = Volumes(client, args, image)
    volumes.initialize()
    matches = [
        volume
        for volume in client.volumes.list()
        if volume.name == 'slipway_image_fixture_test_volume'
    ]
    assert len(matches) == 1
    matches[0].remove()


def test_volumes_purge():
    args = FakeArgs('image-fixture')
    image = Image(client, args)
    volumes = Volumes(client, args, image)
    client.volumes.create('slipway_image_fixture_test_volume')
    volumes.purge()
    for volume in client.volumes.list():
        assert volume.name != 'slipway_image_fixture_test_volume'
