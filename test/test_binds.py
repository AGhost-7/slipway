from slipway.binds import Binds
from slipway.image import Image
from slipway.client import DockerClient
from .util import create_client

client = create_client()


class FakeArgs(object):
    def __init__(self, volume, workspace, cache_directory):
        self.image = "image-fixture"
        self.volume = volume
        self.workspace = workspace
        self.runtime = client.runtime
        self.cache_directory = cache_directory


def test_initialize(tmp_path, image_fixture):
    volume = tmp_path / "initialize"
    cache_directory = tmp_path / "cache"
    assert not volume.exists()
    args = FakeArgs(
        [str(volume) + ":/initialize"],
        str(tmp_path / "workspace"),
        str(cache_directory),
    )
    image = Image(client, args)
    binds = Binds(client, args, image)
    binds.initialize()
    assert volume.exists()


def test_list(tmp_path, image_fixture):
    file_bind = tmp_path / "file.txt"
    file_bind.touch()
    dir_bind = tmp_path / "directory"
    dir_bind.mkdir()
    host_workspace = tmp_path / "some-workspace"
    host_workspace.mkdir()
    cache_directory = tmp_path / "cache"
    args = FakeArgs(
        [str(file_bind) + ":/file", str(dir_bind) + ":/dir"],
        str(host_workspace),
        str(cache_directory),
    )
    image = Image(client, args)
    binds = Binds(client, args, image)
    matches = [
        bind for bind in binds.list() if bind.container_path in ("/file", "/dir")
    ]
    assert len(matches) == 2

    for bind in matches:
        if bind.container_path == "/file":
            assert bind.type == "f"
        else:
            assert bind.type == "d"

    workspace = [
        bind
        for bind in binds.list()
        if bind.container_path == "/home/foobar/some-workspace"
    ]
    assert len(workspace) == 1
