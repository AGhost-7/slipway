#!/usr/bin/env python3

from pathlib import Path
from typing import Optional
import socket
import json
import sys
from os import path, environ
import os
import json
from urllib.parse import urlparse

args = sys.argv[1:]

proxy_url = urlparse(environ["SLIPWAY_COMMAND_PROXY_URL"])


def host_cwd() -> Optional[str]:
    cwd = os.getcwd()
    mapping_path = Path("/run/user") / str(os.getuid()) / "slipway-mapping.json"
    if not mapping_path.exists():
        return None
    with mapping_path.open() as file:
        mappings = json.loads(file.read())
    for mapping in mappings:
        if cwd.startswith(mapping["container"]):
            return cwd.replace(mapping["container"], mapping["host"])
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


socket_type = socket.AF_UNIX if proxy_url.scheme == "unix" else socket.AF_INET
with socket.socket(socket_type, socket.SOCK_STREAM) as sock:
    if proxy_url.scheme == "unix":
        sock.connect(proxy_url.path)
    else:
        [host, port] = proxy_url.netloc.split(":")
        sock.connect((host, int(port)))
    command = path.basename(sys.argv[0])
    payload = json.dumps(
        {
            "args": args,
            "command": command,
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
