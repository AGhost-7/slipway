from .util import snake_case


class Volume(object):
    def __init__(self, image_name, path):
        base = "slipway_" + snake_case(image_name)
        self.name = base + "_" + snake_case(path)
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
        return map(lambda volume: Volume(self.image.name, volume), self.image.volumes)

    def purge(self):
        """
        Clears all volumes tied to the given arguments
        """
        current_volumes = self.client.list_volume_names()
        for volume in self.list():
            found = None
            for volume_name in current_volumes:
                if volume.name == volume_name:
                    found = volume_name
            if found is not None:
                self.client.remove_volume(found)

    def initialize(self):
        """
        Checks if the required volume are present and creates them if missing.
        """
        current_volume_names = self.client.list_volume_names()
        for volume in self.list():
            exist = False
            for volume_name in current_volume_names:
                if volume.name == volume_name:
                    exist = True
            if not exist:
                self.client.create_volume(volume.name)
