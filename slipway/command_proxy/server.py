"""
This script accepts a bind url, and commands which are allowed to execute on
the host system.
"""

from asyncio import StreamReader, StreamWriter
import asyncio
from asyncio.subprocess import Process
import json
import sys
import os
import stat
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse


url = urlparse(sys.argv[1])
allowed_commands = sys.argv[2:]

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


def request_cwd(request: Dict[str, Any]) -> Optional[str]:
    """
    Checks if the cwd provided by the client is valid. Ignores invalid ones.
    """
    cwd = request["cwd"]
    if cwd is not None and not Path(cwd).exists():
        print(f"The path {cwd} does not exist on the host, ignoring", file=sys.stdout)
        cwd = None
    return cwd


def translate_darwin_call(command: str, args: List[str]) -> Tuple[str, List[str]]:
    """
    Handles converting linux-only commands to darwin compatible ones.
    """

    if command == "xdg-open":
        return ("open", args)
    elif command == "xclip":
        if "-o" not in args and "-out" not in args:
            return ("pbcopy", [])
        else:
            return ("pbpaste", [])
    return (command, args)


async def read_client(reader: StreamReader) -> Tuple[int, bytes]:
    """
    Waits until a complete message has been received from the client, and then
    decodes it.
    """
    header = await reader.read(3)
    assert len(header) != 0
    message_type = int.from_bytes(header[0:1], "big", signed=False)
    size = int.from_bytes(header[1:3], "big", signed=False)
    body = await reader.read(size)
    return (message_type, body)


async def poll_client(reader: StreamReader, process: Process, stdin: StreamWriter):
    """
    Continuously waits to receive a stdin message from the client.
    """
    while True:
        (message_type, body) = await read_client(reader)
        if message_type == MESSAGE_STDIN:
            if len(body) == 0:
                stdin.write_eof()
            else:
                stdin.write(body)
        elif message_type == MESSAGE_SIGNAL:
            signal = int.from_bytes(body, "big", signed=False)
            print("Got signal", signal)
            process.send_signal(signal)


async def poll_pipe(writer: StreamWriter, message_type: int, pipe: StreamReader):
    """
    Continuously waits for stdout/stderr chunks which are then sent back to the
    client.
    """
    while True:
        body = await pipe.read(1024)
        if len(body) == 0:
            break
        writer.write(encode(message_type, body))


async def client_connected(reader: StreamReader, writer: StreamWriter):
    """
    Handles a new client connection.
    """
    print('client_connected')
    (message_type, body) = await read_client(reader)
    if message_type == MESSAGE_INIT:
        request = json.loads(body)
        command = request["command"]

        cwd = request_cwd(request)
        args = request["args"]
        if command not in allowed_commands:
            writer.write(
                encode(
                    MESSAGE_STDERR,
                    bytes(
                        f"Command {command} is not permitted to run on the host\n",
                        "utf8",
                    ),
                )
            )
            writer.write(
                encode(MESSAGE_EXIT, (1).to_bytes(1, byteorder="big", signed=False))
            )
        else:
            if sys.platform == "darwin":
                (command, args) = translate_darwin_call(command, args)
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert (
                process.stdin is not None
                and process.stdout is not None
                and process.stderr is not None
            )

            client_task = asyncio.create_task(
                poll_client(reader, process, process.stdin)
            )
            stdout_task = asyncio.create_task(
                poll_pipe(writer, MESSAGE_STDOUT, process.stdout)
            )
            stderr_task = asyncio.create_task(
                poll_pipe(writer, MESSAGE_STDERR, process.stderr)
            )

            await process.wait()
            assert process.returncode is not None
            client_task.cancel()
            stdout_task.cancel()
            stderr_task.cancel()
            writer.write(
                encode(
                    MESSAGE_EXIT,
                    process.returncode.to_bytes(1, byteorder="big", signed=False),
                )
            )


async def main():
    assert url.scheme in ("unix", "tcp"), f"Invalid scheme {url.scheme}"
    if url.scheme == "unix":
        socket_file = Path(url.path)
        if socket_file.exists():
            socket_file.unlink()
        server = await asyncio.start_unix_server(client_connected, socket_file)
    else:
        [host, port] = url.netloc.split(":")
        server = await asyncio.start_server(client_connected, host, port)
    print("Listening on addresss", sys.argv[1])
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
