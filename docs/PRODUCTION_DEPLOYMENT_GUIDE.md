# Production Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions for deploying the Aquaculture Machine Learning Platform to production environments on AWS, Azure, GCP, or multi-cloud setups.

## ✅ Pre-Deployment Checklist

### 1. Run Production Readiness Validation

```bash
# Validate production readiness
python scripts/production_readiness_check.py --environment production

# Check for any critical issues and resolve them
```

### 2. Set Up Production Secrets

```bash
# Generate and configure production secrets
./scripts/setup_production_secrets.sh production

# Verify secrets are properly configured
kubectl get secrets -n aquaculture-production
```

### 3. Database Setup

```bash
# Run database migrations
cd /home/saidul/Desktop/Aquaculture_Machine_Learning_Platform
source venv/bin/activate
alembic upgrade head

# Seed production data
python scripts/seed_production_data.py
```

## 🚀 Deployment Options

### Option 1: AWS EKS Deployment

#### Prerequisites
- AWS CLI configured with appropriate permissions
- kubectl installed and configured
- Terraform installed

#### Steps

1. **Deploy Infrastructure with Terraform**
```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review and customize variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your specific values

# Plan deployment
terraform plan

# Deploy infrastructure
terraform apply
```

2. **Configure kubectl for EKS**
```bash
aws eks update-kubeconfig --region us-east-1 --name aquaculture-production-cluster
```

3. **Deploy Application to Kubernetes**
```bash
cd infrastructure/kubernetes

# Apply base configuration
kubectl apply -k overlays/production

# Verify deployment
kubectl get pods -n aquaculture-production
kubectl get services -n aquaculture-production
```

4. **Configure Load Balancer and DNS**
```bash
# Get load balancer URL
kubectl get ingress -n aquaculture-production

# Configure your DNS to point to the load balancer
```

### Option 2: Docker Compose (Single Server)

#### Prerequisites
- Docker and Docker Compose installed
- Server with sufficient resources (8GB+ RAM, 4+ CPU cores)

#### Steps

1. **Prepare Environment**
```bash
# Copy environment template
cp env.example .env.production

# Edit .env.production with production values
nano .env.production
```

2. **Deploy with Docker Compose**
```bash
# Deploy production stack
docker-compose -f docker-compose.yml --env-file .env.production up -d

# Verify services
docker-compose ps
```

3. **Set Up SSL/TLS**
```bash
# Use Let's Encrypt with Certbot
sudo certbot --nginx -d your-domain.com
```

### Option 3: Multi-Cloud Deployment

#### Azure Deployment

1. **Set Up Azure Resources**
```bash
# Login to Azure
az login

# Create resource group
az group create --name aquaculture-production --location eastus

# Create AKS cluster
az aks create \
  --resource-group aquaculture-production \
  --name aquaculture-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

2. **Configure kubectl for AKS**
```bash
az aks get-credentials --resource-group aquaculture-production --name aquaculture-cluster
```

3. **Deploy Application**
```bash
# Update Kubernetes configs for Azure
kubectl apply -k infrastructure/kubernetes/overlays/azure-production
```

#### Google Cloud Platform (GCP) Deployment

1. **Set Up GCP Resources**
```bash
# Set project
gcloud config set project your-project-id

# Create GKE cluster
gcloud container clusters create aquaculture-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autorepair \
  --enable-autoupgrade
```

2. **Configure kubectl for GKE**
```bash
gcloud container clusters get-credentials aquaculture-cluster --zone us-central1-a
```

3. **Deploy Application**
```bash
kubectl apply -k infrastructure/kubernetes/overlays/gcp-production
```

## 🔧 Post-Deployment Configuration

### 1. Verify All Services

```bash
# Check service health
curl https://your-domain.com/health

# Check API documentation
curl https://your-domain.com/docs

# Test ML inference
curl -X POST https://your-domain.com/api/v1/ml/predict \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "..."}'
```

### 2. Configure Monitoring

```bash
# Access Grafana dashboard
kubectl port-forward svc/grafana 3000:3000 -n aquaculture-production

# Access Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n aquaculture-production
```

### 3. Set Up Backup and Recovery

```bash
# Database backup script
kubectl create cronjob db-backup \
  --image=postgres:13 \
  --schedule="0 2 * * *" \
  --restart=OnFailure \
  -- pg_dump -h postgres-service -U aquaculture aquaculture_db > /backup/db_$(date +%Y%m%d).sql
```

### 4. Configure Log Aggregation

```bash
# Deploy ELK stack (if not already deployed)
kubectl apply -f monitoring/elk/

# Configure log shipping
kubectl apply -f monitoring/elk/filebeat/
```

## 🔒 Security Hardening

### 1. Network Security

- Configure VPC/VNET with private subnets
- Set up security groups/NSGs to restrict access
- Enable WAF (Web Application Firewall)
- Configure DDoS protection

### 2. Application Security

```bash
# Rotate secrets regularly
./scripts/setup_production_secrets.sh production

# Update container images
kubectl set image deployment/api-service api=your-registry/api:v1.1.0 -n aquaculture-production

# Scan for vulnerabilities
docker scan your-registry/api:latest
```

### 3. Access Control

- Configure RBAC (Role-Based Access Control)
- Set up service accounts with minimal permissions
- Enable audit logging
- Configure MFA for admin access

## 📊 Monitoring and Alerting

### 1. Key Metrics to Monitor

- **Application Metrics:**
  - API response times
  - ML inference latency
  - Error rates
  - Request throughput

- **Infrastructure Metrics:**
  - CPU and memory usage
  - Disk space
  - Network I/O
  - Database performance

- **Business Metrics:**
  - Prediction accuracy
  - User activity
  - Model performance drift

### 2. Set Up Alerts

```yaml
# Example Prometheus alert rules
groups:
  - name: aquaculture-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: MLInferenceLatency
        expr: histogram_quantile(0.95, rate(ml_inference_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        annotations:
          summary: "ML inference latency is high"
```

## 🔄 Maintenance and Updates

### 1. Regular Maintenance Tasks

```bash
# Weekly tasks
- Review security logs
- Check system performance
- Verify backups
- Update dependencies

# Monthly tasks
- Rotate secrets
- Review access logs
- Update container images
- Performance optimization
```

### 2. Rolling Updates

```bash
# Update API service
kubectl set image deployment/api-service api=your-registry/api:v1.1.0 -n aquaculture-production

# Monitor rollout
kubectl rollout status deployment/api-service -n aquaculture-production

# Rollback if needed
kubectl rollout undo deployment/api-service -n aquaculture-production
```

### 3. ML Model Updates

```bash
# Deploy new model version
python scripts/enterprise_model_deployment.py \
  --model-path /path/to/new/model.pth \
  --version v2.0.0 \
  --enable-ab-testing \
  --traffic-split 0.1

# Monitor model performance
# Gradually increase traffic to new model
# Rollback if performance degrades
```

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Issues**
```bash
# Check database pod status
kubectl get pods -l app=postgres -n aquaculture-production

# Check database logs
kubectl logs -l app=postgres -n aquaculture-production

# Test database connectivity
kubectl exec -it deployment/api-service -n aquaculture-production -- python -c "
from services.api.core.database import get_db
db = next(get_db())
print('Database connection successful')
"
```

2. **ML Model Loading Issues**
```bash
# Check ML service logs
kubectl logs -l app=ml-service -n aquaculture-production

# Verify model registry connectivity
kubectl exec -it deployment/ml-service -n aquaculture-production -- python -c "
from services.ml_service.core.model_registry import model_registry
print(model_registry.list_available_models())
"
```

3. **High Memory Usage**
```bash
# Check resource usage
kubectl top pods -n aquaculture-production

# Scale up if needed
kubectl scale deployment api-service --replicas=5 -n aquaculture-production
```

### Emergency Procedures

1. **Service Outage**
```bash
# Check all services
kubectl get pods -n aquaculture-production

# Restart failed services
kubectl rollout restart deployment/api-service -n aquaculture-production

# Scale up critical services
kubectl scale deployment api-service --replicas=10 -n aquaculture-production
```

2. **Database Issues**
```bash
# Restore from backup
kubectl exec -it postgres-pod -- psql -U aquaculture -d aquaculture_db < /backup/latest.sql

# Check database integrity
kubectl exec -it postgres-pod -- pg_dump --schema-only -U aquaculture aquaculture_db
```

## 📞 Support and Contacts

### Emergency Contacts
- **DevOps Team:** devops@company.com
- **ML Engineering:** ml-eng@company.com
- **Database Admin:** dba@company.com

### Escalation Procedures
1. Check monitoring dashboards
2. Review recent deployments
3. Check system logs
4. Contact on-call engineer
5. Escalate to senior team if needed

### Documentation Links
- [API Documentation](https://your-domain.com/docs)
- [Monitoring Dashboard](https://grafana.your-domain.com)
- [System Architecture](./SETUP.md)
- [Development Guide](./DEVELOPMENT_ROADMAP.md)

---

## 🎉 Congratulations!

Your Aquaculture Machine Learning Platform is now deployed and ready for production use. Remember to:

- Monitor system health regularly
- Keep security patches up to date
- Review and optimize performance
- Maintain proper backups
- Follow incident response procedures

For additional support, refer to the troubleshooting section or contact the development team.
