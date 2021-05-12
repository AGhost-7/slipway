
void setBuildStatus(String message, String state) {
	// workaround for: https://issues.jenkins-ci.org/browse/JENKINS-54249
	withCredentials([string(credentialsId: 'github-status-access-token', variable: 'TOKEN')]) {
		sh """
			target_url=\"https://jenkins.jonathan-boudreau.com/blue/organizations/jenkins/slipway/detail/slipway/$BUILD_NUMBER/pipeline\"
			curl \
			\"https://api.github.com/repos/AGhost-7/slipway/statuses/$GIT_COMMIT\" \
			-H \"Authorization: token $TOKEN\" \
			-H \"Content-Type: application/json\" \
			-H \"Accept: application/vnd.github.v3+json\" \
			-XPOST \
			-d \"{\\\"description\\\": \\\"$message\\\", \\\"state\\\": \\\"$state\\\", \\\"context\\\": \\\"Jenkins\\\", \\\"target_url\\\": \\\"\$target_url\\\"}\"
			"""
	}
}

pipeline {
    agent {
        label 'ubuntu-vm'
    }

    stages {
        stage("set status") {
            steps {
                setBuildStatus("Build started", "pending")
            }
        }
        stage("install python") {
            steps {
                sh '''
                    set -ex
                    apt-get update
                    apt-get install -y python3 python3-virtualenv
                '''
            }
        }
        stage("install poetry") {
            steps {
                sh '''
                    set -ex
                    if ! command -v poetry; then
                        export POETRY_HOME=/opt/poetry
                        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3 -
                        ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry
                    fi
                    poetry --version
                '''
            }
        }
        stage("create test user") {
            steps {
                sh '''
                    if ! grep -q test-user /etc/passwd; then
                        adduser --uid 1000 --disabled-password --gecos '' test-user
                    fi
                '''
            }
        }
        stage("install dependencies") {
            steps {
                sh "su test-user -c 'poetry install'"
            }
        }
        stage("run mypy") {
            steps {
                sh "su test-user -c 'poetry run mypy .'"
            }
        }
        stage("run black") {
            steps {
                sh "su test-user -c 'poetry run black --check .'"
            }
        }
        stage("install podman") {
            steps {
                sh '''
                    set -ex
                    if ! command -v podman; then
                        . /etc/os-release
                        echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/ /" > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
                        apt-get install -y gpg gpg-agent curl
                        curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/Release.key | apt-key add -
                        apt-get update
                        apt-get install -y podman
                        sed -i 's/unqualified-search-registries.*/unqualified-search-registries = ["docker.io"]/' /etc/containers/registries.conf
                    fi
                    podman info
                '''
            }
        }
        stage("run podman tests") {
            steps {
                sh "sudo -u test-user poetry run pytest"
            }
        }
        stage("install docker") {
            steps {
                sh '''
                    mkdir -p /run/user/1000
                    chown 1000:1000 /run/user/1000
                    sudo -u test-user bash -c '
                        set -ex
                        export XDG_RUNTIME_DIR=/run/user/$UID
                        BIN_DIR="$HOME/.local/bin"
                        export PATH="$PATH:$BIN_DIR"
                        if ! command -v docker; then
                            STABLE_LATEST="20.10.6"
                            CHANNEL=stable
                            mkdir -p "$BIN_DIR"

                            RELEASE_URL="https://download.docker.com/linux/static/$CHANNEL/$(uname -m)/docker-${STABLE_LATEST}.tgz"
                            curl -L -o /tmp/docker.tgz "$RELEASE_URL"
                            tar xvf /tmp/docker.tgz -C "$BIN_DIR" --strip-components=1

                            RELEASE_ROOTLESS_URL="https://download.docker.com/linux/static/$CHANNEL/$(uname -m)/docker-rootless-extras-${STABLE_LATEST}.tgz"
                            curl -L -o /tmp/docker-rootless.tgz "$RELEASE_ROOTLESS_URL"
                            tar xvf /tmp/docker-rootless.tgz -C "$BIN_DIR" --strip-components=1

                            dockerd-rootless.sh --experimental & disown
                        fi
                        export DOCKER_HOST=unix:////run/user/$UID/docker.sock
                        docker info
                    '
                '''
            }
        }
        stage("run docker tests") {
            steps {
                sh '''
                    sudo -u test-user bash -c '
                        export TEST_RUNTIME=docker
                        export XDG_RUNTIME_DIR=/run/user/$UID
                        export PATH="$PATH:$HOME/.local/bin"
                        export DOCKER_HOST=unix:////run/user/$UID/docker.sock
                        poetry run pytest
                    '
                '''
            }
        }
    }

    post {
        success {
            setBuildStatus("Build succeeded", "success")
        }
        failure {
            setBuildStatus("Build failed", "failure")
        }
    }
}


