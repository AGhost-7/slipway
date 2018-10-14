import pwd
import os
from os import environ, path


class Bind(object):
    def __init__(self, host_path, container_path, type='d'):
        self.host_path = host_path
        self.container_path = container_path
        self.type = type


class Binds(object):
    """
    A bind is a type of volume which maps a directory or file from the host
    into the container.
    """

    def __init__(self, client, args, image):
        self.client = client
        self.args = args
        self.image = image

    def initialize(self):
        """
        Creates the directory with appropriate permissions if it doesn't
        exist. Otherwise if we let docker do this the permissions will be
        set as root, which we don't want.
        """
        for bind in self.list():
            if not path.exists(bind.host_path):
                if 'd' in bind.type:
                    os.makedirs(bind.host_path)
                elif 'f' in bind.type:
                    open(bind.host_path, 'w+').close()

    def list(self):
        """
        List all bind mounts, including the default ones.
        """
        home_mappings = [
            ('d', 'workspaces'),
            ('d', '.ssh'),
            ('f', '.gitconfig')
        ]
        for type, mapping in home_mappings:
            host_path = path.join(environ['HOME'], mapping)
            container_path = path.join(self.image.home, mapping)
            yield Bind(host_path, container_path, type)

        if path.isfile('/etc/localtime'):
            yield Bind('/etc/localtime', '/etc/localtime', 'fro')
        if path.exists('/tmp/.X11-unix'):
            yield Bind('/tmp/.X11-unix', '/tmp/.X11-unix', 'fro')

        uid = pwd.getpwnam(environ['USER']).pw_uid
        gnupg_socket_path = path.join('/run/user', str(uid), 'gnupg')
        if path.exists(gnupg_socket_path):
            # FIXME: how to get uid of user in container?
            yield Bind(gnupg_socket_path, '/run/user/1000/gnupg', 'dro')

        gnupg_path = path.join(environ['HOME'], '.gnupg')
        if path.exists(gnupg_path):
            container_path = path.join(self.image.home, '.gnupg')
            yield Bind(gnupg_path, container_path, 'd')

        for volume in self.args.volume or []:
            parts = volume.split(':')
            host_path = parts[0]
            container_path = parts[1]
            type = 'd'
            if path.isfile(host_path):
                type = 'f'
            if len(parts) == 3 and parts[2] == 'ro':
                type += 'ro'
            yield Bind(host_path, container_path, type)
