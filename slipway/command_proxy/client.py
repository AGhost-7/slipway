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

try:
    from .stream import create_standard_streams
except (ModuleNotFoundError, ImportError):
    sys.path.append('/usr/local/lib/slipway/slipway')
    from command_proxy.stream import create_standard_streams


output = open("/tmp/proxy-command.log", "w+")


def debug(*args):
    print(*args, file=output)


def host_cwd() -> Optional[str]:
    cwd = os.getcwd()
    mapping_path = Path("/run/user") / str(os.getuid()) / "slipway-mapping.json"
    debug('host_cwd::mapping_path', mapping_path) 
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


async def poll_stdin(server_writer: StreamWriter, reader: StreamReader):
    """
    Forward stdin to server.
    """
    eof = False
    while not eof:
        chunk = await reader.read(1024)
        if len(chunk) == 0:
            eof = True
        server_writer.write(encode(MESSAGE_STDIN, chunk))


async def poll_replies(server_reader: StreamReader, stdout: StreamWriter, stderr: StreamWriter) -> int:
    """
    Checks for messages from the server and send to appropriate pipe or exit.
    """
    while True:
        header = await server_reader.read(3)
        if len(header) < 3:
            debug("connection closed")
            print("Connection to proxy server closed", file=sys.stderr)
            return 1
        message_type = int.from_bytes(header[0:1], "big", signed=False)
        size = int.from_bytes(header[1:3], "big", signed=False)
        debug("got header, waiting for body")
        body = await server_reader.read(size)
        if len(body) < size:
            debug("connection closed")
            print("Connection to proxy server closed", file=sys.stderr)
            return 1

        if message_type == MESSAGE_STDOUT:
            debug("got stdout message", body)
            stdout.write(body)
        elif message_type == MESSAGE_STDERR:
            debug("got stderr message", body)
            stderr.write(body)
        elif message_type == MESSAGE_EXIT:
            debug("got exit message", body)
            return int.from_bytes(body, "big", signed=False)


async def main():
    args = sys.argv[1:]
    proxy_url = urlparse(environ["SLIPWAY_COMMAND_PROXY_URL"])
    debug("sending", proxy_url)
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
            "tty": os.isatty(sys.stdout.fileno()),
        }
    )
    writer.write(encode(MESSAGE_INIT, bytes(payload, "utf8")))

    def handler(signal_number: int, frame):
        writer.write(
            encode(
                MESSAGE_SIGNAL, signal_number.to_bytes(4, byteorder="big", signed=False)
            )
        )

    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGINT, handler)
    debug('sys.stdin', sys.stdin, 'sys.stdout', sys.stdout, 'sys.stderr', sys.stderr)
    stdin, stdout, stderr = await create_standard_streams(sys.stdin, sys.stdout, sys.stderr)
    stdin_task = asyncio.create_task(poll_stdin(writer, stdin))
    exit_code = await poll_replies(reader, stdout, stderr)
    stdin_task.cancel()
    writer.close()
    output.flush()
    #debug('returning')
    return exit_code


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    exit_code = loop.run_until_complete(main())
    debug('completed without issue')
    output.flush()
    output.close()
    loop.stop()
    loop.close()
    sys.exit(exit_code)
