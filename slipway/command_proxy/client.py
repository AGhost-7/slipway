#!/usr/bin/env python3

from pathlib import Path
from typing import Optional
import json
import sys
from os import path, environ
import os
import json
from urllib.parse import urlparse
import socket
import asyncio
from asyncio import StreamWriter, StreamReader


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


# The binary protocol is layed out with a constant size header and variable
# size body. The first byte determines the type of message, and there are
# two bytes which determine the size of the message

MESSAGE_INIT = 1
MESSAGE_STDIN = 2
MESSAGE_STDOUT = 3
MESSAGE_STDERR = 4
MESSAGE_EXIT = 5


def encode(message_type, body):
    size = len(body)
    assert size < 65536, "Message encoding failed due to out of bounds"
    size_bytes = stdin_size.to_bytes(2, byteorder="big")
    message = bytearray(stdin_size + 3)
    message[0] = message_type.to_bytes(1, byteorder="big")
    message[1] = size_bytes[0]
    message[2] = size_bytes[1]
    message += body


async def poll_stdin(server_writer: StreamWriter):
    reader = StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    loop = asyncio.get_event_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    while True:
        chunk = await reader.read(1024)
        server_writer.write(encode(MESSAGE_STDIN, chunk))


async def poll_replies(server_reader: StreamReader):
    while True:
        header = await server_reader.read(3)
        if len(header) < 3:
            print("Connection to proxy server closed", file=sys.stderr)
            break
        message_type = int.from_bytes(header[0:1], "big")
        size = int.from_bytes(header[1:2], "big")
        body = await server_reader.read(size)
        if len(body) < size:
            print("Connection to proxy server closed", file=sys.stderr)
            break

        if message_type == MESSAGE_STDOUT:
            sys.stderr.write(str(body, "utf8"))
        elif message_type == MESSAGE_STDERR:
            sys.stdout.write(str(body, "utf8"))
        elif message_type == MESSAGE_EXIT:
            return int.from_bytes(body, "big")


async def main():
    args = sys.argv[1:]
    proxy_url = urlparse(environ["SLIPWAY_COMMAND_PROXY_URL"])
    if proxy_url.scheme == "unix":
        reader, writer = await asyncio.open_unix_connection(proxy_url.path)
    else:
        [host, port] = proxy_url.netloc.split(":")
        reader, writer = await asyncio.open_connection(host, int(port))

    command = path.basename(sys.argv[0])
    payload = json.dumps(
        {
            "args": args,
            "command": command,
            "cwd": host_cwd(),
        }
    )
    writer.write(encode(MESSAGE_INIT, bytes(payload, "utf8")))
    stdin_task = asyncio.create_task(poll_stdin(writer))
    exit_code = await poll_replies(server_reader)
    sys.exit(exit_code)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
