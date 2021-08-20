#!/usr/bin/env bash

set -eo pipefail

read -p 'Version: ' version

poetry version "$version"
git add -A
git commit -m "Release prep $version"
git push origin HEAD
git tag "$version"
git push origin "$version"
poetry publish --build
