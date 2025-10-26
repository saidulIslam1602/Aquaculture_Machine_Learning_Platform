# Local Values
# Define computed values and configurations used throughout the infrastructure

locals {
  # Common naming convention
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Account and region information
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  # Availability zones (use first 3 available)
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
  
  # Environment-specific configurations
        environment_config = {
          development = {
            # Development settings
            eks_node_instance_type = "t3.medium"
            eks_min_nodes         = 1
            eks_max_nodes         = 3
            eks_desired_nodes     = 2
            rds_instance_class    = "db.t3.micro"
            redis_node_type       = "cache.t3.micro"
            kafka_instance_type   = "kafka.t3.small"
            sqlserver_instance_class = "db.t3.micro"
            oracle_instance_class = "db.t3.small"
            enable_multi_az       = false
            enable_deletion_protection = false
            log_retention_days    = 7
          }
          staging = {
            # Staging settings
            eks_node_instance_type = "t3.large"
            eks_min_nodes         = 2
            eks_max_nodes         = 6
            eks_desired_nodes     = 3
            rds_instance_class    = "db.t3.small"
            redis_node_type       = "cache.t3.small"
            kafka_instance_type   = "kafka.t3.small"
            sqlserver_instance_class = "db.t3.small"
            oracle_instance_class = "db.t3.medium"
            enable_multi_az       = true
            enable_deletion_protection = false
            log_retention_days    = 30
          }
          production = {
            # Production settings
            eks_node_instance_type = "t3.xlarge"
            eks_min_nodes         = 3
            eks_max_nodes         = 10
            eks_desired_nodes     = 5
            rds_instance_class    = "db.t3.large"
            redis_node_type       = "cache.t3.medium"
            kafka_instance_type   = "kafka.m5.large"
            sqlserver_instance_class = "db.r5.large"
            oracle_instance_class = "db.r5.xlarge"
            enable_multi_az       = true
            enable_deletion_protection = true
            log_retention_days    = 90
          }
        }
  
  # Current environment configuration
  config = local.environment_config[var.environment]
  
  # Common tags applied to all resources
  common_tags = merge(var.additional_tags, {
    Project      = var.project_name
    Environment  = var.environment
    ManagedBy    = "Terraform"
    Owner        = var.owner_email
    CreatedAt    = timestamp()
    AccountId    = local.account_id
    Region       = local.region
  })
  
  # Network CIDR calculations
  vpc_cidr = var.vpc_cidr
  
  # Calculate subnet CIDRs automatically if not provided
  public_subnet_cidrs = length(var.public_subnet_cidrs) > 0 ? var.public_subnet_cidrs : [
    for i in range(length(local.azs)) : cidrsubnet(local.vpc_cidr, 8, i + 100)
  ]
  
  private_subnet_cidrs = length(var.private_subnet_cidrs) > 0 ? var.private_subnet_cidrs : [
    for i in range(length(local.azs)) : cidrsubnet(local.vpc_cidr, 8, i)
  ]
  
  database_subnet_cidrs = [
    for i in range(length(local.azs)) : cidrsubnet(local.vpc_cidr, 8, i + 200)
  ]
  
  # Security group rules for different services
  web_ingress_rules = [
    {
      description = "HTTP"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      description = "HTTPS"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
  
  # Monitoring configuration
  monitoring_enabled = var.environment == "production" ? true : var.enable_monitoring
  log_retention_days = var.environment == "production" ? 90 : 30
  
  # Backup configuration
  backup_retention_period = var.environment == "production" ? 30 : 7
  
  # KMS key policies
  kms_key_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key for encryption/decryption"
        Effect = "Allow"
        Principal = {
          Service = [
            "rds.amazonaws.com",
            "elasticache.amazonaws.com",
            "kafka.amazonaws.com",
            "s3.amazonaws.com"
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}
