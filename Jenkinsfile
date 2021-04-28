
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
        kubernetes {
            defaultContainer "python"
            yamlFile "JenkinsPod.yml"
        }
    }

    stages {
        stage("set status") {
            steps {
                setBuildStatus("Build started", "pending")
            }
        }
        stage("install poetry") {
            steps {
                sh "curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -"
                sh 'echo \'export PATH="$PATH:$HOME/.local/bin"\' >> ~/.profile'
                sh "poetry --version"
            }
        }
        stage("install dependencies") {
            steps {
                sh "poetry install"
            }
        }
        stage("run mypy") {
            steps {
                sh "poetry run mypy ."
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


