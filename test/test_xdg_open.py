import shutil
from subprocess import run
from slipway.xdg_open import XdgOpen
from pytest import fixture
from os import environ, path
import os
import sys
import time


@fixture
def xdg_open(tmp_path):
    runtime_dir = tmp_path / "slipway"
    xdg_open = XdgOpen(runtime_dir)
    yield xdg_open
    if xdg_open.is_server_running():
        xdg_open.stop_server()


def test_start_server(xdg_open):
    xdg_open.start_server()
    assert xdg_open.is_server_running()


def test_server_calls_xdg_open(tmp_path, xdg_open):
    # create isolated environment with only a stub of the xdg-open cli and
    # python3
    fake_cli = path.join(tmp_path, "xdg-open")
    with open(fake_cli, "w+") as file:
        file.write("#!/bin/sh\n" f"echo $@ > {tmp_path}/args.txt")
    os.chmod(fake_cli, 0o700)

    run([fake_cli, "https://jokes.jonathan-boudreau.com"]).check_returncode()

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
