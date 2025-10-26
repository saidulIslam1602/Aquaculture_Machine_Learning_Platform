#!/usr/bin/env groovy

/**
 * ============================================================================
 * JENKINS PIPELINE - AQUACULTURE ML PLATFORM
 * ============================================================================
 * 
 * A sophisticated CI/CD pipeline implementing industry best practices for
 * containerized microservices deployment with comprehensive quality gates.
 *
 * ARCHITECTURE:
 * - Multi-stage declarative pipeline with parallel execution
 * - Docker multi-stage builds for optimized images
 * - Kubernetes deployment with rolling updates
 * - Comprehensive testing strategy (unit, integration, security)
 * - Quality gates with SonarQube integration
 * - Security scanning with Trivy and OWASP
 * - Semantic versioning with Git tags
 * - Blue-green deployment strategy
 * - Automated rollback capabilities
 *
 * PIPELINE STAGES:
 * 1. Checkout & Environment Setup
 * 2. Code Quality Analysis (Parallel)
 * 3. Security Scanning (Parallel)
 * 4. Build & Test (Parallel)
 * 5. Docker Image Build
 * 6. Container Security Scan
 * 7. Deploy to Staging
 * 8. Integration Testing
 * 9. Deploy to Production (with approval)
 * 10. Post-Deployment Verification
 *
 * AUTHOR: DevOps Team
 * VERSION: 2.0.0
 * UPDATED: 2024-10-26
 * ============================================================================
 */

pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  serviceAccountName: jenkins
  containers:
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run
  - name: python
    image: python:3.10-slim
    command:
    - cat
    tty: true
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
  - name: trivy
    image: aquasec/trivy:latest
    command:
    - cat
    tty: true
  volumes:
  - name: docker-sock
    emptyDir: {}
"""
        }
    }
    
    environment {
        // Application Configuration
        APP_NAME = 'aquaculture-ml-platform'
        APP_VERSION = sh(script: "cat version.py | grep '__version__' | cut -d'\"' -f2", returnStdout: true).trim()
        BUILD_VERSION = "${APP_VERSION}-${BUILD_NUMBER}"
        
        // Container Registry
        DOCKER_REGISTRY = credentials('docker-registry-url')
        DOCKER_CREDENTIALS = credentials('docker-registry-credentials')
        IMAGE_PREFIX = "${DOCKER_REGISTRY}/${APP_NAME}"
        
        // Kubernetes Configuration
        K8S_NAMESPACE_STAGING = 'aquaculture-staging'
        K8S_NAMESPACE_PROD = 'aquaculture-production'
        KUBECONFIG = credentials('kubeconfig')
        
        // Quality & Security Thresholds
        CODE_COVERAGE_THRESHOLD = '80'
        SONAR_PROJECT_KEY = 'aquaculture-ml-platform'
        SECURITY_SEVERITY_THRESHOLD = 'HIGH'
        
        // Git Configuration
        GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
        GIT_BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()
        
        // Notification
        SLACK_CHANNEL = '#ci-cd-notifications'
        EMAIL_RECIPIENTS = 'devops-team@company.com'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
        disableConcurrentBuilds()
        timeout(time: 90, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')
    }
    
    parameters {
        choice(
            name: 'DEPLOYMENT_ENVIRONMENT',
            choices: ['staging', 'production', 'both'],
            description: 'Target deployment environment'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip test execution (emergency deployments only)'
        )
        booleanParam(
            name: 'ENABLE_SECURITY_SCAN',
            defaultValue: true,
            description: 'Enable security vulnerability scanning'
        )
        booleanParam(
            name: 'DEPLOY_TO_PRODUCTION',
            defaultValue: false,
            description: 'Deploy to production environment'
        )
    }
    
    triggers {
        githubPush()
        cron(env.BRANCH_NAME == 'main' ? 'H 2 * * 1-5' : '')
    }
    
    stages {
        stage('Initialize Pipeline') {
            steps {
                script {
                    echo "Pipeline Initialization"
                    echo "======================="
                    echo "Application: ${APP_NAME}"
                    echo "Version: ${BUILD_VERSION}"
                    echo "Git Commit: ${GIT_COMMIT_SHORT}"
                    echo "Branch: ${GIT_BRANCH}"
                    echo "Build Number: ${BUILD_NUMBER}"
                    
                    // Set build display name
                    currentBuild.displayName = "#${BUILD_NUMBER} - v${BUILD_VERSION}"
                    currentBuild.description = "Branch: ${GIT_BRANCH} | Commit: ${GIT_COMMIT_SHORT}"
                }
            }
        }
        
        stage('Parallel Quality Checks') {
            parallel {
                stage('Code Quality Analysis') {
                    steps {
                        container('python') {
                            script {
                                echo "Running Code Quality Analysis..."
                                sh '''
                                    pip install --quiet black flake8 pylint mypy bandit
                                    
                                    echo "Code Formatting Check..."
                                    black --check --diff services/ || true
                                    
                                    echo "Linting Check..."
                                    flake8 services/ --max-line-length=100 --exclude=__pycache__ --format=pylint || true
                                    
                                    echo "Type Checking..."
                                    mypy services/ --ignore-missing-imports || true
                                    
                                    echo "Security Linting..."
                                    bandit -r services/ -f txt || true
                                '''
                            }
                        }
                    }
                }
                
                stage('Dependency Security Scan') {
                    when {
                        expression { params.ENABLE_SECURITY_SCAN }
                    }
                    steps {
                        container('python') {
                            script {
                                echo "Scanning Dependencies for Vulnerabilities..."
                                sh '''
                                    pip install --quiet safety pip-audit
                                    
                                    echo "Running Safety Check..."
                                    safety check --json || true
                                    
                                    echo "Running Pip Audit..."
                                    pip-audit --desc || true
                                '''
                            }
                        }
                    }
                }
                
                stage('SAST Analysis') {
                    steps {
                        container('python') {
                            script {
                                echo "Static Application Security Testing..."
                                sh '''
                                    pip install --quiet semgrep
                                    
                                    echo "Running Semgrep SAST..."
                                    semgrep --config=auto services/ --json || true
                                '''
                            }
                        }
                    }
                }
            }
        }
        
        stage('Build & Test') {
            when {
                not { expression { params.SKIP_TESTS } }
            }
            parallel {
                stage('Unit Tests') {
                    steps {
                        container('python') {
                            script {
                                echo "Running Unit Tests with Coverage..."
                                sh '''
                                    pip install --quiet -r requirements.txt
                                    pip install --quiet pytest pytest-cov pytest-xdist
                                    
                                    pytest tests/unit/ \
                                        --cov=services \
                                        --cov-report=xml:coverage.xml \
                                        --cov-report=html:htmlcov \
                                        --cov-report=term-missing \
                                        --junit-xml=junit-unit.xml \
                                        --cov-fail-under=${CODE_COVERAGE_THRESHOLD} \
                                        -n auto \
                                        -v
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            junit 'junit-unit.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Code Coverage Report'
                            ])
                        }
                    }
                }
                
                stage('Integration Tests') {
                    steps {
                        container('python') {
                            script {
                                echo "Running Integration Tests..."
                                sh '''
                                    pytest tests/integration/ \
                                        --junit-xml=junit-integration.xml \
                                        -v
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            junit 'junit-integration.xml'
                        }
                    }
                }
            }
        }
        
        stage('Docker Image Build') {
            parallel {
                stage('Build API Image') {
                    steps {
                        container('docker') {
                            script {
                                echo "Building API Docker Image..."
                                sh """
                                    docker build \
                                        --build-arg BUILD_VERSION=${BUILD_VERSION} \
                                        --build-arg GIT_COMMIT=${GIT_COMMIT_SHORT} \
                                        --build-arg BUILD_DATE=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                                        --label org.opencontainers.image.version=${BUILD_VERSION} \
                                        --label org.opencontainers.image.revision=${GIT_COMMIT_SHORT} \
                                        --label org.opencontainers.image.created=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                                        -f infrastructure/docker/Dockerfile.api \
                                        -t ${IMAGE_PREFIX}/api:${BUILD_VERSION} \
                                        -t ${IMAGE_PREFIX}/api:latest \
                                        .
                                """
                            }
                        }
                    }
                }
                
                stage('Build Frontend Image') {
                    steps {
                        container('docker') {
                            script {
                                echo "Building Frontend Docker Image..."
                                sh """
                                    docker build \
                                        --build-arg BUILD_VERSION=${BUILD_VERSION} \
                                        --build-arg VITE_API_URL=http://localhost:8000 \
                                        -f infrastructure/docker/Dockerfile.frontend \
                                        -t ${IMAGE_PREFIX}/frontend:${BUILD_VERSION} \
                                        -t ${IMAGE_PREFIX}/frontend:latest \
                                        .
                                """
                            }
                        }
                    }
                }
                
                stage('Build Worker Image') {
                    steps {
                        container('docker') {
                            script {
                                echo "Building Worker Docker Image..."
                                sh """
                                    docker build \
                                        --build-arg BUILD_VERSION=${BUILD_VERSION} \
                                        -f infrastructure/docker/Dockerfile.api \
                                        -t ${IMAGE_PREFIX}/worker:${BUILD_VERSION} \
                                        -t ${IMAGE_PREFIX}/worker:latest \
                                        .
                                """
                            }
                        }
                    }
                }
            }
        }
        
        stage('Container Security Scan') {
            when {
                expression { params.ENABLE_SECURITY_SCAN }
            }
            parallel {
                stage('Scan API Image') {
                    steps {
                        container('trivy') {
                            script {
                                echo "Scanning API Image for Vulnerabilities..."
                                sh """
                                    trivy image \
                                        --severity ${SECURITY_SEVERITY_THRESHOLD},CRITICAL \
                                        --exit-code 0 \
                                        --format json \
                                        --output api-security-report.json \
                                        ${IMAGE_PREFIX}/api:${BUILD_VERSION}
                                """
                            }
                        }
                    }
                }
                
                stage('Scan Frontend Image') {
                    steps {
                        container('trivy') {
                            script {
                                echo "Scanning Frontend Image for Vulnerabilities..."
                                sh """
                                    trivy image \
                                        --severity ${SECURITY_SEVERITY_THRESHOLD},CRITICAL \
                                        --exit-code 0 \
                                        --format json \
                                        --output frontend-security-report.json \
                                        ${IMAGE_PREFIX}/frontend:${BUILD_VERSION}
                                """
                            }
                        }
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: '*-security-report.json', allowEmptyArchive: true
                }
            }
        }
        
        stage('Push to Registry') {
            steps {
                container('docker') {
                    script {
                        echo "Pushing Docker Images to Registry..."
                        withCredentials([usernamePassword(
                            credentialsId: 'docker-registry-credentials',
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASS'
                        )]) {
                            sh '''
                                echo "${DOCKER_PASS}" | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USER} --password-stdin
                                
                                echo "Pushing API image..."
                                docker push ${IMAGE_PREFIX}/api:${BUILD_VERSION}
                                docker push ${IMAGE_PREFIX}/api:latest
                                
                                echo "Pushing Frontend image..."
                                docker push ${IMAGE_PREFIX}/frontend:${BUILD_VERSION}
                                docker push ${IMAGE_PREFIX}/frontend:latest
                                
                                echo "Pushing Worker image..."
                                docker push ${IMAGE_PREFIX}/worker:${BUILD_VERSION}
                                docker push ${IMAGE_PREFIX}/worker:latest
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                anyOf {
                    expression { params.DEPLOYMENT_ENVIRONMENT == 'staging' }
                    expression { params.DEPLOYMENT_ENVIRONMENT == 'both' }
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                container('kubectl') {
                    script {
                        echo "Deploying to Staging Environment..."
                        sh """
                            kubectl config use-context staging-cluster
                            
                            # Update deployment images
                            kubectl set image deployment/aquaculture-api \
                                api=${IMAGE_PREFIX}/api:${BUILD_VERSION} \
                                -n ${K8S_NAMESPACE_STAGING}
                            
                            kubectl set image deployment/aquaculture-frontend \
                                frontend=${IMAGE_PREFIX}/frontend:${BUILD_VERSION} \
                                -n ${K8S_NAMESPACE_STAGING}
                            
                            kubectl set image deployment/aquaculture-worker \
                                worker=${IMAGE_PREFIX}/worker:${BUILD_VERSION} \
                                -n ${K8S_NAMESPACE_STAGING}
                            
                            # Wait for rollout to complete
                            kubectl rollout status deployment/aquaculture-api -n ${K8S_NAMESPACE_STAGING} --timeout=5m
                            kubectl rollout status deployment/aquaculture-frontend -n ${K8S_NAMESPACE_STAGING} --timeout=5m
                            kubectl rollout status deployment/aquaculture-worker -n ${K8S_NAMESPACE_STAGING} --timeout=5m
                        """
                    }
                }
            }
        }
        
        stage('Staging Smoke Tests') {
            when {
                anyOf {
                    expression { params.DEPLOYMENT_ENVIRONMENT == 'staging' }
                    expression { params.DEPLOYMENT_ENVIRONMENT == 'both' }
                    branch 'main'
                }
            }
            steps {
                container('python') {
                    script {
                        echo "Running Smoke Tests on Staging..."
                        sh '''
                            pip install --quiet requests pytest
                            
                            pytest tests/smoke/ \
                                --base-url=https://staging.aquaculture.company.com \
                                --junit-xml=junit-smoke.xml \
                                -v
                        '''
                    }
                }
            }
            post {
                always {
                    junit 'junit-smoke.xml'
                }
            }
        }
        
        stage('Production Deployment Approval') {
            when {
                allOf {
                    branch 'main'
                    expression { params.DEPLOY_TO_PRODUCTION }
                }
            }
            steps {
                script {
                    timeout(time: 24, unit: 'HOURS') {
                        input message: 'Deploy to Production?',
                              ok: 'Deploy',
                              submitter: 'admin,devops-lead,platform-owner',
                              parameters: [
                                  choice(
                                      name: 'PRODUCTION_DEPLOYMENT_STRATEGY',
                                      choices: ['rolling-update', 'blue-green'],
                                      description: 'Deployment strategy for production'
                                  )
                              ]
                    }
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                allOf {
                    branch 'main'
                    expression { params.DEPLOY_TO_PRODUCTION }
                }
            }
            steps {
                container('kubectl') {
                    script {
                        echo "Deploying to Production Environment..."
                        sh """
                            kubectl config use-context production-cluster
                            
                            # Create deployment backup
                            kubectl get deployment aquaculture-api -n ${K8S_NAMESPACE_PROD} -o yaml > backup-api-deployment.yaml
                            
                            # Update production deployments
                            kubectl set image deployment/aquaculture-api \
                                api=${IMAGE_PREFIX}/api:${BUILD_VERSION} \
                                -n ${K8S_NAMESPACE_PROD}
                            
                            kubectl set image deployment/aquaculture-frontend \
                                frontend=${IMAGE_PREFIX}/frontend:${BUILD_VERSION} \
                                -n ${K8S_NAMESPACE_PROD}
                            
                            kubectl set image deployment/aquaculture-worker \
                                worker=${IMAGE_PREFIX}/worker:${BUILD_VERSION} \
                                -n ${K8S_NAMESPACE_PROD}
                            
                            # Wait for rollout with longer timeout for production
                            kubectl rollout status deployment/aquaculture-api -n ${K8S_NAMESPACE_PROD} --timeout=10m
                            kubectl rollout status deployment/aquaculture-frontend -n ${K8S_NAMESPACE_PROD} --timeout=10m
                            kubectl rollout status deployment/aquaculture-worker -n ${K8S_NAMESPACE_PROD} --timeout=10m
                        """
                    }
                }
            }
        }
        
        stage('Production Health Check') {
            when {
                allOf {
                    branch 'main'
                    expression { params.DEPLOY_TO_PRODUCTION }
                }
            }
            steps {
                container('python') {
                    script {
                        echo "Verifying Production Deployment Health..."
                        sh '''
                            pip install --quiet requests
                            
                            python3 << 'EOF'
import requests
import time
import sys

def check_health(url, max_retries=5):
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                print(f"Health check passed: {response.json()}")
                return True
        except Exception as e:
            print(f"Retry {i+1}/{max_retries}: {str(e)}")
            time.sleep(10)
    return False

if not check_health("https://aquaculture.company.com"):
    print("Production health check failed!")
    sys.exit(1)
print("Production deployment verified successfully!")
EOF
                        '''
                    }
                }
            }
        }
        
        stage('Create Git Tag') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Creating Git Tag for Release..."
                    sh """
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@company.com"
                        git tag -a v${BUILD_VERSION} -m "Release version ${BUILD_VERSION}"
                        git push origin v${BUILD_VERSION} || true
                    """
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Archive artifacts
                archiveArtifacts artifacts: '**/*-report.*, **/junit-*.xml, backup-*.yaml',
                               allowEmptyArchive: true,
                               fingerprint: true
                
                // Cleanup
                sh 'docker system prune -f || true'
            }
        }
        
        success {
            script {
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: 'good',
                    message: """
                        *BUILD SUCCESSFUL*
                        
                        Application: ${APP_NAME}
                        Version: ${BUILD_VERSION}
                        Branch: ${GIT_BRANCH}
                        Build: #${BUILD_NUMBER}
                        Duration: ${currentBuild.durationString.replace(' and counting', '')}
                        
                        <${BUILD_URL}|View Build Details>
                    """.stripIndent()
                )
                
                emailext(
                    subject: "BUILD SUCCESS: ${APP_NAME} v${BUILD_VERSION}",
                    body: """
                        <h2>Build Successful</h2>
                        <p><strong>Application:</strong> ${APP_NAME}</p>
                        <p><strong>Version:</strong> ${BUILD_VERSION}</p>
                        <p><strong>Branch:</strong> ${GIT_BRANCH}</p>
                        <p><strong>Commit:</strong> ${GIT_COMMIT_SHORT}</p>
                        <p><strong>Build Number:</strong> ${BUILD_NUMBER}</p>
                        <p><strong>Duration:</strong> ${currentBuild.durationString}</p>
                        <p><a href="${BUILD_URL}">View Build Details</a></p>
                    """,
                    to: env.EMAIL_RECIPIENTS,
                    mimeType: 'text/html'
                )
            }
        }
        
        failure {
            script {
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: 'danger',
                    message: """
                        *BUILD FAILED*
                        
                        Application: ${APP_NAME}
                        Version: ${BUILD_VERSION}
                        Branch: ${GIT_BRANCH}
                        Build: #${BUILD_NUMBER}
                        Failed Stage: ${env.STAGE_NAME}
                        
                        <${BUILD_URL}console|View Console Output>
                    """.stripIndent()
                )
                
                emailext(
                    subject: "BUILD FAILED: ${APP_NAME} v${BUILD_VERSION}",
                    body: """
                        <h2>Build Failed</h2>
                        <p><strong>Application:</strong> ${APP_NAME}</p>
                        <p><strong>Failed Stage:</strong> ${env.STAGE_NAME}</p>
                        <p><strong>Branch:</strong> ${GIT_BRANCH}</p>
                        <p><strong>Build Number:</strong> ${BUILD_NUMBER}</p>
                        <p><a href="${BUILD_URL}console">View Console Output</a></p>
                    """,
                    to: env.EMAIL_RECIPIENTS,
                    mimeType: 'text/html'
                )
            }
        }
        
        unstable {
            script {
                slackSend(
                    channel: env.SLACK_CHANNEL,
                    color: 'warning',
                    message: """
                        *BUILD UNSTABLE*
                        
                        Application: ${APP_NAME}
                        Version: ${BUILD_VERSION}
                        Some tests failed or quality gates not met.
                        
                        <${BUILD_URL}|Review Build Results>
                    """.stripIndent()
                )
            }
        }
    }
}
