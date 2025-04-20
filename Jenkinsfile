pipeline {
    agent {
        docker { image 'ahmed377/jenkins-agent:v1' }
    }
    stages {
        stage('Test') {
            steps {
                script {
                    // تنفيذ الـ linting و unit tests باستخدام الأدوات اللي على الـ agent
                    sh 'pylint Temp/app_temp.py'
                }
            }
        }
    }
}
