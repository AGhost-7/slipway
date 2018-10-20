
import docker
from slipway.binds import Binds
from slipway.image import Image

client = docker.from_env()


class FakeArgs(object):
    def __init__(self, volume):
        self.image = 'image-fixture'
        self.volume = volume


def test_initialize(tmp_path):
    volume = tmp_path / 'initialize'
    assert not volume.exists()
    args = FakeArgs([str(volume) + ':/initialize'])
    image = Image(client, args)
    binds = Binds(client, args, image)
    binds.initialize()
    assert volume.exists()


def test_list(tmp_path):
    file_bind = tmp_path / 'file.txt'
    file_bind.touch()
    dir_bind = tmp_path / 'directory'
    dir_bind.mkdir()
    args = FakeArgs(
        [str(file_bind) + ':/file', str(dir_bind) + ':/dir'])
    image = Image(client, args)
    binds = Binds(client, args, image)
    matches = [
        bind for bind in binds.list()
        if bind.container_path in ('/file', '/dir')
    ]
    assert len(matches) == 2

    for bind in matches:
        if bind.container_path == '/file':
            assert bind.type == 'f'
        else:
            assert bind.type == 'd'
