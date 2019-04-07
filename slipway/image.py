from docker.errors import ImageNotFound

from multiprocessing.dummy import Pool
import math
from os import path
import re
import requests
from sys import stdout


# ANSI (terminal) escape sequences
CLEAR_LINE = '\x1b[0K'
SHOW_CURSOR = '\x1b[?25h'
HIDE_CURSOR = '\x1b[?25l'


class Image(object):
    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.name = args.image
        self._image = None

        colon_parts = self.name.split(':')
        if len(colon_parts) == 1:
            self._tag = 'latest'
        else:
            self._tag = colon_parts[1]

        slash_parts = colon_parts[0].split('/')

        if len(slash_parts) == 3:
            self._registry_base_url = slash_parts[0]
        else:
            self._registry_base_url = 'https://index.docker.io'

        if len(slash_parts) == 1:
            self._repository = 'library/' + slash_parts[0]
        elif len(slash_parts) == 2:
            self._repository = '/'.join(slash_parts)
        else:
            self._repository = '/'.join(slash_parts[:1])

    def _docker_image(self):
        if self._image is None:
            self._image = self.client.images.get(self.name)
        return self._image

    def stale(self):
        """
        Returns true if the image isn't in sync with what is in the registry.
        """
        distribution = self.client.api.inspect_distribution(self.name)
        remote_digest = distribution['Descriptor']['digest']
        for local_digest in self._docker_image().attrs['RepoDigests']:
            remote_part = remote_digest.split(':')[1]
            local_part = local_digest.split(':')[1]
            if remote_part != local_part:
                return True
        return False

    def _registry_auth_url(self, base_url):
        if base_url == 'https://index.docker.io':
            return ('https://auth.docker.io/token', 'registry.docker.io')
        else:
            response = requests.get(
                base_url + '/v2/_catalog')
            if response.status_code != 401:
                message = 'Unexpected status code while determining ' + \
                    'authentication url'
                raise Exception(message)
            authenticate = response.headers['Www-authenticate']
            auth_url = re.match('realm="([^,]+)"', authenticate)
            service_url = re.match('service="([^,]+)"', authenticate)
            return (auth_url, service_url)

    def _urljoin(self, *parts):
        return '/'.join(parts)

    def _registry_token(self, auth_url, service_url):
        scope = 'repository:' + self._repository + ':pull'
        query = 'scope=' + scope + '&service=' + service_url
        url = auth_url + '?' + query
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(
                'Failed to retrieve auth token')
        return response.json()['token']

    def _registry_manifest(self, token):
        url = self._urljoin(
            self._registry_base_url, 'v2', self._repository, 'manifests',
            self._tag)
        headers = {'authorization': 'Bearer ' + token}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            message = 'Unexpected {} response retrieving manifest'
            formatted = message.format(response.status_code)
            raise Exception(formatted)
        return response.json()

    def _manifest_layer_size(self, token, manifest):
        def fetch(layer):
            digest = layer['blobSum']
            url = self._registry_base_url + '/v2/' + self._repository + \
                '/blobs/' + digest
            headers = {'authorization': 'Bearer ' + token}
            with requests.get(url, headers=headers, stream=True) as response:
                if response.status_code != 200:
                    message = 'Unexpected {} response determining layer size'
                    raise Exception(message.format(response.status_code))
                content_length = int(response.headers['content-length'])
                id = digest.replace('sha256:', '')
                return (id, content_length)
        pool = Pool(10)
        sizes = pool.map(fetch, manifest['fsLayers'])
        layer_sizes = {}
        total = 0
        for (id, size) in sizes:
            total += size
            layer_sizes[id] = size
        return (total, layer_sizes)

    def _format_bytes(self, unformatted):
        mb = (unformatted / 1024) / 1024
        rounded = math.floor(mb * 10) / 10
        return '{} MB'.format(rounded)

    def _print_pull_status(self, total, downloaded, extracted):
        formatted_total = self._format_bytes(total)
        if self._pull_status_started:
            stdout.write(CLEAR_LINE)
            stdout.flush()
        else:
            self._pull_status_started = True

        stdout.write('Downloaded: {} / {}, Extracted: {} / {}\r'.format(
            self._format_bytes(downloaded),
            formatted_total,
            self._format_bytes(extracted),
            formatted_total))
        stdout.flush()

    def _consume_pull_status_stream(self, total, layer_sizes, stream):
        downloaded = 0
        extracted = 0
        downloaded_layers = {}
        extracted_layers = {}
        for status in stream:
            if status['status'] == 'Downloading':
                detail = status['progressDetail']
                if status['id'] in downloaded_layers:
                    layer = downloaded_layers[status['id']]
                    downloaded -= layer['current']
                downloaded += detail['current']
                downloaded_layers[status['id']] = detail
                self._print_pull_status(total, downloaded, extracted)
            elif status['status'] == 'Extracting':
                if status['id'] in extracted_layers:
                    layer = extracted_layers[status['id']]
                    extracted -= layer['current']
                extracted += detail['current']
                extracted_layers[status['id']] = detail
                self._print_pull_status(total, downloaded, extracted)
            elif status['status'] == 'Already exists':
                size = None
                for layer in layer_sizes:
                    if layer.startswith(status['id']):
                        size = layer_sizes[layer]
                        break
                if size is None:
                    raise Exception('Unexpected layer from daemon')
                downloaded += size
                extracted += size
                self._print_pull_status(total, downloaded, extracted)

    def pull(self):
        print('Computing total image size')
        (auth_url, service_url) = self._registry_auth_url(
            self._registry_base_url)
        token = self._registry_token(auth_url, service_url)
        manifest = self._registry_manifest(token)
        (total, layer_sizes) = self._manifest_layer_size(token, manifest)
        self._pull_status_started = False
        print('Downloading layers')
        stream = self.client.api.pull(
            self._repository, tag=self._tag, stream=True, decode=True)
        try:
            stdout.write(HIDE_CURSOR)
            stdout.flush()
            self._consume_pull_status_stream(total, layer_sizes, stream)
        finally:
            stdout.write(SHOW_CURSOR)
            stdout.flush()

    def exists(self):
        """
        Returns true if the image exists locally, false otherwise.
        """
        try:
            self._docker_image()
            return True
        except ImageNotFound:
            return False

    def initialize(self):
        """
        Pulls the image if not present
        """
        if not self.exists():
            message = 'Image {} not found, attempting to pull down'
            print(message.format(self.name))
            self.pull()
        elif self.args.pull:
            print('Checking for updates')
            if self.stale():
                print('Updates available, pulling')
                self.pull()

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
