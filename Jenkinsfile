pipeline {
    agent {
        docker {
             image 'ahmed377/jenkins-agent:v1' 
             args '-v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker'
        }
    }

    environment{
            DOCKERHUB_CREDENTIALS = credentials('dockerhub') // Create in Jenkins credentials
            IMAGE_NAME = 'ahmed377/apptemp'
            IMAGE_TAG = 'V12'

    }
    stages {
            stage('Lint the code') {
            steps {
                script {
                    echo "Lint The Code Using Pylint"
                    def result = sh(script: 'pylint --exit-zero Temp/app_temp.py', returnStdout: true)
                    echo result
                    def match = result =~ /Your code has been rated at ([\d.]+)\/10/
                    if (match) {
                        def score = match[0][1].toFloat()
                        echo "Code Score: ${score}"
                        if (score < 7.0) {
                            error("Code quality score too low: ${score}/10")
                        }
                    }
                }
            }
        }
            
            stage('lint the Dockerfile'){
                steps{
                    echo "==========================================================================================="
                    echo "Lint The Dockerfile Using Hadolint"
                    sh 'hadolint Temp/Dockerfile'
                }
            }
            
            stage('Run Unit Tests'){
                steps{
                    echo "==========================================================================================="
                    echo "Run The Unit Tests Using unittest"
                    sh 'python -m unittest discover -s tests -p "text_app_temp.py"'
                }
            }
            stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Temp/Dockerfile Temp/
                sh 'docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest'
                sh 'docker images'
            }
        }

            stage('Push Docker Image'){
                steps{
                     script {
                    sh """
                    echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                    """
                }

                }
            }
    }
}
