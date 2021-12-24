#!/usr/bin/env python3

import signal
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
import stat


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
MESSAGE_SIGNAL = 6


def encode(message_type: int, body: bytes) -> bytes:
    """
    Encodes the the data into a frame. The header is a fixed size of 3 bytes,
    where the first byte determines the type of frame. The next two bytes
    determine the size of the body. The body is of variable size.
    """
    size = len(body)
    assert size < 65536, "Message encoding failed due to out of bounds"
    size_bytes = size.to_bytes(2, byteorder="big", signed=False)
    type_bytes = message_type.to_bytes(1, byteorder="big", signed=False)
    message = b"".join([type_bytes, size_bytes, body])
    return message


async def poll_stdin(server_writer: StreamWriter):
    """
    Forward stdin to server.
    """
    loop = asyncio.get_event_loop()
    try:
        file = await loop.run_in_executor(None, open, 0, "rb")
        eof = False
        while not eof:
            chunk = await loop.run_in_executor(None, file.read, 1024)
            if len(chunk) == 0:
                eof = True
            server_writer.write(encode(MESSAGE_STDIN, chunk))  # type: ignore
    finally:
        if file is not None:
            file.close()


async def poll_replies(server_reader: StreamReader):
    """
    Checks for messages from the server and send to appropriate pipe or exit.
    """
    while True:
        header = await server_reader.read(3)
        if len(header) < 3:
            print("Connection to proxy server closed", file=sys.stderr)
            return 1
        message_type = int.from_bytes(header[0:1], "big", signed=False)
        size = int.from_bytes(header[1:3], "big", signed=False)
        body = await server_reader.read(size)
        if len(body) < size:
            print("Connection to proxy server closed", file=sys.stderr)
            return 1

        if message_type == MESSAGE_STDOUT:
            sys.stdout.write(str(body, "utf8"))
        elif message_type == MESSAGE_STDERR:
            sys.stderr.write(str(body, "utf8"))
        elif message_type == MESSAGE_EXIT:
            return int.from_bytes(body, "big", signed=False)


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

    def handler(signal_number: int, frame):
        print("sending signal")
        writer.write(
            encode(
                MESSAGE_SIGNAL, signal_number.to_bytes(4, byteorder="big", signed=False)
            )
        )

    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGINT, handler)

    stdin_task = asyncio.create_task(poll_stdin(writer))
    exit_code = await poll_replies(reader)
    stdin_task.cancel()
    os._exit(exit_code)  # TODO: why is it not exiting cleanly?


asyncio.run(main())
