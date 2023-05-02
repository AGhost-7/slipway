import signal
import json
import shutil
from subprocess import run, Popen, PIPE
from slipway.command_proxy import CommandProxy
from pytest import fixture
from os import environ, path
import os
import sys
import time
from .util import create_client
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def start_command_proxy(tmp_path: Path, script_name, script_content):
    logs_directory = tmp_path / "logs"
    command_proxy = CommandProxy(tmp_path, logs_directory, [script_name])

    fake_cli = tmp_path / script_name
    with open(fake_cli, "w+") as file:
        file.write(f"#!/bin/sh\n{script_content}")
    os.chmod(fake_cli, 0o700)

    sub_env = environ.copy()
    sub_env["PATH"] = f"{str(tmp_path)}:{sub_env['PATH']}"
    print('PATH', sub_env["PATH"])
    command_proxy.start_server(env=sub_env)

    proxy_bin = tmp_path / "proxy"
    proxy_bin.mkdir()
    proxy = proxy_bin / script_name
    proxy.symlink_to(command_proxy.client_path)

    # server takes a bit of time to start up...
    time.sleep(1)
    assert command_proxy.is_server_running()

    try:
        yield command_proxy
    finally:
        if command_proxy.is_server_running():
            command_proxy.stop_server()


def test_proxy_args(tmp_path: Path):
    with start_command_proxy(
        tmp_path, "xdg-open-test", f"echo $@ > {tmp_path}/args.txt"
    ) as command_proxy:

        result = run(
            [
                tmp_path / "proxy" / "xdg-open-test",
                "https://jokes.jonathan-boudreau.com",
            ],
            env={
                **environ,
                "SLIPWAY_COMMAND_PROXY_URL": command_proxy.bind_url,
            },
        )

        assert result.returncode == 0

        with open(tmp_path / "args.txt") as file:
            content = file.read()
            assert content.strip() == "https://jokes.jonathan-boudreau.com"


def test_workdir_mapping(tmp_path: Path, image_fixture: str):
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
    with start_command_proxy(
        tmp_path, "xdg-open-test", f"echo $PWD > {tmp_path}/pwd.txt"
    ) as command_proxy:
        result = run(
            [
                client.runtime,
                "run",
                "-ti",
                "--rm",
                "-v",
                f"{command_proxy.client_path}:/usr/bin/xdg-open-test",
                "-v",
                f"{tmp_path / 'slipway'}:/run/slipway",
                "-e",
                f"SLIPWAY_COMMAND_PROXY_URL={command_proxy.server_url}",
                "-v",
                f"{os.getcwd()}:/workspace",
                "-v" f"{mapping_file}:/run/user/1000/slipway-mapping.json",
                "python:3",
                "bash",
                "-c",
                "cd /workspace && xdg-open-test ./README.md",
            ]
        )
    assert result.returncode == 0
    with open(tmp_path / "pwd.txt") as file:
        assert file.read().strip() == os.getcwd()


def test_signals():
    tmp_path = Path("/tmp/pytest-of-jonathan/pytest-1/test_signals0")
    print('tmp_path', tmp_path)
    bind_url = "unix:///run/user/1000/slipway-test.sock"
    process = Popen(
        [tmp_path / "proxy" / "docker-compose-test"],
        env={
            **environ,
            "SLIPWAY_COMMAND_PROXY_URL": bind_url,
        },
        stdout=PIPE,
        stderr=PIPE,
    )
    os.kill(process.pid, signal.SIGINT.value)
    process.wait(10)
    print("returncode", process.returncode)
    print("stdout", process.stdout.read())
    print("stderr", process.stderr.read())
    #with start_command_proxy(
    #    tmp_path,
    #    "docker-compose-test",
    #    f"trap 'echo 1 > {tmp_path}/sig_int' INT; echo 1 > /tmp/test_signals.txt; sleep 10000",
    #) as command_proxy:
    #    print("proxy_url", command_proxy.bind_url)
    #    print('tmp_path', tmp_path)

    #    process = Popen(
    #        [tmp_path / "proxy" / "docker-compose-test"],
    #        env={
    #            **environ,
    #            "SLIPWAY_COMMAND_PROXY_URL": command_proxy.bind_url,
    #        },
    #        stdout=PIPE,
    #        stderr=PIPE,
    #    )
    #    print("signal.SIGINT", signal.SIGINT.value)
    #    # process.send_signal(signal.SIGINT.value)
    #    os.kill(process.pid, signal.SIGINT.value)
    #    time.sleep(1)
    #    process.wait(10)
    #    print("returncode", process.returncode)
    #    print("stdout", process.stdout.read())
    #    print("stderr", process.stderr.read())
    #    with open(tmp_path / "sig_int") as file:
    #        assert file.read().strip() == "1"


def test_stdio(tmp_path: Path):
    # logs_directory = tmp_path / "logs"
    # command_proxy = CommandProxy(tmp_path, logs_directory, ["echo-cli"])

    # fake_cli = tmp_path / "echo-cli"
    # with open(fake_cli, "w+") as file:
    #    file.write(
    #        "#!/bin/sh\n"
    #        "cat -"
    #    )
    # os.chmod(fake_cli, 0o700)

    # sub_env = environ.copy()
    # sub_env["PATH"] = f"{str(tmp_path)}:{sub_env['PATH']}"
    # command_proxy.start_server(env=sub_env)

    # proxy_bin = tmp_path / "proxy"
    # proxy_bin.mkdir()
    # echo_proxy = proxy_bin / "echo-cli"
    # echo_proxy.symlink_to(command_proxy.client_path)

    with start_command_proxy(tmp_path, "echo-cli", "cat -") as command_proxy:
        process = Popen(
            [tmp_path / "proxy" / "echo-cli"],
            env={
                **environ,
                "SLIPWAY_COMMAND_PROXY_URL": f"unix://{tmp_path}/slipway/command-proxy.sock",
            },
            stdin=PIPE,
            stdout=PIPE,
        )
        assert process.stdin is not None
        process.stdin.write(b"foobar")
        time.sleep(10)
        # process.wait(10)
        # process.stdin.close()
        # print("stdout", process.stdout.read())
        print("returncode", process.returncode)
