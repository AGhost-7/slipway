from .util import snake_case


class Volume(object):
    def __init__(self, image_name, path):
        base = 'slipway_' + snake_case(image_name)
        self.name = base + '_' + snake_case(path)
        self.path = path


class Volumes(object):
    def __init__(self, client, args, image):
        self.client = client
        self.args = args
        self.image = image

    def list(self):
        """
        Lists all volumes
        """
        return map(
            lambda volume: Volume(self.image.name, volume), self.image.volumes)

    def purge(self):
        """
        Clears all volumes tied to the given arguments
        """
        docker_volumes = self.client.volumes.list()
        for volume in self.list():
            found = None
            for docker_volume in docker_volumes:
                if volume.name == docker_volume.name:
                    found = docker_volume
            if found is not None:
                found.remove()

    def initialize(self):
        """
        Checks if the required volumer are present and creates them if missing.
        """
        docker_volumes = self.client.volumes.list()
        for volume in self.list():
            exist = False
            for docker_volume in docker_volumes:
                if volume.name == docker_volume.name:
                    exist = True
            if not exist:
                self.client.volumes.create(volume.name)
