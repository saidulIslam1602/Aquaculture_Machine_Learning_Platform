# Terraform Configuration for Aquaculture ML Platform
# Production-grade infrastructure as code

# Terraform configuration moved to versions.tf

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${local.name_prefix}-vpc"
  cidr = local.vpc_cidr
  
  azs             = local.azs
  private_subnets = local.private_subnet_cidrs
  public_subnets  = local.public_subnet_cidrs
  database_subnets = local.database_subnet_cidrs
  
  # Enable NAT Gateway for private subnets
  enable_nat_gateway = true
  single_nat_gateway = var.environment == "development"
  
  # Enable DNS
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # VPC Flow Logs for security
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = "${local.name_prefix}-eks"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Cluster endpoint access
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true
  
  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
  
  # Node groups
  eks_managed_node_groups = {
    # General purpose nodes
    general = {
      name           = "general-purpose"
      instance_types = [coalesce(var.force_instance_types.eks_nodes, local.config.eks_node_instance_type)]
      
      min_size     = local.config.eks_min_nodes
      max_size     = local.config.eks_max_nodes
      desired_size = local.config.eks_desired_nodes
      
      labels = {
        role = "general"
      }
      
      tags = {
        NodeGroup = "general-purpose"
      }
    }
    
    # GPU nodes for ML inference
    gpu = {
      name           = "gpu-inference"
      instance_types = ["g4dn.xlarge"]
      
      min_size     = 0
      max_size     = 5
      desired_size = 1
      
      labels = {
        role = "ml-inference"
        gpu  = "nvidia-t4"
      }
      
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NoSchedule"
      }]
      
      tags = {
        NodeGroup = "gpu-inference"
      }
    }
  }
  
  tags = {
    Name = "${var.project_name}-eks"
  }
}

# RDS PostgreSQL
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"
  
  identifier = "${local.name_prefix}-postgres"
  
  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = coalesce(var.force_instance_types.rds, local.config.rds_instance_class)
  
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_encrypted     = true
  
  db_name  = "aquaculture_db"
  username = "aquaculture_admin"
  port     = 5432
  
  # Multi-AZ for high availability
  multi_az               = local.config.enable_multi_az
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Backup configuration
  backup_retention_period = local.backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  
  # Performance Insights
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  
  # Deletion protection
  deletion_protection = coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  skip_final_snapshot = !coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  
  tags = {
    Name = "${var.project_name}-postgres"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.name_prefix}-redis"
  replication_group_description = "Redis cluster for caching"
  
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = coalesce(var.force_instance_types.redis, local.config.redis_node_type)
  number_cache_clusters = 2  # Primary + replica
  
  port                       = 6379
  parameter_group_name       = "default.redis7"
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  
  # Automatic failover
  automatic_failover_enabled = true
  multi_az_enabled          = local.config.enable_multi_az
  
  # Backup
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  
  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "${var.project_name}-redis"
  }
}

# MSK (Managed Kafka)
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "${local.name_prefix}-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3
  
  broker_node_group_info {
    instance_type   = coalesce(var.force_instance_types.kafka, local.config.kafka_instance_type)
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.kafka.id]
    
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }
  
  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
    encryption_at_rest_kms_key_arn = aws_kms_key.kafka.arn
  }
  
  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.kafka.name
      }
    }
  }
  
  tags = {
    Name = "${var.project_name}-kafka"
  }
}

# S3 Bucket for model storage
resource "aws_s3_bucket" "models" {
  bucket = "${local.name_prefix}-models-${random_string.bucket_suffix.result}"
  
  tags = {
    Name = "${var.project_name}-models"
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# ============================================================================
# ENTERPRISE SQL SERVER DATABASE (Optional)
# ============================================================================

# RDS SQL Server for Enterprise Applications
resource "aws_db_instance" "sqlserver" {
  count = var.enable_enterprise_databases ? 1 : 0
  
  identifier = "${local.name_prefix}-sqlserver"
  
  engine         = "sqlserver-ex"
  engine_version = "15.00.4236.7.v1"
  instance_class = coalesce(var.force_instance_types.sqlserver, local.config.sqlserver_instance_class)
  
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds.arn
  
  db_name  = null  # SQL Server doesn't use db_name parameter
  username = "sqladmin"
  port     = 1433
  
  # Multi-AZ for high availability
  multi_az               = local.config.enable_multi_az
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = var.enable_enterprise_databases ? [aws_security_group.sqlserver[0].id] : []
  
  # Backup configuration
  backup_retention_period = local.backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  
  # Performance Insights
  performance_insights_enabled = true
  
  # Deletion protection
  deletion_protection = coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  skip_final_snapshot = !coalesce(var.enable_deletion_protection, local.config.enable_deletion_protection)
  
  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-sqlserver"
    Database = "SQLServer"
  })
}

# Outputs moved to outputs.tf for better organization
