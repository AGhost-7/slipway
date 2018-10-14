from docker.errors import ImageNotFound
from os import path


class Image(object):
    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.name = args.image
        self._image = None

    def _docker_image(self):
        if self._image is None:
            self._image = self.client.images.get(self.name)
        return self._image

    def initialize(self):
        """
        Pulls the image if not present
        """
        try:
            self._docker_image()
        except ImageNotFound:
            message = 'Image {} not found, attempting to pull down'
            print(message.format(self.name))
            self.client.images.pull(self.name)

    @property
    def volumes(self):
        """
        Returns all volumes tied to the image's container configuration
        """
        config = self._docker_image().attrs['ContainerConfig']
        if config['Volumes'] is None:
            return []
        return list(config['Volumes'].keys())

    @property
    def entrypoint(self):
        return self._docker_image().attrs['ContainerConfig']['Entrypoint']

    @property
    def user(self):
        return self._docker_image().attrs['ContainerConfig']['User']

    @property
    def home(self):
        return path.join('/home', self.user)
