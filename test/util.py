import docker
from os import path


def build_image():
    client = docker.from_env()
    current_dir = path.dirname(__file__)
    client.images.build(
        tag='image-fixture', path=path.join(current_dir, 'fixtures'))
