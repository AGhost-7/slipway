import shutil
from subprocess import run
from slipway.xdg_open import XdgOpen
from pytest import fixture
from os import environ, path
import os
import sys
import time
from .util import create_client


@fixture
def xdg_open(tmp_path):
    runtime_dir = tmp_path / "slipway"
    xdg_open = XdgOpen(runtime_dir)
    yield xdg_open
    if xdg_open.is_server_running():
        xdg_open.stop_server()
        pass


def test_start_server(xdg_open):
    xdg_open.start_server()
    assert xdg_open.is_server_running()


def test_server_calls_xdg_open(tmp_path, xdg_open):
    fake_cli = path.join(tmp_path, "xdg-open")
    with open(fake_cli, "w+") as file:
        file.write("#!/bin/sh\n" f"echo $@ > {tmp_path}/args.txt")
    os.chmod(fake_cli, 0o700)

    sub_env = environ.copy()
    sub_env["PATH"] = str(tmp_path)
    shutil.copy2(sys.executable, tmp_path / "python3")
    xdg_open.start_server(env=sub_env)
    assert xdg_open.is_server_running()
    # server takes a bit of time to start up...
    time.sleep(1)

    result = run(
        [xdg_open.client_path, "https://jokes.jonathan-boudreau.com"],
        env={**environ, "SLIPWAY_RUNTIME_DIR": xdg_open.runtime_dir},
    )

    assert result.returncode == 0

    with open(path.join(tmp_path, "args.txt")) as file:
        content = file.read()
        assert content.strip() == "https://jokes.jonathan-boudreau.com"


def test_xdg_mapping(tmp_path, xdg_open: XdgOpen, image_fixture: str):
    fake_cli = path.join(tmp_path, "xdg-open")
    with open(fake_cli, "w+") as file:
        file.write(
            "#!/bin/sh\n"
            f"echo $@ > {tmp_path}/args.txt; echo $PWD > {tmp_path}/pwd.txt"
        )
    os.chmod(fake_cli, 0o700)

    sub_env = environ.copy()
    sub_env["PATH"] = str(tmp_path)
    shutil.copy2(sys.executable, tmp_path / "python3")
    xdg_open.start_server(env=sub_env)
    assert xdg_open.is_server_running()
    time.sleep(1)

    client = create_client()
    result = run(
        [
            client.runtime,
            "run",
            "-ti",
            "--rm",
            "-v",
            f"{xdg_open.client_path}:/usr/bin/xdg-open",
            "-v",
            f"{xdg_open.runtime_dir}:/run/slipway",
            "-v",
            f"{os.getcwd()}:/workspace",
            "python:3",
            "bash",
            "-c",
            "cd /workspace && xdg-open ./README.md",
        ]
    )
    assert result.returncode == 0
    with open(path.join(tmp_path, "args.txt")) as file:
        content = file.read()
        assert content.strip() == "./README.md"
    with open(path.join(tmp_path, "pwd.txt")) as file:
        assert file.read().strip() == os.getcwd()
