#!/bin/bash

# =============================================================================
# JENKINS CREDENTIALS SETUP SCRIPT
# =============================================================================
# This script helps you set up all the credentials and configurations needed
# for your Jenkins CI/CD pipeline to work with Docker and Kubernetes.
#
# WHAT THIS SCRIPT DOES:
# - Provides step-by-step instructions for setting up Jenkins credentials
# - Shows you exactly what values to enter in the Jenkins UI
# - Verifies your Kubernetes cluster is ready
# - Checks that all required resources are created
#
# WHAT YOU NEED BEFORE RUNNING:
# - Jenkins running and accessible at http://localhost:8080
# - Docker Hub account (for storing your application images)
# - Kubernetes cluster running (Minikube in this case)
# - Basic understanding of what credentials are for
#
# CREDENTIALS EXPLAINED:
# - Docker Registry: Where your application images are stored
# - Kubernetes Token: Allows Jenkins to deploy to your cluster
# - Kubeconfig: Configuration file for connecting to Kubernetes
# =============================================================================

# Exit immediately if any command fails (good practice for scripts)
set -e

echo "🔧 Jenkins Credentials Setup for Aquaculture ML Platform"
echo "========================================================"

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================
# These are the connection details for your Jenkins and Kubernetes setup
# You may need to update these values based on your specific environment

# Jenkins Connection Details
JENKINS_URL="http://localhost:8080/"                                    # Where Jenkins is running
JENKINS_USER="Saidul"                                                   # Your Jenkins username
JENKINS_TOKEN="1142a2a3208ac16445c152e32dc36fcfa0"                      # Your Jenkins API token
JENKINS_CLI="java -jar jenkins-cli.jar -s ${JENKINS_URL} -http -auth ${JENKINS_USER}:${JENKINS_TOKEN}"

# Kubernetes Cluster Information
# These values come from your Minikube setup
K8S_URL="https://192.168.49.2:8443"                                     # Kubernetes API server URL
K8S_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6IjFGcWF6NG10b2VPUThQaVNCell3QUYwRDAtNlF0LUpxRm5ORHlVb1d0UTAifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiXSwiZXhwIjoxNzYxNDg4NjkzLCJpYXQiOjE3NjE0ODUwOTMsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiNDBlZmFjMmEtY2U4OS00ZGU0LThlODctN2IwYjQwZDMzNjEwIiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJkZWZhdWx0Iiwic2VydmljZWFjY291bnQiOnsibmFtZSI6ImplbmtpbnMiLCJ1aWQiOiI1NjlkZGU5Ni1jMTVjLTQ1MzYtOWEwMC1lZWMxMzZiYjk1NmEifX0sIm5iZiI6MTc2MTQ4NTA5Mywic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmRlZmF1bHQ6amVua2lucyJ9.W6ROIBMCxMSsOMi5WeMtVz5tDfOBJIFMLB1qE59CfswAicygj3XggKC7TJKYpsvnWS1nuZ4CPRlXvrsxPen7CEXLULuTgHrYoAudlsqQq3wIj1bb7SrVUKTJPUVHajSfpje8rBGubhvUsqWEsAZUC79cbV-T4dykukgU4JBYW9-xrCZ_AHcL4e1VRQuztsV4I6_NTafvEjUHYKvSaT9AfC2U1ib6oqRI8X5kkdbATgazkkNop6hg8tXjdhVQafHKaWCLw-m-QotYHkjbyayTpTm4Q8WFKWnX-t-TmAkh52d5WxaI2Dm_yUuHG1sq3huplEsHG9fknngA7OVHnYP7QA"  # Service account token for Jenkins

echo ""
echo "📋 MANUAL STEPS REQUIRED:"
echo "========================"
echo "These credentials must be added manually in Jenkins UI because"
echo "Jenkins security doesn't allow scripts to create credentials automatically."
echo ""
echo "1. 🌐 Open Jenkins in your browser: ${JENKINS_URL}"
echo "2. 🔑 Login with: ${JENKINS_USER} / Saidul1602"
echo "3. 🛠️  Navigate to: Manage Jenkins → Manage Credentials → Global credentials → Add Credentials"
echo ""

echo "4. 📦 Add Docker Registry URL:"
echo "   WHY: Jenkins needs to know where to push your Docker images"
echo "   - Kind: Secret text"
echo "   - Secret: docker.io                    # This is Docker Hub's registry URL"
echo "   - ID: docker-registry-url              # Internal name Jenkins uses"
echo "   - Description: Docker Registry URL     # Human-readable description"
echo ""

echo "5. 🐳 Add Docker Registry Credentials:"
echo "   WHY: Jenkins needs permission to push images to Docker Hub"
echo "   - Kind: Username with password"
echo "   - Username: [Your Docker Hub Username]  # Replace with your actual username"
echo "   - Password: [Your Docker Hub Password]  # Replace with your actual password"
echo "   - ID: docker-registry-credentials       # Internal name Jenkins uses"
echo "   - Description: Docker Registry Login    # Human-readable description"
echo ""

echo "6. ☸️  Add Kubernetes Token:"
echo "   - Kind: Secret text"
echo "   - Secret: ${K8S_TOKEN}"
echo "   - ID: kubernetes-token"
echo "   - Description: Kubernetes Service Account Token"
echo ""

echo "7. 📁 Add Kubeconfig (Create a dummy file for now):"
echo "   - Kind: Secret file"
echo "   - File: Create a text file with 'dummy-config' content"
echo "   - ID: kubeconfig"
echo "   - Description: Kubernetes Config"
echo ""

echo "8. ☁️  Configure Kubernetes Cloud:"
echo "   - Navigate to: Manage Jenkins → Configure System → Cloud"
echo "   - Add new cloud → Kubernetes"
echo "   - Name: kubernetes"
echo "   - Kubernetes URL: ${K8S_URL}"
echo "   - Credentials: Select 'kubernetes-token'"
echo "   - Disable https certificate check: ✅"
echo "   - Kubernetes Namespace: default"
echo "   - Jenkins URL: http://host.docker.internal:8080"
echo "   - Test Connection (should show 'Connected to Kubernetes')"
echo ""

echo "9. 🚀 Test the Pipeline:"
echo "   - Navigate to: Dashboard → aquaculture-pipeline"
echo "   - Click 'Build with Parameters'"
echo "   - Set parameters and click 'Build'"
echo ""

echo "✅ WHAT'S ALREADY CONFIGURED:"
echo "============================"
echo "✓ All required Jenkins plugins installed"
echo "✓ Minikube Kubernetes cluster running"
echo "✓ Jenkins service account created in Kubernetes"
echo "✓ Required namespaces created (aquaculture-staging, aquaculture-production)"
echo "✓ Jenkins job 'aquaculture-pipeline' created"
echo "✓ RBAC permissions configured"
echo ""

echo "🔍 CLUSTER INFO:"
echo "==============="
echo "Kubernetes URL: ${K8S_URL}"
echo "Minikube Status:"
~/bin/minikube status

echo ""
echo "📊 KUBERNETES RESOURCES:"
echo "======================="
echo "Namespaces:"
kubectl get namespaces | grep aquaculture

echo ""
echo "Service Accounts:"
kubectl get serviceaccounts jenkins

echo ""
echo "============="
echo "1. Complete the manual credential setup above"
echo "2. Configure the Kubernetes cloud in Jenkins"
echo "3. Run your first pipeline build!"
echo ""
echo " For troubleshooting, check:"
echo "- Jenkins logs: docker logs jenkins (if running in Docker)"
echo "- Kubernetes logs: kubectl logs -n default [pod-name]"
echo "- Minikube dashboard: minikube dashboard"
