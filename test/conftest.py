from pathlib import Path
import pytest
import subprocess
import docker

from .util import test_runtime


@pytest.fixture(scope="module")
def image_fixture():
    context_path = str(Path(__file__).parent / "fixtures")
    tag = "image-fixture"
    if test_runtime() == "docker":
        client = docker.from_env()
        client.images.build(tag=tag, path=context_path, pull=True)
    else:
        subprocess.run(["podman", "build", "-t", "--pull", tag, context_path])
    return tag
