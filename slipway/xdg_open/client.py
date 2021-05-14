#!/usr/bin/env python3

from typing import Optional
import socket
import json
import sys
from os import path, environ
import os

args = sys.argv[1:]

socket_file = path.join(
    environ.get("SLIPWAY_RUNTIME_DIR", "/run/slipway"), "xdg-open.sock"
)


def host_cwd() -> Optional[str]:
    cwd = os.getcwd()
    with open("/proc/self/mountinfo") as file:
        for line in file.read().strip().splitlines():
            columns = line.split(" ")
            host_path = columns[3]
            container_path = columns[4]
            if container_path != "/" and cwd.startswith(container_path):
                return cwd.replace(container_path, host_path)
    return None


def wait_result() -> Optional[dict]:
    line_end = False
    attempts_left = 100
    data = ""

    while not line_end and attempts_left:
        attempts_left -= 1
        chunk = sock.recv(2046)
        converted = str(chunk, "utf8")
        if "\n" in converted:
            line_end = True
        data += converted

    if attempts_left:
        return json.loads(data)
    return None


with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect(socket_file)
    payload = json.dumps(
        {
            "args": args,
            "cwd": host_cwd(),
        }
    )
    sock.sendall(bytes(payload + "\n", "utf8"))
    result = wait_result()

    if result is not None:
        sys.stderr.write(result["stderr"])
        sys.stdout.write(result["stdout"])
        sys.exit(result["returncode"])
    else:
        print("xdg-open server failed to reply", file=sys.stderr)
        sys.exit(1)
