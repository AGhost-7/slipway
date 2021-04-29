from .util import create_client
from slipway.volumes import Volumes
from slipway.image import Image

client = create_client()


class FakeArgs(object):
    def __init__(self, image):
        self.image = image
        self.runtime = client.runtime


def test_volumes_init(image_fixture):
    try:
        client.remove_volume("slipway_image_fixture_test_volume")
    except:
        pass
    args = FakeArgs(image_fixture)
    image = Image(client, args)
    volumes = Volumes(client, args, image)
    volumes.initialize()
    assert "slipway_image_fixture_test_volume" in client.list_volume_names()


def test_volumes_purge(image_fixture):
    try:
        client.remove_volume("slipway_image_fixture_test_volume")
    except:
        pass
    args = FakeArgs(image_fixture)
    image = Image(client, args)
    volumes = Volumes(client, args, image)
    client.create_volume("slipway_image_fixture_test_volume")
    volumes.purge()
    assert "slipway_image_fixture_test_volume" not in client.list_volume_names()
