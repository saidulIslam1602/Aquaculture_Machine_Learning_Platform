# Kubernetes Infrastructure - Enhanced Structure

This directory contains the restructured Kubernetes manifests for the Aquaculture ML Platform, following industry best practices with Kustomize-based configuration management.

## 🏗️ Directory Structure

```
infrastructure/kubernetes-new/
├── base/                          # Base Kubernetes resources
│   ├── namespace.yaml             # Platform namespace definition
│   ├── api-service.yaml           # FastAPI backend service
│   ├── ml-service.yaml            # TensorFlow ML inference service  
│   ├── worker-service.yaml        # Celery background workers
│   ├── database.yaml              # PostgreSQL StatefulSet with monitoring
│   ├── redis.yaml                 # Redis cache and message broker
│   └── kustomization.yaml         # Base kustomization configuration
├── overlays/                      # Environment-specific configurations
│   ├── staging/                   # Staging environment
│   │   ├── kustomization.yaml     # Staging-specific settings
│   │   ├── postgresql.conf        # Development-optimized DB config
│   │   └── redis.conf             # Development-optimized cache config
│   └── production/                # Production environment
│       ├── kustomization.yaml     # Production-specific settings
│       ├── postgresql.conf        # Production-optimized DB config
│       └── redis.conf             # Production-optimized cache config
├── monitoring/                    # Monitoring and observability
│   ├── servicemonitor.yaml        # Prometheus service discovery
│   ├── prometheus-rules.yaml      # Alerting rules and thresholds
│   └── kustomization.yaml         # Monitoring resources
├── secrets/                       # Secret management templates
│   ├── README.md                  # Secret management guide
│   ├── api-secrets.yaml.template  # API service secret template
│   └── database-secrets.yaml.template # Database secret template
└── README.md                      # This file
```

## 🚀 Key Improvements

### 1. **Kustomize-Based Architecture**
- **Base Resources**: Common configurations shared across environments
- **Environment Overlays**: Staging and production-specific customizations
- **Declarative Management**: GitOps-ready configuration management
- **DRY Principle**: Eliminate configuration duplication

### 2. **Production-Grade Services**
- **High Availability**: Multi-replica deployments with pod anti-affinity
- **Resource Management**: Proper CPU/memory limits and requests
- **Health Checks**: Comprehensive liveness and readiness probes
- **Security Contexts**: Non-root containers with read-only filesystems
- **Service Accounts**: Proper RBAC with minimal permissions

### 3. **Comprehensive Monitoring**
- **Prometheus Integration**: ServiceMonitors for all components
- **Alert Rules**: 25+ production-grade alerting rules
- **Multi-Level Monitoring**: Infrastructure, application, and business metrics
- **Runbook Integration**: Alert annotations with troubleshooting guides

### 4. **Security Enhancements**
- **Secret Management**: Templates for external secret management
- **Network Policies**: (Future) Network segmentation and isolation
- **Pod Security**: SecurityContexts and SecurityPolicies
- **RBAC**: Service accounts with minimal required permissions

### 5. **Operational Excellence**
- **Persistent Storage**: StatefulSets for database and cache
- **Configuration Management**: ConfigMaps for all services
- **Resource Optimization**: Environment-specific resource tuning
- **Backup Integration**: Database backup and recovery support

## 📋 Prerequisites

### Required Tools
```bash
# Kubernetes cluster (v1.20+)
kubectl version --client

# Kustomize (v4.0+)  
kustomize version

# Helm (v3.0+) - for monitoring stack
helm version
```

### Monitoring Stack
```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

## 🔧 Deployment Guide

### 1. **Deploy Staging Environment**
```bash
# Deploy base + staging overlay
kubectl apply -k infrastructure/kubernetes-new/overlays/staging

# Verify deployment
kubectl get pods -n aquaculture-staging
kubectl get services -n aquaculture-staging
```

### 2. **Deploy Production Environment**
```bash
# Deploy base + production overlay
kubectl apply -k infrastructure/kubernetes-new/overlays/production

# Verify deployment
kubectl get pods -n aquaculture-production
kubectl get services -n aquaculture-production
```

### 3. **Deploy Monitoring**
```bash
# Deploy monitoring resources
kubectl apply -k infrastructure/kubernetes-new/monitoring

# Verify ServiceMonitors
kubectl get servicemonitor -n monitoring
kubectl get prometheusrule -n monitoring
```

## 🔐 Secret Management

### External Secrets Operator (Recommended)
```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Configure secret stores (Vault, AWS, etc.)
kubectl apply -f infrastructure/kubernetes-new/secrets/
```

### Manual Secret Creation (Development)
```bash
# Create secrets from templates
envsubst < infrastructure/kubernetes-new/secrets/api-secrets.yaml.template | kubectl apply -f -
envsubst < infrastructure/kubernetes-new/secrets/database-secrets.yaml.template | kubectl apply -f -
```

## 📊 Monitoring and Observability

### Prometheus Targets
The platform exposes metrics on the following endpoints:
- **API Service**: `:8000/metrics` - HTTP requests, business KPIs
- **ML Service**: `:8001/metrics` - Model inference, prediction latency
- **Worker Service**: `:8002/metrics` - Task processing, queue statistics
- **PostgreSQL**: `:9187/metrics` - Database performance, connections
- **Redis**: `:9121/metrics` - Cache hit rates, memory usage

### Alert Categories
- **Critical**: Service down, high error rates, resource exhaustion
- **Warning**: Performance degradation, capacity planning
- **Business**: Data quality issues, KPI thresholds

### Grafana Dashboards
Import dashboards for comprehensive visualization:
```bash
# Platform Overview Dashboard
# Database Performance Dashboard  
# ML Model Performance Dashboard
# Business Metrics Dashboard
```

## 🔄 Environment Differences

| Component | Staging | Production |
|-----------|---------|------------|
| **Replicas** | 1 per service | 2-3 per service |
| **Resources** | Reduced limits | Production-grade |
| **Storage** | 2-5GB | 20-100GB |
| **Monitoring** | Basic alerts | Full alerting |
| **Secrets** | Simple | External management |
| **Persistence** | Relaxed durability | High durability |

## 🚨 Migration from Old Structure

### Backup Current Deployment
```bash
# Export current resources
kubectl get all -n aquaculture-prod -o yaml > backup-resources.yaml
kubectl get configmap -n aquaculture-prod -o yaml > backup-configmaps.yaml
kubectl get secret -n aquaculture-prod -o yaml > backup-secrets.yaml
```

### Migration Steps
1. **Test in Staging**: Deploy new structure to staging environment
2. **Validate Configuration**: Ensure all services start correctly
3. **Database Migration**: Plan for data preservation during transition
4. **Rolling Update**: Use blue-green deployment for zero downtime
5. **Monitor Transition**: Watch metrics during migration

### Rollback Plan
```bash
# Quick rollback using backup
kubectl apply -f backup-resources.yaml
kubectl apply -f backup-configmaps.yaml
kubectl apply -f backup-secrets.yaml
```

## 🛠️ Customization Guide

### Adding New Services
1. Create base resource in `base/` directory
2. Add to `base/kustomization.yaml` resources list
3. Add environment-specific patches in overlays
4. Include monitoring configuration
5. Update this README

### Environment-Specific Configuration
```yaml
# In overlay kustomization.yaml
patches:
- target:
    kind: Deployment
    name: your-service
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 3
```

### Resource Scaling
```yaml
# Automatic scaling based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 📚 Additional Resources

- **Kustomize Documentation**: https://kustomize.io/
- **Kubernetes Best Practices**: https://kubernetes.io/docs/concepts/
- **Prometheus Operator**: https://prometheus-operator.dev/
- **External Secrets**: https://external-secrets.io/
- **Platform Runbooks**: https://docs.aquaculture.com/runbooks/

## 🤝 Contributing

When adding new resources or making changes:
1. Follow the established naming conventions
2. Include proper labels and annotations  
3. Add monitoring for new services
4. Update environment overlays as needed
5. Test in staging before production deployment
6. Update documentation

## 📞 Support

For issues with Kubernetes deployment:
- **Platform Team**: @platform-team
- **SRE Team**: @sre-team  
- **On-Call**: Use established escalation procedures

---

**Version**: 1.0.0 "Neptune"  
**Last Updated**: $(date)  
**Architecture**: Microservices on Kubernetes with Kustomize