#!/usr/bin/env python3

"""
Entrypoint script
"""

import os
from os import environ
import sys
import pwd


entrypoint = environ.get('SLIPWAY_ENTRYPOINT')
user_name = environ.get('SLIPWAY_USER')

# All we need to do is correct the permisions in the volumes and call it a day.
user = pwd.getpwnam(user_name)
uid = user.pw_uid
gid = user.pw_gid

for volume in environ.get('SLIPWAY_VOLUMES').split(','):
    if len(volume) > 0:
        os.chown(volume, uid, gid)

# Essentially, doing this but in python:
# exec su -c "$@" $SLIPWAY_USER

args = ['sudo', '--preserve-env', '-u', user_name]

if entrypoint:
    args.append(entrypoint)

args.extend(sys.argv[1:])

os.execvp('sudo', args)
