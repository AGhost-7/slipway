
from os import path, makedirs
from datetime import datetime
from .util import snake_case


class Image(object):
    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.name = args.image
        self._metadata = None

    def _image_metadata(self):
        if self._metadata is None:
            self._metadata = self.client.inspect_image(self.name)
        return self._metadata

    def pull(self):
        self.client.pull_image(self.name)

    def exists(self):
        """
        Returns true if the image exists locally, false otherwise.
        """

        return self.client.image_exists(self.name)

    def _pulled_today(self):
        """
        Returns true is the last successful pull was performed today.
        """
        last_stale_path = path.join(
            self.args.data_directory,
            'last_stale_check',
            snake_case(self.name))
        if path.exists(last_stale_path):
            with open(last_stale_path) as file_descriptor:
                content = file_descriptor.read()
                last_pull = datetime.strptime(content, '%Y-%m-%d')
                now = datetime.now()
                return now.day == last_pull.day \
                    and now.month == last_pull.month \
                    and now.year == last_pull.year

        return False

    def _create_stale_check_file(self):
        """
        Creates the last_pull file which after a successful pull was performed.
        """
        stale_check_dir = path.join(
            self.args.data_directory, 'last_stale_check')
        makedirs(stale_check_dir, exist_ok=True)
        content = datetime.now().strftime('%Y-%m-%d')
        last_stale_path = path.join(stale_check_dir, snake_case(self.name))
        with open(last_stale_path, 'w+') as file_descriptor:
            file_descriptor.write(content)

    def initialize(self):
        """
        Pulls the image if not present
        """
        if not self.exists():
            message = 'Image {} not found, attempting to pull down'
            print(message.format(self.name))
            self.pull()
            self._create_stale_check_file()
        elif self.args.pull and not (
                self.args.pull_daily and self._pulled_today()):
            self.pull()
            self._create_stale_check_file()

    @property
    def volumes(self):
        """
        Returns all volumes tied to the image's container configuration
        """
        config = self._image_metadata()['Config']
        if config['Volumes'] is None:
            return []
        return list(config['Volumes'].keys())

    @property
    def entrypoint(self):
        return self._image_metadata()['Config']['Entrypoint']

    @property
    def user(self):
        return self._image_metadata()['Config']['User']

    @property
    def home(self):
        return path.join('/home', self.user)
