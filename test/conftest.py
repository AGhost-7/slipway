from pathlib import Path
import pytest
import subprocess

from .util import test_runtime


@pytest.fixture(scope="module")
def image_fixture():
    context_path = str(Path(__file__).parent / "fixtures")
    tag = "image-fixture"
    if test_runtime() == "docker":
        client = docker.from_env()
        client.images.build(tag=tag, path=context_path)
    else:
        subprocess.run(["podman", "build", "-t", tag, context_path])
    return tag
