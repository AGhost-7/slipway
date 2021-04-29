from os import path
from datetime import datetime, timedelta
from slipway.image import Image
from .util import create_client

client = create_client()


class FakeArgs(object):
    def __init__(self, image, tmp_path):
        self.image = image
        self.data_directory = tmp_path / "data"
        self.cache_directory = tmp_path / "cache"
        self.pull = False
        self.pull_daily = False
        self.runtime = client.runtime


def test_initialize(tmp_path):
    client.remove_image("busybox")
    args = FakeArgs("busybox", tmp_path)
    image = Image(client, args)
    image.initialize()
    client.inspect_image("busybox")


def test_initialize_daily(tmp_path):
    args = FakeArgs("busybox", tmp_path)
    args.pull = True
    args.pull_daily = True
    image = Image(client, args)
    image.initialize()
    assert image._pulled_today()


def test_initialize_daily_stale(tmp_path):
    args = FakeArgs("busybox", tmp_path)
    args.pull = True
    args.pull_daily = True
    image = Image(client, args)
    image.initialize()
    last_pull = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    stale_path = path.join(args.data_directory, "last_stale_check/busybox")
    with open(stale_path, "w") as file_descriptor:
        file_descriptor.write(last_pull)
    assert not image._pulled_today()


def test_volumes(tmp_path, image_fixture):
    image = Image(client, FakeArgs(image_fixture, tmp_path))
    assert len(image.volumes) == 1
    assert image.volumes[0] == "/test-volume"


def test_entrypoint(tmp_path, image_fixture):
    image = Image(client, FakeArgs(image_fixture, tmp_path))
    assert image.entrypoint == ["/entrypoint.sh"]


def test_user(tmp_path, image_fixture):
    image = Image(client, FakeArgs(image_fixture, tmp_path))
    assert image.user == "foobar"


def test_user_id(tmp_path, image_fixture):
    image = Image(client, FakeArgs(image_fixture, tmp_path))
    assert image.user_id == 1001


def test_home(tmp_path, image_fixture):
    image = Image(client, FakeArgs(image_fixture, tmp_path))
    assert image.home == "/home/foobar"
