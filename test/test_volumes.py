import docker
from slipway.client import DockerClient
from slipway.volumes import Volumes
from slipway.image import Image
from test.util import build_image

docker_client = docker.from_env()
client = DockerClient()
image_name = build_image()


class FakeArgs(object):
    def __init__(self, image):
        self.image = image
        self.runtime = 'docker'


def test_volumes_init():
    for volume in docker_client.volumes.list():
        if volume.name == 'slipway_image_fixture_test_volume':
            volume.remove()
    args = FakeArgs('image-fixture')
    image = Image(client, args)
    volumes = Volumes(client, args, image)
    volumes.initialize()
    matches = [
        volume
        for volume in docker_client.volumes.list()
        if volume.name == 'slipway_image_fixture_test_volume'
    ]
    assert len(matches) == 1
    matches[0].remove()


def test_volumes_purge():
    args = FakeArgs('image-fixture')
    image = Image(client, args)
    volumes = Volumes(client, args, image)
    docker_client.volumes.create('slipway_image_fixture_test_volume')
    volumes.purge()
    for volume in docker_client.volumes.list():
        assert volume.name != 'slipway_image_fixture_test_volume'
