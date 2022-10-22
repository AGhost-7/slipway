"""
The binary protocol is layed out with a fixed size header and variable
size body. The first byte determines the type of message, and there are
two bytes which determine the size of the message.
"""

from enum import Enum
from typing import Tuple
from asyncio import StreamReader


class ConnectionClosedException(Exception):
    pass


class MessageType(Enum):
    # initial configuration step
    INIT = 1
    # stdin frame
    STDIN = 2
    # stdout frame
    STDOUT = 3
    # stderr frame
    STDERR = 4
    # process has terminated
    EXIT = 5
    # process signal being sent by the client
    SIGNAL = 6


def encode(message_type: MessageType, body: bytes) -> bytes:
    """
    Encodes the the data into a frame. The header is a fixed size of 3 bytes,
    where the first byte determines the type of frame. The next two bytes
    determine the size of the body. The body is of variable size.
    """
    size = len(body)
    assert size < 65536, "Message encoding failed due to out of bounds"
    size_bytes = size.to_bytes(2, byteorder="big", signed=False)
    type_bytes = message_type.value.to_bytes(1, byteorder="big", signed=False)
    message = b"".join([type_bytes, size_bytes, body])
    return message


async def decode(reader: StreamReader) -> Tuple[MessageType, bytes]:
    header = await reader.read(3)
    if len(header) < 3:
        raise ConnectionClosedException()
    message_type = int.from_bytes(header[0:1], "big", signed=False)
    size = int.from_bytes(header[1:3], "big", signed=False)
    body = await reader.read(size)
    if len(body) < size:
        raise ConnectionClosedException()
    return (MessageType(message_type), body)
