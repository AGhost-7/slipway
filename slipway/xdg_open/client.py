#!/usr/bin/env python3

import socket
import json
import sys
from os import path, environ

url = sys.argv[1]

socket_file = path.join(
    environ.get('SLIPWAY_RUNTIME_DIR', '/run/slipway'),
    'xdg-open.sock')

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect(socket_file)
    sock.sendall(bytes(url + '\n', 'utf8'))
    line_end = False
    attempts_left = 100
    data = ''

    while not line_end and attempts_left:
        attempts_left -= 1
        chunk = sock.recv(2046)
        converted = str(chunk, 'utf8')
        if '\n' in converted:
            line_end = True
        data += converted

    if attempts_left:
        result = json.loads(data)
        sys.stderr.write(result['stderr'])
        sys.stdout.write(result['stdout'])
        sys.exit(result['returncode'])
    else:
        print('xdg-open server failed to reply', file=sys.stderr)
        sys.exit(1)
