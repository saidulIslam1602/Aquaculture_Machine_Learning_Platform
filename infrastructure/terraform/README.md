# Aquaculture ML Platform - Terraform Infrastructure

This directory contains the Infrastructure as Code (IaC) for the Aquaculture ML Platform using Terraform. The infrastructure is designed to be production-ready, scalable, and follows AWS best practices.

## 🏗️ Architecture Overview

The infrastructure deploys the following AWS services:

- **VPC**: Multi-AZ Virtual Private Cloud with public/private subnets
- **EKS**: Managed Kubernetes cluster with auto-scaling node groups
- **RDS**: PostgreSQL database with Multi-AZ support
- **ElastiCache**: Redis cluster for caching and session storage
- **MSK**: Managed Kafka for event streaming
- **S3**: Object storage for models and data
- **ECR**: Container registries for Docker images
- **ALB**: Application Load Balancer with SSL termination
- **CloudWatch**: Comprehensive monitoring and alerting
- **KMS**: Encryption keys for data at rest

## 📁 File Structure

```
terraform/
├── main.tf                    # Main infrastructure resources
├── versions.tf               # Terraform and provider versions
├── variables.tf              # Input variables with validation
├── locals.tf                 # Local values and computed configurations
├── data.tf                   # Data sources
├── outputs.tf                # Output values
├── security-groups.tf        # Network security rules
├── additional-resources.tf   # Supporting resources (KMS, ECR, etc.)
├── monitoring.tf             # CloudWatch alarms and dashboards
├── terraform.tfvars.example  # Example variable values
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0 installed
3. **kubectl** for Kubernetes management
4. **S3 bucket** for Terraform state storage
5. **DynamoDB table** for state locking

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd infrastructure/terraform
   ```

2. **Create your variables file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your specific values
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan the deployment**:
   ```bash
   terraform plan
   ```

5. **Apply the infrastructure**:
   ```bash
   terraform apply
   ```

### Environment-Specific Deployments

The infrastructure supports three environments with different configurations:

#### Development
```hcl
environment = "development"
log_retention_days = 7
enable_deletion_protection = false
```

#### Staging
```hcl
environment = "staging"
log_retention_days = 14
enable_monitoring = true
```

#### Production
```hcl
environment = "production"
log_retention_days = 90
enable_deletion_protection = true
compliance_level = "high"
```

## 🔧 Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `aws_region` | AWS region for deployment | `us-east-1` |
| `environment` | Environment name | `production` |
| `project_name` | Project name for resources | `aquaculture-ml` |
| `owner_email` | Owner email for notifications | `admin@company.com` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` |
| `create_bastion` | Create bastion host | `false` |
| `enable_monitoring` | Enable CloudWatch monitoring | `true` |
| `log_retention_days` | Log retention period | `30` |

### Instance Type Overrides

You can override default instance types per environment:

```hcl
force_instance_types = {
  eks_nodes = "t3.xlarge"
  rds       = "db.r5.large"
  redis     = "cache.r5.large"
  kafka     = "kafka.m5.xlarge"
}
```

## 🔐 Security Features

### Network Security
- **VPC Flow Logs**: Network traffic monitoring
- **Security Groups**: Least-privilege access rules
- **Private Subnets**: Database and cache isolation
- **NAT Gateways**: Secure outbound internet access

### Data Encryption
- **KMS Keys**: Customer-managed encryption keys
- **Encryption at Rest**: All storage encrypted
- **Encryption in Transit**: TLS/SSL for all communications

### Access Control
- **IAM Roles**: Service-specific permissions
- **OIDC Provider**: EKS service account integration
- **Bastion Host**: Optional secure access point

## 📊 Monitoring and Alerting

### CloudWatch Alarms
- **EKS**: CPU and memory utilization
- **RDS**: CPU, connections, and storage
- **ElastiCache**: CPU and memory usage
- **ALB**: Response time and error rates
- **Kafka**: Disk usage monitoring

### SNS Notifications
- **Critical Alerts**: Immediate attention required
- **Warning Alerts**: Performance degradation
- **Email Subscriptions**: Automated notifications

### Dashboards
- **Infrastructure Overview**: Key metrics visualization
- **Service Health**: Real-time status monitoring

## 🔄 State Management

### Remote State Backend
```hcl
backend "s3" {
  bucket         = "aquaculture-terraform-state"
  key            = "prod/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

### State Locking
- **DynamoDB Table**: Prevents concurrent modifications
- **Encryption**: State files encrypted at rest
- **Versioning**: S3 bucket versioning enabled

## 📋 Outputs

After deployment, Terraform provides the following outputs:

### Connection Information
- **EKS Cluster**: Endpoint and authentication
- **RDS Database**: Connection string and endpoint
- **Redis Cache**: Primary and reader endpoints
- **Kafka**: Bootstrap brokers

### Infrastructure Details
- **VPC**: Network configuration
- **Security Groups**: Network access rules
- **Load Balancer**: DNS name and hosted zone
- **ECR Repositories**: Container registry URLs

## 🛠️ Operations

### Connecting to EKS
```bash
# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name aquaculture-ml-production-eks

# Verify connection
kubectl get nodes
```

### Database Access
```bash
# Through bastion host (if enabled)
ssh -i key.pem ec2-user@bastion-ip
psql -h rds-endpoint -U aquaculture_admin -d aquaculture_db
```

### Scaling Operations
```bash
# Scale EKS node groups
terraform apply -var="force_instance_types={eks_nodes=\"t3.2xlarge\"}"

# Update RDS instance class
terraform apply -var="force_instance_types={rds=\"db.r5.xlarge\"}"
```

## 🔍 Troubleshooting

### Common Issues

1. **State Lock Errors**:
   ```bash
   terraform force-unlock <lock-id>
   ```

2. **Resource Conflicts**:
   ```bash
   terraform import aws_resource.name resource-id
   ```

3. **Permission Errors**:
   - Verify AWS credentials
   - Check IAM permissions
   - Review resource policies

### Validation Commands
```bash
# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Security scan
terraform plan | grep -i security

# Cost estimation
terraform plan -out=plan.out
terraform show -json plan.out | jq '.resource_changes[].change.after'
```

## 📚 Best Practices

### Code Organization
- **Modular Structure**: Separate concerns into files
- **Variable Validation**: Input validation rules
- **Consistent Naming**: Standardized resource names
- **Comprehensive Tagging**: Resource identification

### Security
- **Least Privilege**: Minimal required permissions
- **Encryption Everywhere**: Data protection at rest and in transit
- **Network Isolation**: Private subnets for sensitive resources
- **Regular Updates**: Keep providers and modules current

### Operations
- **Environment Parity**: Consistent configurations across environments
- **Automated Testing**: Validate changes before deployment
- **Monitoring**: Comprehensive observability
- **Backup Strategy**: Regular data backups

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Code Standards
- Use `terraform fmt` for formatting
- Add variable descriptions and validation
- Update documentation for changes
- Follow naming conventions

## 📞 Support

For questions or issues:
- **Documentation**: Check this README and inline comments
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact the infrastructure team

## 📄 License

This infrastructure code is part of the Aquaculture ML Platform project.
See the main repository LICENSE file for details.

---

**Last Updated**: $(date)
**Terraform Version**: >= 1.5.0
**AWS Provider Version**: ~> 5.0
