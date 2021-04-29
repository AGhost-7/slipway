from shutil import copyfile
from os import makedirs, path
from slipway.configuration import Configuration


def test_configuration_none(tmp_path):
    configuration = Configuration({"HOME": tmp_path})
    configuration.load()


def test_configuration(tmp_path):
    makedirs(path.join(tmp_path, ".config"))
    copyfile(
        "./test/fixtures/configuration.yaml",
        path.join(tmp_path, ".config/slipway.yaml"),
    )
    configuration = Configuration({"HOME": tmp_path})
    configuration.load()
    assert configuration.alias["mini"]["image"] == "busybox"
    assert configuration.pull_daily
    assert configuration.pull
    assert not configuration.mount_docker
    assert "FORWARD" in configuration.environment
    assert "STATIC=1" in configuration.environment
