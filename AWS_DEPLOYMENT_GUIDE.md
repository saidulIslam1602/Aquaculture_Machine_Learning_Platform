# =============================================================================
# AWS DEPLOYMENT GUIDE - AQUACULTURE PLATFORM CLOUD DEPLOYMENT
# =============================================================================
#
# WHAT IS THIS GUIDE?
# This guide walks through deploying the Aquaculture ML Platform to Amazon Web
# Services (AWS). Think of it as a "step-by-step recipe" for moving the platform
# from local development to production cloud infrastructure.
#
# WHAT IS AWS DEPLOYMENT?
# AWS deployment means running the platform on Amazon's cloud infrastructure:
# - Scalable: Automatically handle more users and data
# - Reliable: High availability with backup systems
# - Secure: Enterprise-grade security and compliance
# - Managed: AWS handles server maintenance and updates
# - Global: Deploy close to users worldwide
#
# WHY DEPLOY TO AWS?
# Moving to AWS provides several benefits:
# - Production Readiness: Handle real users and production workloads
# - Scalability: Grow from 10 to 10,000 users seamlessly
# - Reliability: 99.9%+ uptime with automatic failover
# - Security: Built-in security features and compliance certifications
# - Cost Efficiency: Pay only for resources used
# - Integration: Connect with other AWS services easily
#
# DEPLOYMENT OPTIONS EXPLAINED:
# - ECS (Elastic Container Service): Fully managed container orchestration
# - EC2 (Elastic Compute Cloud): Virtual servers with full control
# - App Runner: Simplified container deployment service
# - RDS (Relational Database Service): Managed PostgreSQL database
# - ElastiCache: Managed Redis for caching and sessions
#
# AUTHOR: DevOps Team
# VERSION: 1.0.0
# UPDATED: 2024-10-26
# =============================================================================

## 📋 Table of Contents
1. [Environment Files Structure](#environment-files-structure)
2. [Local Development](#local-development)
3. [AWS Deployment Options](#aws-deployment-options)
4. [Step-by-Step AWS Deployment](#step-by-step-aws-deployment)
5. [Production Checklist](#production-checklist)

---

## 🔧 Environment Files Structure

### Files You Need

**ONE .env file is required** - Located at the project root:

```
Aquaculture_Machine_Learning_Platform/
├── .env                          # Main environment configuration (DO NOT commit to git)
├── .env.example                  # Template for .env file (safe to commit)
└── docker-compose.yml           # Docker orchestration file
```

### Current .env File

Your `.env` file is already configured and contains:

- **Database Configuration**: PostgreSQL connection settings
- **Redis Configuration**: Cache and session storage
- **Kafka Configuration**: Message broker for events
- **Security Keys**: JWT tokens and encryption keys
- **API Settings**: Host, port, and CORS configuration
- **ML Model Settings**: Model paths and inference configuration

**✅ This is the ONLY environment file you need to manage!**

---

## 🖥️  Local Development (Current Setup)

### Access Your Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3001 | React web application |
| **API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | Service health status |

### Demo Credentials
```
Username: demo
Password: demo12345
```

### Start/Stop Services

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose build api frontend
docker compose up -d
```

---

## ☁️ AWS Deployment Options

### 🏗️ Understanding the Deployment Options

Each AWS deployment option serves different needs and technical requirements:

### Option 1: AWS ECS (Elastic Container Service) - **RECOMMENDED FOR PRODUCTION**
**What it is**: A fully managed container orchestration service that runs Docker containers
**Think of it as**: A "smart container manager" that automatically handles scaling and load balancing

- **Best for**: Production-grade applications that need to handle varying traffic
- **Key Benefits**: 
  - Automatic scaling based on demand
  - Built-in load balancing across multiple containers
  - Health monitoring and automatic container replacement
  - Integration with other AWS services (RDS, ElastiCache, etc.)
  - No server management required
- **Cost**: ~$50-200/month for small-medium workloads
- **Complexity**: Medium (requires understanding of containers and AWS services)

### Option 2: AWS EC2 with Docker Compose - **RECOMMENDED FOR GETTING STARTED**
**What it is**: Virtual servers where the platform runs using Docker Compose (same as local development)
**Think of it as**: Renting a "virtual computer" in the cloud and running the same setup as locally

- **Best for**: Quick deployment, learning AWS, full control over the environment
- **Key Benefits**:
  - Direct migration from local development setup
  - Full control over server configuration
  - Easier to troubleshoot and debug
  - Familiar Docker Compose commands
  - Lower learning curve
- **Cost**: ~$20-100/month for t3.medium instances
- **Complexity**: Low (similar to local development)

### Option 3: AWS App Runner - **SIMPLEST BUT LIMITED**
**What it is**: A service that automatically builds and runs containerized applications
**Think of it as**: "One-click deployment" service that handles everything automatically

- **Best for**: Simple web applications without complex infrastructure needs
- **Key Benefits**:
  - Easiest deployment (just provide source code)
  - Automatic scaling and load balancing
  - No infrastructure management
  - Built-in CI/CD pipeline
- **Limitations**: Less control, limited customization options
- **Cost**: Pay-per-use, ~$25-150/month
- **Complexity**: Very Low (almost no configuration required)

---

## 🚀 Step-by-Step AWS Deployment

### Method 1: AWS ECS (Recommended for Production)

#### 🔧 Prerequisites - Setting Up AWS Tools

Before deploying to AWS, these tools need to be installed and configured:

```bash
# Install AWS CLI (Command Line Interface)
# This tool allows interaction with AWS services from the terminal
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
# This connects the local machine to the AWS account
aws configure
# When prompted, enter:
# - AWS Access Key ID (from AWS IAM console)
# - AWS Secret Access Key (from AWS IAM console)  
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

**What these credentials do**: They authenticate the local machine with AWS so commands can create and manage cloud resources.

#### 1. 📦 Create ECR Repositories - Container Image Storage

**What is ECR?** Elastic Container Registry (ECR) is AWS's Docker image storage service.
**Think of it as**: A "container image warehouse" where Docker images are stored securely.

```bash
# Create repository for API service
# This creates a secure storage location for the backend API Docker images
aws ecr create-repository --repository-name aquaculture-api --region us-east-1

# Create repository for Frontend service  
# This creates a secure storage location for the React frontend Docker images
aws ecr create-repository --repository-name aquaculture-frontend --region us-east-1
```

**Why ECR is needed**: ECS needs to pull Docker images from somewhere. ECR provides secure, scalable image storage integrated with AWS services.

#### 2. Build and Push Docker Images
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag API image
docker build -f infrastructure/docker/Dockerfile.api -t aquaculture-api .
docker tag aquaculture-api:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aquaculture-api:latest

# Push API image
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aquaculture-api:latest

# Build and tag Frontend image
docker build -f infrastructure/docker/Dockerfile.frontend -t aquaculture-frontend .
docker tag aquaculture-frontend:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aquaculture-frontend:latest

# Push Frontend image
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aquaculture-frontend:latest
```

#### 3. Set Up RDS PostgreSQL
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier aquaculture-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username aquaculture \
    --master-user-password YOUR_SECURE_PASSWORD \
    --allocated-storage 20 \
    --publicly-accessible \
    --region us-east-1
```

#### 4. Set Up ElastiCache Redis
```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id aquaculture-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --region us-east-1
```

#### 5. Create ECS Cluster
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name aquaculture-cluster --region us-east-1
```

#### 6. Create Task Definitions and Services
Create `ecs-task-definition.json`:
```json
{
  "family": "aquaculture-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aquaculture-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://aquaculture:PASSWORD@RDS_ENDPOINT:5432/aquaculture_db"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://ELASTICACHE_ENDPOINT:6379/0"
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aquaculture-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register and deploy:
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS service
aws ecs create-service \
    --cluster aquaculture-cluster \
    --service-name aquaculture-api-service \
    --task-definition aquaculture-api \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

### Method 2: AWS EC2 with Docker Compose (Simpler)

#### 1. Launch EC2 Instance
```bash
# Launch t3.medium instance with Ubuntu
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxx \
    --subnet-id subnet-xxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Aquaculture-ML}]'
```

#### 2. SSH into Instance
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

#### 3. Install Docker
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 4. Deploy Application
```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/Aquaculture_Machine_Learning_Platform.git
cd Aquaculture_Machine_Learning_Platform

# Create .env file with production settings
nano .env
# Update DATABASE_URL, REDIS_URL, and security keys

# Start services
docker compose up -d

# Check status
docker compose ps
```

#### 5. Configure Security Group
Allow inbound traffic:
- **Port 8000**: API (from Application Load Balancer)
- **Port 3001**: Frontend (from Application Load Balancer)
- **Port 22**: SSH (from your IP only)

---

## ✅ Production Checklist

### Before Deploying to AWS

- [ ] **Update .env file with production values**
  ```bash
  # Generate secure keys
  openssl rand -base64 32  # For SECRET_KEY
  openssl rand -base64 32  # For JWT_SECRET
  ```

- [ ] **Set ENVIRONMENT=production** in .env

- [ ] **Update database credentials**
  - Use AWS RDS endpoint
  - Use strong passwords (20+ characters)

- [ ] **Update Redis URL**
  - Use AWS ElastiCache endpoint

- [ ] **Configure CORS_ORIGINS**
  - Update with your actual domain
  - Remove localhost URLs

- [ ] **Set up SSL/TLS certificates**
  - Use AWS Certificate Manager (ACM)
  - Configure HTTPS in Application Load Balancer

- [ ] **Enable monitoring**
  - CloudWatch Logs
  - CloudWatch Metrics
  - Set up alarms

- [ ] **Set up backups**
  - Enable RDS automated backups
  - Configure snapshot retention
  - Test restore procedures

- [ ] **Security hardening**
  - Enable AWS WAF
  - Configure VPC properly
  - Use AWS Secrets Manager for credentials
  - Enable encryption at rest and in transit

---

## 🔐 AWS Secrets Manager (Recommended)

Instead of hardcoding secrets in .env, use AWS Secrets Manager:

```bash
# Store database password
aws secretsmanager create-secret \
    --name aquaculture/database/password \
    --secret-string "YOUR_DB_PASSWORD"

# Store JWT secret
aws secretsmanager create-secret \
    --name aquaculture/jwt/secret \
    --secret-string "YOUR_JWT_SECRET"
```

Update your application to fetch secrets from AWS Secrets Manager.

---

## 📊 Cost Estimate (Monthly)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| **ECS Fargate** | 2 tasks (0.5 vCPU, 1GB) | $30 |
| **RDS PostgreSQL** | db.t3.micro | $15 |
| **ElastiCache Redis** | cache.t3.micro | $12 |
| **Application Load Balancer** | Standard | $18 |
| **Data Transfer** | ~50GB/month | $5 |
| **CloudWatch Logs** | 5GB/month | $3 |
| **ECR Storage** | 2GB images | $0.20 |
| **Total** | | **~$83/month** |

*Prices are approximate and vary by region*

---

## 🆘 Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs api
docker compose logs frontend

# Restart specific service
docker compose restart api
```

### Database connection issues
```bash
# Test database connection
docker exec -it aquaculture-api python -c "from services.api.core.database import engine; engine.connect()"
```

### Port conflicts
```bash
# Check what's using ports
sudo lsof -i :8000
sudo lsof -i :3001

# Stop conflicting services or change ports in docker-compose.yml
```

---

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS PostgreSQL](https://docs.aws.amazon.com/rds/postgresql/)
- [AWS ElastiCache Redis](https://docs.aws.amazon.com/elasticache/redis/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

## 🎯 Quick Start Summary

**Your application is ready to deploy!**

1. ✅ **Environment file**: `.env` is properly configured
2. ✅ **Docker setup**: All services containerized
3. ✅ **Local testing**: Running on http://localhost:3001
4. ✅ **Database**: PostgreSQL configured
5. ✅ **Cache**: Redis configured
6. ✅ **API**: FastAPI backend ready

**To deploy to AWS**: Follow Method 2 (EC2 + Docker Compose) for the simplest path, or Method 1 (ECS) for production-grade deployment.

**Support**: If you encounter issues, check the troubleshooting section or review container logs.

