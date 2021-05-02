
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
                sh """
                    set -e
                    apt-get update
                    apt-get install -y python3 python3-virtualenv
                """
            }
        }
        stage("install poetry") {
            steps {
                sh """
                    set -e
                    export POETRY_HOME=/opt/poetry
                    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3 -
                    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry
                    poetry --version
                """
            }
        }
        stage("create test user") {
            steps {
                sh "adduser --uid 1000 --disabled-password --gecos '' test-user"
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
                    . /etc/os-release
                    echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/ /" > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
                    apt-get install -y gpg gpg-agent curl
                    curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/Release.key | apt-key add -
                    apt-get update
                    apt-get install -y podman
                    podman info
                '''
            }
        }
        stage("run podman tests") {
            steps {
                sh "sudo -u test-user poetry run pytest"
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


