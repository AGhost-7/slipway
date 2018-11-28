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
- Detects X11 support and will map it into the container
- Maps your `~/workspace` directory into the container (can be overriden).
- Sets the timezone to match the host
- Sets your gitignore to match the host

## Getting Started
Install slipway:
```sh
python3 -m pip install slipway
```

Run an example image:
```
slipway start aghost7/nodejs-dev:bionic-carbon
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

## Developing
Install pipenv:
```
python3 -m pip install --user --upgrade pipenv
```

Install dependencies and load virtualenv:
```
pipenv install --dev
pipenv shell
```

Run tests:
```
pytest --capture=no
```
