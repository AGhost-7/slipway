from .util import create_client

client = create_client()


def test_rootless():
    assert client.is_rootless()
