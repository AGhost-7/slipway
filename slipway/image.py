from typing import List
from os import path, makedirs
from datetime import datetime
from .util import snake_case


class PasswdEntry(object):
    def __init__(self, uid: int, gid: int):
        self.uid = uid
        self.gid = gid


class Image(object):
    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.name = args.image
        self._metadata = None
        self._passwd = None
        self._group = None

    def _cached_file(self, name: str, container_path: str):
        cache_path = path.join(self.args.cache_directory, name, self.id)
        if path.exists(cache_path):
            with open(cache_path) as file:
                text = file.read()
        else:
            text = self.client.image_file(self.name, container_path)
            makedirs(path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w+") as file:
                file.write(text)
        return text

    def _image_passwd(self):
        if self._passwd is None:
            self._passwd = {}
            text = self._cached_file("passwd", "/etc/passwd")
            for line in text.splitlines():
                parts = line.split(":")
                self._passwd[parts[0]] = PasswdEntry(int(parts[2]), int(parts[3]))
        return self._passwd

    def _image_group(self):
        if self._group is None:
            self._group = {}
            text = self._cached_file("group", "/etc/group")
            for line in text.splitlines():
                parts = line.split(":")
                self._group[parts[0]] = int(parts[2])
        return self._group

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
            self.args.data_directory, "last_stale_check", snake_case(self.name)
        )
        if path.exists(last_stale_path):
            with open(last_stale_path) as file_descriptor:
                content = file_descriptor.read()
                last_pull = datetime.strptime(content, "%Y-%m-%d")
                now = datetime.now()
                return (
                    now.day == last_pull.day
                    and now.month == last_pull.month
                    and now.year == last_pull.year
                )

        return False

    def _create_stale_check_file(self):
        """
        Creates the last_pull file which after a successful pull was performed.
        """
        stale_check_dir = path.join(self.args.data_directory, "last_stale_check")
        makedirs(stale_check_dir, exist_ok=True)
        content = datetime.now().strftime("%Y-%m-%d")
        last_stale_path = path.join(stale_check_dir, snake_case(self.name))
        with open(last_stale_path, "w+") as file_descriptor:
            file_descriptor.write(content)

    def initialize(self):
        """
        Pulls the image if not present
        """
        if not self.exists():
            message = "Image {} not found, attempting to pull down"
            print(message.format(self.name))
            self.pull()
            self._create_stale_check_file()
        elif self.args.pull and not (self.args.pull_daily and self._pulled_today()):
            self.pull()
            self._create_stale_check_file()

    @property
    def user_ids(self) -> List[int]:
        return [entry.uid for entry in self._image_passwd().values()]

    @property
    def group_ids(self) -> List[int]:
        return list(self._image_group().values())

    @property
    def volumes(self):
        """
        Returns all volumes tied to the image's container configuration
        """
        config = self._image_metadata()["Config"]
        if config.get("Volumes") is None:
            return []
        return list(config["Volumes"].keys())

    @property
    def id(self):
        return self._image_metadata()["Id"].replace("sha256:", "")

    @property
    def entrypoint(self):
        return self._image_metadata()["Config"]["Entrypoint"]

    @property
    def user(self) -> str:
        user = self._image_metadata()["Config"].get("User", "root")
        return "root" if user == "" else user

    @property
    def user_id(self) -> int:
        if self.user.isdigit():
            return int(self.user)
        return self._image_passwd()[self.user].uid

    @property
    def group_id(self) -> int:
        return self._image_passwd()[self.user].gid

    @property
    def home(self):
        return path.join("/home", self.user)
