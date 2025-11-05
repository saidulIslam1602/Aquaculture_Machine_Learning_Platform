# Deployment Secrets Setup Guide

This guide explains how to configure the required secrets in your GitHub repository to enable actual Kubernetes deployments instead of simulated ones.

## Overview

The CI/CD pipeline includes both staging and production deployment jobs that can operate in two modes:
- **Simulation Mode**: When secrets are not configured (default for demo purposes)
- **Real Deployment Mode**: When proper Kubernetes configurations are provided

## Required Secrets

### 1. Kubernetes Configuration Secrets

#### `KUBE_CONFIG_STAGING`
- **Purpose**: Kubernetes configuration for staging environment
- **Format**: Base64-encoded kubeconfig file content
- **Usage**: Used by staging deployment job when `github.ref == 'refs/heads/develop'`

#### `KUBE_CONFIG_PRODUCTION`
- **Purpose**: Kubernetes configuration for production environment  
- **Format**: Base64-encoded kubeconfig file content
- **Usage**: Used by production deployment job when `github.ref == 'refs/heads/main'`

### 2. Optional Notification Secrets

#### `SLACK_WEBHOOK_URL`
- **Purpose**: Slack webhook URL for deployment notifications
- **Format**: Full webhook URL (https://hooks.slack.com/services/...)
- **Usage**: Sends notifications about deployment status

## How to Configure Secrets

### Step 1: Obtain Kubernetes Configuration

#### For Azure Kubernetes Service (AKS)
```bash
# Login to Azure
az login

# Get AKS credentials
az aks get-credentials --resource-group <resource-group> --name <cluster-name>

# Encode kubeconfig for GitHub secret
cat ~/.kube/config | base64 -w 0
```

#### For Amazon EKS
```bash
# Configure AWS CLI
aws configure

# Update kubeconfig for EKS
aws eks update-kubeconfig --region <region> --name <cluster-name>

# Encode kubeconfig for GitHub secret
cat ~/.kube/config | base64 -w 0
```

#### For Google GKE
```bash
# Authenticate with Google Cloud
gcloud auth login

# Get GKE credentials
gcloud container clusters get-credentials <cluster-name> --zone <zone> --project <project-id>

# Encode kubeconfig for GitHub secret
cat ~/.kube/config | base64 -w 0
```

### Step 2: Add Secrets to GitHub Repository

1. Navigate to your GitHub repository
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `KUBE_CONFIG_STAGING` | Base64-encoded staging kubeconfig | Staging Kubernetes access |
| `KUBE_CONFIG_PRODUCTION` | Base64-encoded production kubeconfig | Production Kubernetes access |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | Deployment notifications |

### Step 3: Verify Secret Configuration

After adding secrets, the next pipeline run will:
- Check for secret availability
- Use real deployment mode if secrets are present
- Fall back to simulation mode if secrets are missing

## Environment-Specific Configurations

### Staging Environment
- **Branch Trigger**: `develop`
- **Namespace**: `aquaculture-staging`
- **Deployment Strategy**: Rolling update
- **Health Check**: `https://staging.example.com/health`

### Production Environment
- **Branch Trigger**: `main`
- **Namespace**: `aquaculture-prod`
- **Deployment Strategy**: Blue-Green deployment
- **Health Check**: Internal cluster health checks

## Security Best Practices

### 1. Least Privilege Access
Ensure kubeconfig has minimal required permissions:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: aquaculture-prod
  name: deployment-role
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["services", "pods"]
  verbs: ["get", "list", "patch"]
```

### 2. Secret Rotation
- Rotate kubeconfig secrets regularly (quarterly recommended)
- Use service accounts with limited scope
- Monitor secret usage in GitHub Actions logs

### 3. Environment Isolation
- Use separate clusters or namespaces for staging/production
- Implement network policies for traffic isolation
- Use different service accounts for each environment

## Troubleshooting

### Common Issues

#### 1. "kubeconfig: command not found"
**Solution**: Ensure kubectl is installed in the runner environment

#### 2. "Unable to connect to the server"
**Possible Causes**:
- Incorrect kubeconfig encoding
- Expired cluster credentials
- Network connectivity issues

**Solution**: Re-generate and re-encode kubeconfig

#### 3. "Insufficient permissions"
**Solution**: Verify RBAC permissions for the service account

### Debugging Steps

1. **Check Secret Availability**:
   ```bash
   # In GitHub Actions workflow
   echo "Checking secrets..."
   if [ -z "${{ secrets.KUBE_CONFIG_PRODUCTION }}" ]; then
     echo "KUBE_CONFIG_PRODUCTION not set"
   else
     echo "KUBE_CONFIG_PRODUCTION is configured"
   fi
   ```

2. **Validate Kubeconfig**:
   ```bash
   # Test kubeconfig locally before encoding
   kubectl config view
   kubectl cluster-info
   kubectl auth can-i create deployments --namespace=aquaculture-prod
   ```

3. **Monitor Deployment Logs**:
   - Check GitHub Actions logs for detailed error messages
   - Review Kubernetes events: `kubectl get events -n <namespace>`
   - Check pod logs: `kubectl logs -n <namespace> <pod-name>`

## Migration from Simulation to Real Deployment

When you're ready to move from simulation to real deployments:

1. Set up your Kubernetes clusters (staging and production)
2. Configure the required secrets as described above
3. Update the environment URLs in the workflow file:
   - Replace `https://staging.example.com` with your actual staging URL
   - Replace `https://api.example.com` with your actual production URL
4. Test with a staging deployment first
5. Monitor the deployment process and logs

## Support

For additional help with deployment setup:
- Review the [Kubernetes documentation](https://kubernetes.io/docs/)
- Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
- Consult your cloud provider's Kubernetes service documentation

## Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Infrastructure Setup](../infrastructure/README.md)
- [Monitoring and Observability](MONITORING.md)
