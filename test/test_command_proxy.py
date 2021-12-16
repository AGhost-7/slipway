import json
import shutil
from subprocess import run
from slipway.command_proxy import CommandProxy
from pytest import fixture
from os import environ, path
import os
import sys
import time
from .util import create_client
from pathlib import Path


@fixture
def command_proxy(tmp_path: Path):
    logs_directory = tmp_path / "logs"
    command_proxy = CommandProxy(tmp_path, logs_directory)

    fake_cli = tmp_path / "xdg-open"
    with open(fake_cli, "w+") as file:
        file.write(
            "#!/bin/sh\n"
            f"echo $@ > {tmp_path}/args.txt; echo $PWD > {tmp_path}/pwd.txt"
        )
    os.chmod(fake_cli, 0o700)

    sub_env = environ.copy()
    sub_env["PATH"] = f"{str(tmp_path)}:{sub_env['PATH']}"
    command_proxy.start_server(env=sub_env)

    yield command_proxy
    if command_proxy.is_server_running():
        command_proxy.stop_server()
        pass


def test_start_server(command_proxy: CommandProxy):
    command_proxy.start_server()
    assert command_proxy.is_server_running()


def test_server_calls_command_proxy(tmp_path: Path, command_proxy: CommandProxy):
    proxy_bin = tmp_path / "proxy"
    proxy_bin.mkdir()
    xdg_proxy = proxy_bin / "xdg-open"
    xdg_proxy.symlink_to(command_proxy.client_path)

    # server takes a bit of time to start up...
    time.sleep(1)
    assert command_proxy.is_server_running()

    result = run(
        [xdg_proxy, "https://jokes.jonathan-boudreau.com"],
        env={**environ, "SLIPWAY_RUNTIME_DIR": str(tmp_path / "slipway")},
    )

    assert result.returncode == 0

    with open(tmp_path / "args.txt") as file:
        content = file.read()
        assert content.strip() == "https://jokes.jonathan-boudreau.com"


def test_xdg_mapping(tmp_path: Path, command_proxy: CommandProxy, image_fixture: str):
    proxy_bin = tmp_path / "proxy"
    proxy_bin.mkdir()
    xdg_proxy = proxy_bin / "xdg-open"
    xdg_proxy.symlink_to(command_proxy.client_path)

    assert command_proxy.is_server_running()
    time.sleep(1)

    client = create_client()
    mapping_file = tmp_path / "slipway-mapping.json"
    with open(mapping_file, "w") as file:
        file.write(
            json.dumps(
                [
                    {"container": "/workspace", "host": os.getcwd()},
                ]
            )
        )
    result = run(
        [
            client.runtime,
            "run",
            "-ti",
            "--rm",
            "-v",
            f"{command_proxy.client_path}:/usr/bin/xdg-open",
            "-v",
            f"{tmp_path / 'slipway'}:/run/slipway",
            "-v",
            f"{os.getcwd()}:/workspace",
            "-v" f"{mapping_file}:/run/user/1000/slipway-mapping.json",
            "python:3",
            "bash",
            "-c",
            "cd /workspace && xdg-open ./README.md",
        ]
    )
    assert result.returncode == 0
    with open(tmp_path / "args.txt") as file:
        content = file.read()
        assert content.strip() == "./README.md"
    with open(tmp_path / "pwd.txt") as file:
        assert file.read().strip() == os.getcwd()
