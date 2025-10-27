# =============================================================================
# MAIN INFRASTRUCTURE CONFIGURATION
# =============================================================================
# This is the main Terraform configuration file for the Aquaculture ML Platform.
# It defines all the core AWS infrastructure components needed to run the platform:
# - Virtual Private Cloud (VPC) for network isolation
# - Elastic Kubernetes Service (EKS) for container orchestration
# - Relational Database Service (RDS) for data storage
# - ElastiCache Redis for caching and session storage
# - Managed Streaming for Kafka (MSK) for real-time data processing
# - S3 buckets for file and model storage
# - Enterprise databases for legacy system integration

# Note: Terraform version requirements are defined in versions.tf

# =============================================================================
# AWS PROVIDER CONFIGURATION
# =============================================================================
# Configure the AWS provider with region and default tags
# The provider is how Terraform communicates with AWS APIs

provider "aws" {
  region = var.aws_region  # Deploy to the specified AWS region
  
  # Apply common tags to ALL AWS resources automatically
  # This ensures consistent tagging for cost tracking and resource management
  default_tags {
    tags = local.common_tags  # Tags defined in locals.tf
  }
}

# =============================================================================
# VIRTUAL PRIVATE CLOUD (VPC) - NETWORK FOUNDATION
# =============================================================================
# Creates an isolated network environment in AWS where all resources will live
# Think of VPC as your own private data center in the cloud

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"  # Use community-maintained VPC module
  version = "~> 5.0"                        # Use version 5.x (stable and well-tested)
  
  name = "${local.name_prefix}-vpc"  # VPC name: e.g., "aquaculture-ml-production-vpc"
  cidr = local.vpc_cidr               # IP address range for the entire VPC
  
  # Distribute subnets across multiple availability zones for high availability
  azs             = local.azs                    # Availability zones to use
  private_subnets = local.private_subnet_cidrs   # Subnets for internal resources (no direct internet)
  public_subnets  = local.public_subnet_cidrs    # Subnets for internet-facing resources
  database_subnets = local.database_subnet_cidrs # Isolated subnets for databases
  
  # NAT Gateway Configuration for Internet Access from Private Subnets
  # NAT gateways allow private resources to access the internet for updates, etc.
  enable_nat_gateway = true                              # Enable NAT for private subnet internet access
  single_nat_gateway = var.environment == "development"  # Use 1 NAT for dev (cost), multiple for prod (availability)
  
  # DNS Configuration - Required for EKS and other AWS services
  enable_dns_hostnames = true  # Allow resources to have DNS names
  enable_dns_support   = true  # Enable DNS resolution within VPC
  
  # VPC Flow Logs for Security Monitoring
  # Flow logs capture network traffic information for security analysis
  enable_flow_log                      = true  # Enable network traffic logging
  create_flow_log_cloudwatch_iam_role  = true  # Create IAM role for flow logs
  create_flow_log_cloudwatch_log_group = true  # Create CloudWatch log group
  
  tags = {
    Name = "${var.project_name}-vpc"  # Human-readable name for the VPC
  }
}

# =============================================================================
# ELASTIC KUBERNETES SERVICE (EKS) - CONTAINER ORCHESTRATION
# =============================================================================
# Creates a managed Kubernetes cluster for running containerized applications
# Kubernetes orchestrates containers, handles scaling, and manages deployments

module "eks" {
  source  = "terraform-aws-modules/eks/aws"  # Use community-maintained EKS module
  version = "~> 19.0"                       # Use version 19.x (supports latest EKS features)
  
  cluster_name    = "${local.name_prefix}-eks"  # Cluster name: e.g., "aquaculture-ml-production-eks"
  cluster_version = "1.28"                      # Kubernetes version (use recent stable version)
  
  # Network Configuration - Deploy cluster in private subnets for security
  vpc_id     = module.vpc.vpc_id           # VPC where cluster will be created
  subnet_ids = module.vpc.private_subnets  # Private subnets for worker nodes
  
  # Cluster API Endpoint Access Configuration
  # Controls who can access the Kubernetes API server
  cluster_endpoint_public_access  = true   # Allow access from internet (with restrictions)
  cluster_endpoint_private_access = true   # Allow access from within VPC
  
  # =============================================================================
  # EKS CLUSTER ADDONS - ESSENTIAL KUBERNETES COMPONENTS
  # =============================================================================
  # Addons are AWS-managed components that extend Kubernetes functionality
  
  cluster_addons = {
    # CoreDNS - DNS server for service discovery within the cluster
    # Allows pods to find each other by name (e.g., "api-service")
    coredns = {
      most_recent = true  # Always use the latest version for security
    }
    
    # Kube-proxy - Network proxy for Kubernetes services
    # Handles network routing between pods and services
    kube-proxy = {
      most_recent = true  # Always use the latest version
    }
    
    # VPC CNI - Container Network Interface for AWS VPC integration
    # Assigns VPC IP addresses directly to pods for better networking
    vpc-cni = {
      most_recent = true  # Always use the latest version
    }
    
    # EBS CSI Driver - Allows pods to use EBS volumes for persistent storage
    # Required for databases and applications that need persistent disk storage
    aws-ebs-csi-driver = {
      most_recent = true  # Always use the latest version
    }
  }
  
  # =============================================================================
  # EKS NODE GROUPS - COMPUTE RESOURCES FOR KUBERNETES
  # =============================================================================
  # Node groups are sets of EC2 instances that run your Kubernetes workloads
  # We create different node groups for different types of workloads
  
  eks_managed_node_groups = {
    # General Purpose Node Group - For most applications
    # These nodes run web applications, APIs, and general workloads
    general = {
      name           = "general-purpose"  # Human-readable name
      # Instance type: Use override if specified, otherwise use environment default
      instance_types = [coalesce(var.force_instance_types.eks_nodes, local.config.eks_node_instance_type)]
      
      # Auto Scaling Configuration - Automatically adjusts based on workload
      min_size     = local.config.eks_min_nodes      # Minimum nodes (cost control)
      max_size     = local.config.eks_max_nodes      # Maximum nodes (capacity limit)
      desired_size = local.config.eks_desired_nodes  # Target number of nodes
      
      # Node Labels - Used by Kubernetes scheduler to place workloads
      labels = {
        role = "general"  # Identifies this as a general-purpose node
      }
      
      tags = {
        NodeGroup = "general-purpose"  # Tag for cost tracking
      }
    }
    
    # GPU Node Group - For Machine Learning Inference
    # These nodes have NVIDIA GPUs for running ML models and AI workloads
    gpu = {
      name           = "gpu-inference"  # Human-readable name
      instance_types = ["g4dn.xlarge"]  # GPU instance type with NVIDIA T4 GPU
      
      # GPU Auto Scaling - Start with fewer nodes since GPUs are expensive
      min_size     = 0  # Can scale to zero when not needed (cost optimization)
      max_size     = 5  # Maximum GPU nodes for peak ML workloads
      desired_size = 1  # Start with 1 GPU node ready
      
      # Node Labels - Help Kubernetes identify GPU nodes
      labels = {
        role = "ml-inference"  # Identifies this as an ML inference node
        gpu  = "nvidia-t4"     # Specifies the GPU type available
      }
      
      # Node Taints - Prevent non-GPU workloads from being scheduled here
      # This ensures GPU nodes are reserved for ML workloads that actually need GPUs
      taints = [{
        key    = "nvidia.com/gpu"  # Standard GPU taint key
        value  = "true"            # Taint value
        effect = "NoSchedule"      # Prevent scheduling unless tolerated
      }]
      
      tags = {
        NodeGroup = "gpu-inference"  # Tag for cost tracking
      }
    }
  }
  
  # Tags for the EKS cluster itself
  tags = {
    Name = "${var.project_name}-eks"  # Human-readable cluster name
  }
}

# =============================================================================
# RDS POSTGRESQL DATABASE - PRIMARY DATA STORAGE
# =============================================================================
# Creates a managed PostgreSQL database for storing application data
# RDS handles backups, updates, monitoring, and high availability automatically

module "rds" {
  source  = "terraform-aws-modules/rds/aws"  # Use community-maintained RDS module
  version = "~> 6.0"                        # Use version 6.x (latest stable)
  
  identifier = "${local.name_prefix}-postgres"  # Database identifier in AWS
  
  # Database Engine Configuration
  engine               = "postgres"    # PostgreSQL database engine
  engine_version       = "15.4"        # Specific PostgreSQL version (stable)
  family               = "postgres15"  # Parameter group family
  major_engine_version = "15"          # Major version for option groups
  # Instance size: Use override if specified, otherwise use environment default
  instance_class       = coalesce(var.force_instance_types.rds, local.config.rds_instance_class)
  
  # Storage Configuration
  allocated_storage     = 100   # Initial storage size in GB
  max_allocated_storage = 500   # Maximum storage (auto-scaling enabled)
  storage_encrypted     = true  # Encrypt data at rest for security
  
  # Database Configuration
  db_name  = "aquaculture_db"    # Name of the database to create
  username = "aquaculture_admin" # Master username (password auto-generated)
  port     = 5432               # Standard PostgreSQL port
  
  # High Availability and Network Configuration
  multi_az               = local.config.enable_multi_az          # Deploy across multiple AZs for failover
  db_subnet_group_name   = module.vpc.database_subnet_group_name # Use isolated database subnets
  vpc_security_group_ids = [aws_security_group.rds.id]           # Apply database security group
  
  # Backup and Maintenance Configuration
  backup_retention_period = local.backup_retention_period  # How long to keep backups (days)
  backup_window          = "03:00-04:00"                   # When to perform daily backups (UTC)
  maintenance_window     = "Mon:04:00-Mon:05:00"           # When to perform maintenance (UTC)
  
  # Monitoring and Performance Configuration
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]  # Export logs to CloudWatch
  performance_insights_enabled    = true                       # Enable detailed performance monitoring
  
  # Data Protection Configuration
  # Prevents accidental deletion in production environments
  deletion_protection = coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  skip_final_snapshot = !coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  
  tags = {
    Name = "${var.project_name}-postgres"  # Human-readable database name
  }
}

# =============================================================================
# ELASTICACHE REDIS - HIGH-PERFORMANCE CACHING
# =============================================================================
# Creates a managed Redis cluster for caching and session storage
# Redis provides sub-millisecond response times for frequently accessed data

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.name_prefix}-redis"  # Redis cluster identifier
  replication_group_description = "Redis cluster for caching and session storage"
  
  # Redis Engine Configuration
  engine               = "redis"  # Redis engine
  engine_version       = "7.0"    # Redis version (latest stable)
  # Instance size: Use override if specified, otherwise use environment default
  node_type            = coalesce(var.force_instance_types.redis, local.config.redis_node_type)
  number_cache_clusters = 2        # Primary + 1 replica for high availability
  
  # Network Configuration
  port                       = 6379                                    # Standard Redis port
  parameter_group_name       = "default.redis7"                       # Redis 7.0 parameter group
  subnet_group_name          = aws_elasticache_subnet_group.redis.name # Use private subnets
  security_group_ids         = [aws_security_group.redis.id]           # Apply Redis security group
  
  # High Availability Configuration
  automatic_failover_enabled = true                        # Auto-failover to replica if primary fails
  multi_az_enabled          = local.config.enable_multi_az # Deploy across multiple AZs
  
  # Backup Configuration
  snapshot_retention_limit = 5             # Keep 5 daily snapshots
  snapshot_window         = "03:00-05:00"  # When to take snapshots (UTC)
  
  # Security Configuration
  at_rest_encryption_enabled = true  # Encrypt data stored on disk
  transit_encryption_enabled = true  # Encrypt data in transit
  
  tags = {
    Name = "${var.project_name}-redis"  # Human-readable Redis cluster name
  }
}

# =============================================================================
# MSK (MANAGED STREAMING FOR KAFKA) - REAL-TIME DATA PROCESSING
# =============================================================================
# Creates a managed Kafka cluster for real-time data streaming and event processing
# Kafka handles high-throughput data streams for ML pipelines and real-time analytics

resource "aws_msk_cluster" "kafka" {
  cluster_name           = "${local.name_prefix}-kafka"  # Kafka cluster identifier
  kafka_version          = "3.5.1"                      # Kafka version (stable)
  number_of_broker_nodes = 3                            # 3 brokers for high availability
  
  # Broker Configuration
  broker_node_group_info {
    # Instance size: Use override if specified, otherwise use environment default
    instance_type   = coalesce(var.force_instance_types.kafka, local.config.kafka_instance_type)
    client_subnets  = module.vpc.private_subnets  # Deploy in private subnets for security
    security_groups = [aws_security_group.kafka.id]  # Apply Kafka security group
    
    # Storage Configuration for Kafka Logs
    storage_info {
      ebs_storage_info {
        volume_size = 100  # 100 GB per broker for message storage
      }
    }
  }
  
  # Security and Encryption Configuration
  encryption_info {
    # Encrypt all data in transit
    encryption_in_transit {
      client_broker = "TLS"  # TLS encryption between clients and brokers
      in_cluster    = true   # TLS encryption between brokers
    }
    # Encrypt all data at rest using KMS
    encryption_at_rest_kms_key_arn = aws_kms_key.kafka.arn
  }
  
  # Logging Configuration
  logging_info {
    broker_logs {
      # Send Kafka broker logs to CloudWatch for monitoring
      cloudwatch_logs {
        enabled   = true                               # Enable CloudWatch logging
        log_group = aws_cloudwatch_log_group.kafka.name # Log group for Kafka logs
      }
    }
  }
  
  tags = {
    Name = "${var.project_name}-kafka"  # Human-readable Kafka cluster name
  }
}

# =============================================================================
# S3 BUCKET FOR ML MODEL STORAGE
# =============================================================================
# Creates an S3 bucket for storing machine learning models and artifacts
# S3 provides durable, scalable object storage for model files

resource "aws_s3_bucket" "models" {
  # Bucket name includes random suffix to ensure global uniqueness
  bucket = "${local.name_prefix}-models-${random_string.bucket_suffix.result}"
  
  tags = {
    Name = "${var.project_name}-models"  # Human-readable bucket name
  }
}

# Enable versioning for model files (keeps history of model versions)
resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  
  versioning_configuration {
    status = "Enabled"  # Keep multiple versions of model files
  }
}

# Encrypt all model files at rest for security
resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  
  rule {
    # Use KMS encryption for all objects in the bucket
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"          # Use KMS for encryption
      kms_master_key_id = aws_kms_key.s3.arn # Use our custom KMS key
    }
    bucket_key_enabled = true  # Reduce KMS costs by using bucket keys
  }
}

# =============================================================================
# ENTERPRISE SQL SERVER DATABASE (OPTIONAL)
# =============================================================================
# Creates an optional SQL Server database for enterprise applications
# This is only created if var.enable_enterprise_databases is true
# Useful for integrating with existing enterprise systems that require SQL Server

# RDS SQL Server for Enterprise Applications
resource "aws_db_instance" "sqlserver" {
  count = var.enable_enterprise_databases ? 1 : 0  # Only create if enterprise features enabled
  
  identifier = "${local.name_prefix}-sqlserver"  # Database identifier in AWS
  
  # SQL Server Engine Configuration
  engine         = "sqlserver-ex"         # SQL Server Express Edition (free tier)
  engine_version = "15.00.4236.7.v1"     # SQL Server 2019 version
  # Instance size: Use override if specified, otherwise use environment default
  instance_class = coalesce(var.force_instance_types.sqlserver, local.config.sqlserver_instance_class)
  
  # Storage Configuration
  allocated_storage     = 100                 # Initial storage size in GB
  max_allocated_storage = 500                 # Maximum storage (auto-scaling enabled)
  storage_encrypted     = true                # Encrypt data at rest for security
  kms_key_id           = aws_kms_key.rds.arn  # Use custom KMS key for encryption
  
  # Database Configuration
  db_name  = null        # SQL Server doesn't use db_name parameter (unlike PostgreSQL)
  username = "sqladmin"  # Master username for SQL Server
  port     = 1433        # Standard SQL Server port
  
  # High Availability and Network Configuration
  multi_az               = local.config.enable_multi_az          # Deploy across multiple AZs for failover
  db_subnet_group_name   = module.vpc.database_subnet_group_name # Use isolated database subnets
  # Apply SQL Server security group only if enterprise databases are enabled
  vpc_security_group_ids = var.enable_enterprise_databases ? [aws_security_group.sqlserver[0].id] : []
  
  # Backup and Maintenance Configuration
  backup_retention_period = local.backup_retention_period  # How long to keep backups (days)
  backup_window          = "03:00-04:00"                   # When to perform daily backups (UTC)
  maintenance_window     = "Mon:04:00-Mon:05:00"           # When to perform maintenance (UTC)
  
  # Monitoring Configuration
  performance_insights_enabled = true  # Enable detailed performance monitoring
  
  # Data Protection Configuration
  # Prevents accidental deletion in production environments
  deletion_protection = coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  skip_final_snapshot = !coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  
  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-sqlserver"  # Human-readable database name
    Database = "SQLServer"                       # Database type for filtering
  })
}

# =============================================================================
# INFRASTRUCTURE OUTPUTS
# =============================================================================
# All infrastructure outputs have been moved to outputs.tf for better organization
# Outputs provide information about created resources that other systems need
# Examples: database connection strings, cluster endpoints, load balancer URLs
