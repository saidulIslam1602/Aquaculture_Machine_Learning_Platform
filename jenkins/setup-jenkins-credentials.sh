#!/bin/bash

# Jenkins Credentials Setup Script
# This script helps configure all required credentials for the Aquaculture ML Platform pipeline

set -e

echo "🔧 Jenkins Credentials Setup for Aquaculture ML Platform"
echo "========================================================"

# Configuration
JENKINS_URL="http://localhost:8080/"
JENKINS_USER="Saidul"
JENKINS_TOKEN="1142a2a3208ac16445c152e32dc36fcfa0"
JENKINS_CLI="java -jar jenkins-cli.jar -s ${JENKINS_URL} -http -auth ${JENKINS_USER}:${JENKINS_TOKEN}"

# Kubernetes cluster info
K8S_URL="https://192.168.49.2:8443"
K8S_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6IjFGcWF6NG10b2VPUThQaVNCell3QUYwRDAtNlF0LUpxRm5ORHlVb1d0UTAifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiXSwiZXhwIjoxNzYxNDg4NjkzLCJpYXQiOjE3NjE0ODUwOTMsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiNDBlZmFjMmEtY2U4OS00ZGU0LThlODctN2IwYjQwZDMzNjEwIiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJkZWZhdWx0Iiwic2VydmljZWFjY291bnQiOnsibmFtZSI6ImplbmtpbnMiLCJ1aWQiOiI1NjlkZGU5Ni1jMTVjLTQ1MzYtOWEwMC1lZWMxMzZiYjk1NmEifX0sIm5iZiI6MTc2MTQ4NTA5Mywic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmRlZmF1bHQ6amVua2lucyJ9.W6ROIBMCxMSsOMi5WeMtVz5tDfOBJIFMLB1qE59CfswAicygj3XggKC7TJKYpsvnWS1nuZ4CPRlXvrsxPen7CEXLULuTgHrYoAudlsqQq3wIj1bb7SrVUKTJPUVHajSfpje8rBGubhvUsqWEsAZUC79cbV-T4dykukgU4JBYW9-xrCZ_AHcL4e1VRQuztsV4I6_NTafvEjUHYKvSaT9AfC2U1ib6oqRI8X5kkdbATgazkkNop6hg8tXjdhVQafHKaWCLw-m-QotYHkjbyayTpTm4Q8WFKWnX-t-TmAkh52d5WxaI2Dm_yUuHG1sq3huplEsHG9fknngA7OVHnYP7QA"

echo ""
echo "📋 MANUAL STEPS REQUIRED:"
echo "========================"
echo ""
echo "1. 🌐 Open Jenkins in your browser: ${JENKINS_URL}"
echo "2. 🔑 Login with: ${JENKINS_USER} / Saidul1602"
echo "3. 🛠️  Navigate to: Manage Jenkins → Manage Credentials → Global credentials → Add Credentials"
echo ""

echo "4. 📦 Add Docker Registry URL:"
echo "   - Kind: Secret text"
echo "   - Secret: docker.io"
echo "   - ID: docker-registry-url"
echo "   - Description: Docker Registry URL"
echo ""

echo "5. 🐳 Add Docker Registry Credentials:"
echo "   - Kind: Username with password"
echo "   - Username: [Your Docker Hub Username]"
echo "   - Password: [Your Docker Hub Password]"
echo "   - ID: docker-registry-credentials"
echo "   - Description: Docker Registry Login"
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
echo "🎯 NEXT STEPS:"
echo "============="
echo "1. Complete the manual credential setup above"
echo "2. Configure the Kubernetes cloud in Jenkins"
echo "3. Run your first pipeline build!"
echo ""
echo "📚 For troubleshooting, check:"
echo "- Jenkins logs: docker logs jenkins (if running in Docker)"
echo "- Kubernetes logs: kubectl logs -n default [pod-name]"
echo "- Minikube dashboard: minikube dashboard"
