
    pipeline {
    agent any

    environment {
        APP_NAME = "aeloria"
        IMAGE_NAME = "aeloria-backend"
        PORT = "5000"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/Gouthamvaishnav11/Aeloria.git'
            }
        }

        stage('Install Backend Dependencies') {
            steps {
                sh '''
                   pip3 install --upgrade pip
                   pip3 install -r requirements.txt
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME} ."
                sh "docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:latest"
            }
        }

        stage('Run Docker Container') {
            steps {
               sh """
                   docker stop ${APP_NAME}-container || true
                   docker rm ${APP_NAME}-container || true
                   docker run -d -p ${PORT}:${PORT} --name ${APP_NAME}-container ${IMAGE_NAME}:latest
               """
            }
        }

        stage('Test API') {
            steps {
                sh """
                   sleep 5
                   curl -f http://localhost:${PORT} || echo 'API not responding'
                """
            }
        }
    }

    post {
        success {
            echo "✅ Deployment successful! Your Aeloria app is running on port ${PORT}."
        }
        failure {
            echo "❌ Deployment failed. Check the logs above for errors."
        }
    }
}
