pipeline {
    agent {
        docker { image 'ahmed377/jenkins-agent:v1' }
    }
    stages {
        stage('Lint && Test') {
            steps {
                script {
                    // تنفيذ الـ linting و unit tests باستخدام الأدوات اللي على الـ agent
                    sh 'pylint --persistent=n Temp/app_temp.py'
                    sh 'hadolint Temp/Dockerfile'
                    sh 'python -m unittest discover -s tests -p "test_app_temp.py"'
                }
            }
        }
    }
}
