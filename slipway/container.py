
import os
from os import environ, path
from .image import Image
from .volumes import Volumes
from .util import snake_case


class Container(object):

    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.image = Image(self.client, self.args)
        self.volumes = Volumes(self.client, self.args, self.image)
        self.name = 'slipway_' + snake_case(self.args.image)

    def _run_arguments(self):
        arguments = [
            'docker',
            'run',
            '--net=host',
            '--rm',
            '-ti',
            '--detach-keys', 'ctrl-q,ctrl-q',
            '--name', self.name,
            '-e', 'GH_USER',
            '-e', 'GH_PASS',
            '-e', 'DISPLAY',
            '-v', '/tmp/.X11-unix:/tmp/.X11-unix:ro',
            '-v', '/etc/localtime:/etc/localtime:ro'
        ]
        for mapping in ('workspaces', '.gitconfig', '.ssh'):
            arguments.append('-v')
            arguments.append(
                path.join(environ['HOME'], mapping) + ':' +
                path.join(self.image.home, mapping)
            )
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
