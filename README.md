# Slipway
An easier way to use containers for development on Linux. It automatically
maps credentials, sets up things such as the clipboard, and corrects permission
issues which arise from developing with containers natively.

## What this tool does
- Automatically maps ssh credentials into the container
- Automatically maps GPG
- Inspects the image for volumes and will correct any permission issues. For
example if you're using npm and you want the cache to be persisted between
restarts you can add the following to your image:
```dockerfile
VOLUME $HOME/.npm
```
Since docker will create the directory with root as the owner slipway will
correct it automatically.
- Detects X11 support and will map it into the container (clipboard
integration).
- Handles open calls (e.g., open in browser on the host) via unix sockets.
- Maps your `~/workspace` directory into the container (can be overriden).
- Sets the timezone to match the host
- Sets your git config to match the host
- Maps credentials files for certain package managers to the container (yarn,
cargo, etc).

## Requirements
- Linux OS
- Python 3.7+
- Docker or Podman (rootless only)

## Getting Started
Install slipway:
```sh
python3 -m pip install slipway
```

Run an example image:
```
slipway start aghost7/nodejs-dev:focal-carbon
```

## Configuration
The `start` command line options can be specified in a configuration file
under `~/.config/slipway.yaml`.
```yml
pull: true
pull_daily: true
runtime: podman
alias:
  devops:
    image: aghost7/devops:focal
    network: slirp4netns
    environment:
    - AWS_ACCESS_KEY_ID
```

You can then use your `devops` alias in place of the image name:
```bash
slipway start devops
```

## Optional GnuPG (GPG) Support
On your host, you will need to have gpg configured with the daemon running.
Slipway will detect that gpg is running and will automatically create a bind
mount (volume) to map the socket file into the container.

Enable gpg signing git commits:
```sh
git config --global commit.gpgSign true
```

If you want to always sign tags:
```sh
git config --global tag.forceSignAnnotated true
```

Since we want gnupg to be used from the terminal interface, we need to change
the configuration under `~/.gnupg/gpg.conf`:

```
use-agent
pinentry-mode loopback
```

## Using rootless containers
Slipway supports podman, which is an alternative implementation to docker that
has much better security. There are additional steps to setting this up, which
is why it isn't the default.

Start by installing [podman](https://podman.io/getting-started/installation).

Setup the registry configuration:
```bash
mkdir -p ~/.config/containers
echo 'unqualified-search-registries = ["docker.io"]' > ~/.config/containers/registries.conf
```

Install some additional dependencies:
```bash
sudo apt-get install -y fuse-overlayfs slirp4netns
```

Grant your user some [subuids][subuids]/[subgids][subgids]:
```bash
echo "$USER:100000:600000" | sudo tee -a /etc/subuid
echo "$USER:100000:600000" | sudo tee -a /etc/subgid
podman system migrate
```

And then you can run your containers with podman instead!
```bash
slipway start --runtime podman aghost7/nvim:bionic
```

[subuid]: https://www.man7.org/linux/man-pages/man5/subuid.5.html
[subgid]: https://www.man7.org/linux/man-pages/man5/subgid.5.html

### I can't use networking tools (nmap, traceroute, etc) with rootless containers
This is actually because slipway defaults to host-based networking. When using
rootless containers, you need to change the network used to `slirp4netns`.

```bash
slipway start --network slirp4netns aghost7/devops:focal
```

## Developing
Requirements:
- python 3
- poetry

Install dependencies:
```
poetry install
```

Run tests:
```
poetry run pytest
```
