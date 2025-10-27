# =============================================================================
# LOCAL VALUES AND COMPUTED CONFIGURATIONS
# =============================================================================
# This file defines computed values that are calculated from variables and data sources.
# Locals help avoid repetition and create dynamic configurations based on environment.
# Think of locals as "calculated variables" that change based on your inputs.

locals {
  # =============================================================================
  # BASIC COMPUTED VALUES
  # =============================================================================
  
  # Common naming convention for all resources
  # Combines project name and environment (e.g., "aquaculture-ml-production")
  name_prefix = "${var.project_name}-${var.environment}"
  
  # AWS Account and Region Information
  # These are fetched dynamically from the current AWS session
  account_id = data.aws_caller_identity.current.account_id  # Your AWS account ID
  region     = data.aws_region.current.name                # Current AWS region
  
  # Availability Zones for High Availability
  # Uses the first 3 available zones in the region for redundancy
  # Most AWS services require at least 2 AZs, we use 3 for better resilience
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
  
  # =============================================================================
  # ENVIRONMENT-SPECIFIC CONFIGURATIONS
  # =============================================================================
  # This map defines different resource sizes and settings for each environment.
  # This allows the same code to create small dev environments and large prod ones.
  
  environment_config = {
          development = {
            # Development Environment - Optimized for cost, minimal resources
            # Perfect for testing and development work
            eks_node_instance_type = "t3.medium"     # Small Kubernetes nodes
            eks_min_nodes         = 1               # Minimum cluster size
            eks_max_nodes         = 3               # Maximum cluster size
            eks_desired_nodes     = 2               # Target cluster size
            rds_instance_class    = "db.t3.micro"   # Small database instance
            redis_node_type       = "cache.t3.micro" # Small cache instance
            kafka_instance_type   = "kafka.t3.small" # Small message broker
            sqlserver_instance_class = "db.t3.micro" # Small SQL Server
            oracle_instance_class = "db.t3.small"   # Small Oracle instance
            enable_multi_az       = false           # Single AZ to save cost
            enable_deletion_protection = false      # Allow easy cleanup
            log_retention_days    = 7               # Short log retention
          }
          staging = {
            # Staging Environment - Production-like but smaller scale
            # Used for final testing before production deployment
            eks_node_instance_type = "t3.large"      # Medium Kubernetes nodes
            eks_min_nodes         = 2               # Higher minimum for testing
            eks_max_nodes         = 6               # More capacity for load testing
            eks_desired_nodes     = 3               # Larger baseline cluster
            rds_instance_class    = "db.t3.small"   # Medium database instance
            redis_node_type       = "cache.t3.small" # Medium cache instance
            kafka_instance_type   = "kafka.t3.small" # Medium message broker
            sqlserver_instance_class = "db.t3.small" # Medium SQL Server
            oracle_instance_class = "db.t3.medium"  # Medium Oracle instance
            enable_multi_az       = true            # High availability testing
            enable_deletion_protection = false      # Allow cleanup after testing
            log_retention_days    = 30              # Medium log retention
          }
          production = {
            # Production Environment - Full scale, high availability, performance optimized
            # Designed to handle real user traffic and provide business continuity
            eks_node_instance_type = "t3.xlarge"     # Large Kubernetes nodes for performance
            eks_min_nodes         = 3               # High minimum for availability
            eks_max_nodes         = 10              # Large capacity for peak loads
            eks_desired_nodes     = 5               # Substantial baseline cluster
            rds_instance_class    = "db.t3.large"   # Large database for performance
            redis_node_type       = "cache.t3.medium" # Fast cache for low latency
            kafka_instance_type   = "kafka.m5.large" # High-performance message broker
            sqlserver_instance_class = "db.r5.large" # Memory-optimized SQL Server
            oracle_instance_class = "db.r5.xlarge"  # Large Oracle for enterprise workloads
            enable_multi_az       = true            # Full high availability
            enable_deletion_protection = true       # Prevent accidental deletion
            log_retention_days    = 90              # Long log retention for compliance
          }
        }
  
  # =============================================================================
  # ACTIVE CONFIGURATION SELECTION
  # =============================================================================
  # Selects the configuration for the current environment
  # This is how the same code adapts to different environment needs
  config = local.environment_config[var.environment]
  
  # =============================================================================
  # RESOURCE TAGGING STRATEGY
  # =============================================================================
  # Common tags applied to all AWS resources for organization and cost tracking
  # Tags help you understand what resources belong to what project and who owns them
  common_tags = merge(var.additional_tags, {
    Project      = var.project_name          # Which project this belongs to
    Environment  = var.environment           # Which environment (dev/staging/prod)
    ManagedBy    = "Terraform"               # How this resource was created
    Owner        = var.owner_email           # Who is responsible for this resource
    CreatedAt    = timestamp()               # When this resource was created
    AccountId    = local.account_id          # Which AWS account owns this
    Region       = local.region              # Which AWS region this is in
  })
  
  # =============================================================================
  # NETWORK IP ADDRESS CALCULATIONS
  # =============================================================================
  # Automatically calculates subnet IP ranges from the main VPC CIDR block
  # This ensures subnets don't overlap and are properly distributed across AZs
  
  vpc_cidr = var.vpc_cidr  # Main VPC IP range (e.g., 10.0.0.0/16)
  
  # Public Subnets (for load balancers, NAT gateways)
  # These subnets have internet access and are where public-facing resources go
  # IP range: 10.0.100.0/24, 10.0.101.0/24, 10.0.102.0/24
  public_subnet_cidrs = length(var.public_subnet_cidrs) > 0 ? var.public_subnet_cidrs : [
    for i in range(length(local.azs)) : cidrsubnet(local.vpc_cidr, 8, i + 100)
  ]
  
  # Private Subnets (for applications, Kubernetes nodes)
  # These subnets have no direct internet access, only through NAT gateways
  # IP range: 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24
  private_subnet_cidrs = length(var.private_subnet_cidrs) > 0 ? var.private_subnet_cidrs : [
    for i in range(length(local.azs)) : cidrsubnet(local.vpc_cidr, 8, i)
  ]
  
  # Database Subnets (for RDS, ElastiCache)
  # Isolated subnets for databases with no internet access at all
  # IP range: 10.0.200.0/24, 10.0.201.0/24, 10.0.202.0/24
  database_subnet_cidrs = [
    for i in range(length(local.azs)) : cidrsubnet(local.vpc_cidr, 8, i + 200)
  ]
  
  # =============================================================================
  # SECURITY GROUP RULES TEMPLATES
  # =============================================================================
  # Pre-defined security rules for common web services
  # These rules allow HTTP and HTTPS traffic from anywhere on the internet
  web_ingress_rules = [
    {
      description = "HTTP"                    # Standard web traffic
      from_port   = 80                       # HTTP port
      to_port     = 80
      protocol    = "tcp"                    # TCP protocol
      cidr_blocks = ["0.0.0.0/0"]           # Allow from anywhere
    },
    {
      description = "HTTPS"                  # Secure web traffic
      from_port   = 443                     # HTTPS port
      to_port     = 443
      protocol    = "tcp"                   # TCP protocol
      cidr_blocks = ["0.0.0.0/0"]          # Allow from anywhere
    }
  ]
  
  # =============================================================================
  # MONITORING AND BACKUP CONFIGURATIONS
  # =============================================================================
  # Dynamic settings that change based on environment importance
  
  # Monitoring is always enabled for production, optional for other environments
  monitoring_enabled = var.environment == "production" ? true : var.enable_monitoring
  
  # Log retention: Production keeps logs longer for compliance and troubleshooting
  log_retention_days = var.environment == "production" ? 90 : 30
  
  # Backup retention: Production keeps backups longer for data protection
  backup_retention_period = var.environment == "production" ? 30 : 7
  
  # =============================================================================
  # KMS ENCRYPTION KEY POLICY
  # =============================================================================
  # Defines who can use the encryption keys for securing data at rest
  # This policy allows AWS services to encrypt/decrypt data automatically
  kms_key_policy = jsonencode({
    Version = "2012-10-17"  # AWS policy language version
    Statement = [
      {
        # Allow full administrative access to the AWS account owner
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"  # Account root user
        }
        Action   = "kms:*"      # All KMS actions
        Resource = "*"          # All resources
      },
      {
        # Allow AWS services to use the key for encryption/decryption
        Sid    = "Allow use of the key for encryption/decryption"
        Effect = "Allow"
        Principal = {
          Service = [
            "rds.amazonaws.com",        # For database encryption
            "elasticache.amazonaws.com", # For cache encryption
            "kafka.amazonaws.com",      # For message encryption
            "s3.amazonaws.com"          # For file encryption
          ]
        }
        Action = [
          "kms:Encrypt",           # Encrypt data
          "kms:Decrypt",           # Decrypt data
          "kms:ReEncrypt*",        # Re-encrypt with different key
          "kms:GenerateDataKey*",  # Generate encryption keys
          "kms:DescribeKey"        # Get key information
        ]
        Resource = "*"  # Apply to all resources
      }
    ]
  })
}
