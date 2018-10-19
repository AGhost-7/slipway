
import os
from os import path
from .image import Image
from .volumes import Volumes
from .binds import Binds
from .util import snake_case


class Container(object):

    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.image = Image(self.client, self.args)
        self.volumes = Volumes(self.client, self.args, self.image)
        self.binds = Binds(self.client, self.args, self.image)
        self.name = 'slipway_' + snake_case(self.args.image)

    def _entrypoint(self):
        module_dir = path.dirname(path.abspath(__file__))
        return path.abspath(
            path.join(module_dir, '../scripts/entrypoint.py'))

    def _volumes_env(self):
        return ','.join(list(map(lambda vol: vol.path, self.volumes.list())))

    def _run_arguments(self):
        arguments = [
            'docker',
            'run',
            '--net=host',
            '--user', 'root',
            '--rm',
            '-ti',
            '--detach-keys', 'ctrl-q,ctrl-q',
            '--name', self.name,
            '-e', 'GH_USER',
            '-e', 'GH_PASS',
            '-e', 'DISPLAY',
            '-e', 'SLIPWAY_USER={}'.format(self.image.user),
            '-e', 'SLIPWAY_VOLUMES={}'.format(self._volumes_env()),
            '-v', self._entrypoint() + ':/slipway-entrypoint.py:ro',
            '--entrypoint', '/slipway-entrypoint.py'
        ]

        for env in self.args.environment or []:
            arguments.append('-e')
            arguments.append(env)

        for bind in self.binds.list():
            arguments.append('-v')
            argument = bind.host_path + ':' + bind.container_path
            if 'ro' in bind.type:
                argument += ':ro'
            arguments.append(argument)

        for volume in self.volumes.list():
            arguments.append('--mount')
            arguments.append(
                'source={},target={}'.format(volume.name, volume.path))

        arguments.append(self.image.name)
        arguments.append('tmux')
        arguments.append('new')
        return arguments

    def run(self):
        os.execvp('docker', self._run_arguments())
