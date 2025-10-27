# =============================================================================
# TERRAFORM OUTPUTS - INFRASTRUCTURE INFORMATION EXPORT
# =============================================================================
# Outputs export important information about created resources for use by:
# - Application deployment scripts
# - Other Terraform configurations
# - CI/CD pipelines
# - Monitoring and management tools
# - Development teams who need connection details
# 
# Outputs are organized by category for easy consumption:
# - Infrastructure info (VPC, subnets, account details)
# - Compute resources (EKS cluster, load balancer)
# - Databases and caches (connection strings, endpoints)
# - Storage and registries (S3 buckets, ECR repositories)
# - Security information (security groups, KMS keys)
# - Monitoring and logging (log groups, dashboards)

# =============================================================================
# INFRASTRUCTURE INFORMATION
# =============================================================================
# Basic information about the AWS environment and network setup

# AWS Account and Region Information
# Useful for scripts that need to know which account/region they're working with
output "account_info" {
  description = "AWS account and region information"
  value = {
    account_id = local.account_id  # AWS account ID where resources are deployed
    region     = local.region      # AWS region where resources are deployed
  }
}

# VPC Network Information
# Complete network topology information for applications and other infrastructure
output "vpc_info" {
  description = "VPC network information"
  value = {
    vpc_id     = module.vpc.vpc_id         # VPC ID for security group references
    cidr_block = module.vpc.vpc_cidr_block # VPC IP range for network planning
    
    # Public subnets (internet-facing resources like load balancers)
    public_subnets = {
      ids   = module.vpc.public_subnets              # Subnet IDs for resource placement
      cidrs = module.vpc.public_subnets_cidr_blocks  # IP ranges for network ACLs
    }
    
    # Private subnets (application servers, Kubernetes nodes)
    private_subnets = {
      ids   = module.vpc.private_subnets              # Subnet IDs for resource placement
      cidrs = module.vpc.private_subnets_cidr_blocks  # IP ranges for network ACLs
    }
    
    # Database subnets (isolated database resources)
    database_subnets = {
      ids   = module.vpc.database_subnets              # Subnet IDs for database placement
      cidrs = module.vpc.database_subnets_cidr_blocks  # IP ranges for database security
    }
    
    nat_gateway_ips = module.vpc.nat_public_ips  # NAT Gateway IPs for firewall rules
  }
}

# =============================================================================
# COMPUTE RESOURCES
# =============================================================================
# Information about Kubernetes cluster and load balancer for application deployment

# EKS Cluster Information
# Everything applications need to connect to and deploy on the Kubernetes cluster
output "eks_info" {
  description = "EKS cluster information"
  value = {
    cluster_name                = module.eks.cluster_name                 # Cluster name for kubectl commands
    cluster_endpoint           = module.eks.cluster_endpoint              # API server endpoint for kubectl
    cluster_version            = module.eks.cluster_version               # Kubernetes version
    cluster_security_group_id  = module.eks.cluster_security_group_id     # Security group for cluster access
    node_security_group_id     = module.eks.node_security_group_id        # Security group for worker nodes
    oidc_provider_arn          = module.eks.oidc_provider_arn             # For IAM roles for service accounts
    cluster_certificate_authority_data = module.eks.cluster_certificate_authority_data  # CA cert for secure connection
  }
}

output "load_balancer_info" {
  description = "Application Load Balancer information"
  value = {
    dns_name    = aws_lb.main.dns_name
    zone_id     = aws_lb.main.zone_id
    arn         = aws_lb.main.arn
    hosted_zone = aws_lb.main.zone_id
  }
}

# =============================================================================
# DATABASE AND CACHE INFORMATION
# =============================================================================
# Connection details for databases and caches (marked sensitive for security)

# PostgreSQL Database Information
# Everything applications need to connect to the primary database
output "database_info" {
  description = "RDS PostgreSQL database information"
  value = {
    endpoint                = module.rds.db_instance_endpoint          # Database connection endpoint
    port                   = module.rds.db_instance_port              # Database port (5432)
    database_name          = module.rds.db_instance_name              # Database name
    username               = module.rds.db_instance_username          # Master username
    identifier             = module.rds.db_instance_identifier        # AWS RDS identifier
    availability_zone      = module.rds.db_instance_availability_zone  # Primary AZ
    multi_az               = module.rds.db_instance_multi_az           # High availability status
    backup_retention_period = module.rds.db_instance_backup_retention_period  # Backup retention
    backup_window          = module.rds.db_instance_backup_window      # Backup time window
    maintenance_window     = module.rds.db_instance_maintenance_window # Maintenance time window
  }
  sensitive = true  # Hide from logs and console output for security
}

output "enterprise_database_info" {
  description = "Enterprise database information (SQL Server, Oracle)"
  value = {
    sqlserver = var.enable_enterprise_databases ? {
      endpoint          = aws_db_instance.sqlserver[0].endpoint
      port             = aws_db_instance.sqlserver[0].port
      username         = aws_db_instance.sqlserver[0].username
      identifier       = aws_db_instance.sqlserver[0].identifier
      availability_zone = aws_db_instance.sqlserver[0].availability_zone
      multi_az         = aws_db_instance.sqlserver[0].multi_az
    } : null
    oracle = var.enable_enterprise_databases && var.enable_oracle_database ? {
      # Oracle database outputs would go here when implemented
    } : null
  }
  sensitive = true
}

# Redis Cache Information
# Connection details for the Redis cache cluster
output "cache_info" {
  description = "ElastiCache Redis information"
  value = {
    primary_endpoint   = aws_elasticache_replication_group.redis.primary_endpoint_address  # Write endpoint
    reader_endpoint    = aws_elasticache_replication_group.redis.reader_endpoint_address   # Read endpoint
    port              = aws_elasticache_replication_group.redis.port                       # Redis port (6379)
    node_type         = aws_elasticache_replication_group.redis.node_type                  # Instance type
    num_cache_clusters = aws_elasticache_replication_group.redis.num_cache_clusters        # Number of nodes
    engine_version    = aws_elasticache_replication_group.redis.engine_version             # Redis version
  }
  sensitive = true  # Hide from logs and console output for security
}

# =============================================================================
# MESSAGING SYSTEM INFORMATION
# =============================================================================
# Connection details for the Kafka message streaming platform

# Kafka Cluster Information
# Everything applications need to connect to Kafka for real-time messaging
output "messaging_info" {
  description = "MSK Kafka cluster information"
  value = {
    cluster_name           = aws_msk_cluster.kafka.cluster_name            # Kafka cluster name
    bootstrap_brokers      = aws_msk_cluster.kafka.bootstrap_brokers       # Broker endpoints (plain)
    bootstrap_brokers_tls  = aws_msk_cluster.kafka.bootstrap_brokers_tls   # Broker endpoints (TLS)
    zookeeper_connect_string = aws_msk_cluster.kafka.zookeeper_connect_string  # Zookeeper connection
    kafka_version         = aws_msk_cluster.kafka.kafka_version            # Kafka version
    number_of_broker_nodes = aws_msk_cluster.kafka.number_of_broker_nodes  # Number of brokers
  }
  sensitive = true  # Hide from logs and console output for security
}

# ============================================================================
# STORAGE
# ============================================================================

output "storage_info" {
  description = "S3 bucket information"
  value = {
    models_bucket = {
      id     = aws_s3_bucket.models.id
      arn    = aws_s3_bucket.models.arn
      domain = aws_s3_bucket.models.bucket_domain_name
    }
    data_bucket = {
      id     = aws_s3_bucket.data.id
      arn    = aws_s3_bucket.data.arn
      domain = aws_s3_bucket.data.bucket_domain_name
    }
    alb_logs_bucket = {
      id     = aws_s3_bucket.alb_logs.id
      arn    = aws_s3_bucket.alb_logs.arn
      domain = aws_s3_bucket.alb_logs.bucket_domain_name
    }
  }
}

# ============================================================================
# CONTAINER REGISTRIES
# ============================================================================

output "container_registries" {
  description = "ECR repository information"
  value = var.create_ecr_repositories ? {
    api = {
      url = aws_ecr_repository.api[0].repository_url
      arn = aws_ecr_repository.api[0].arn
    }
    ml_service = {
      url = aws_ecr_repository.ml_service[0].repository_url
      arn = aws_ecr_repository.ml_service[0].arn
    }
    frontend = {
      url = aws_ecr_repository.frontend[0].repository_url
      arn = aws_ecr_repository.frontend[0].arn
    }
    worker = {
      url = aws_ecr_repository.worker[0].repository_url
      arn = aws_ecr_repository.worker[0].arn
    }
  } : {}
}

# ============================================================================
# SECURITY
# ============================================================================

output "security_groups" {
  description = "Security group IDs"
  value = {
    alb                    = aws_security_group.alb.id
    eks_additional         = aws_security_group.eks_additional.id
    rds                   = aws_security_group.rds.id
    redis                 = aws_security_group.redis.id
    kafka                 = aws_security_group.kafka.id
    vpc_endpoints         = aws_security_group.vpc_endpoints.id
    bastion               = var.create_bastion ? aws_security_group.bastion[0].id : null
    sqlserver             = var.enable_enterprise_databases ? aws_security_group.sqlserver[0].id : null
    oracle                = var.enable_enterprise_databases && var.enable_oracle_database ? aws_security_group.oracle[0].id : null
    ldap                  = var.enable_enterprise_auth ? aws_security_group.ldap[0].id : null
    enterprise_messaging  = var.enable_enterprise_messaging ? aws_security_group.enterprise_messaging[0].id : null
  }
}

output "enterprise_security_info" {
  description = "Enterprise security services information"
  value = {
    waf = var.enable_enterprise_security ? {
      web_acl_id  = aws_wafv2_web_acl.main[0].id
      web_acl_arn = aws_wafv2_web_acl.main[0].arn
    } : null
    guardduty = var.enable_enterprise_security ? {
      detector_id = aws_guardduty_detector.main[0].id
    } : null
    secrets_manager = var.enable_enterprise_auth ? {
      ldap_secret_arn  = aws_secretsmanager_secret.ldap_credentials[0].arn
      saml_secret_arn  = aws_secretsmanager_secret.saml_certificates[0].arn
    } : null
  }
}

output "enterprise_compliance_info" {
  description = "Enterprise compliance and governance information"
  value = {
    cloudtrail = var.enable_enterprise_compliance ? {
      trail_arn    = aws_cloudtrail.main[0].arn
      s3_bucket    = aws_s3_bucket.cloudtrail[0].bucket
    } : null
    config = var.enable_enterprise_compliance ? {
      recorder_name = aws_config_configuration_recorder.main[0].name
      s3_bucket     = aws_s3_bucket.config[0].bucket
    } : null
    xray = var.enable_enterprise_monitoring ? {
      sampling_rule_arn = aws_xray_sampling_rule.main[0].arn
    } : null
  }
}

output "kms_keys" {
  description = "KMS key information"
  value = {
    kafka = {
      id     = aws_kms_key.kafka.id
      arn    = aws_kms_key.kafka.arn
      alias  = aws_kms_alias.kafka.name
    }
    rds = {
      id     = aws_kms_key.rds.id
      arn    = aws_kms_key.rds.arn
      alias  = aws_kms_alias.rds.name
    }
    s3 = {
      id     = aws_kms_key.s3.id
      arn    = aws_kms_key.s3.arn
      alias  = aws_kms_alias.s3.name
    }
  }
}

# =============================================================================
# CONNECTION STRINGS - READY-TO-USE CONNECTION INFORMATION
# =============================================================================
# Pre-formatted connection strings that applications can use directly

# Application Connection Strings
# Ready-to-use connection strings for common application frameworks
output "connection_strings" {
  description = "Connection strings for applications"
  value = {
    # PostgreSQL connection string (format: postgresql://user@host:port/database)
    database = "postgresql://${module.rds.db_instance_username}@${module.rds.db_instance_endpoint}:${module.rds.db_instance_port}/${module.rds.db_instance_name}"
    
    # Redis connection string (format: redis://host:port)
    redis    = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}"
    
    # Kafka bootstrap brokers (TLS-encrypted endpoints)
    kafka    = aws_msk_cluster.kafka.bootstrap_brokers_tls
  }
  sensitive = true  # Hide from logs and console output for security
}

# =============================================================================
# KUBERNETES CONFIGURATION - CLUSTER ACCESS
# =============================================================================
# Information needed to connect to and manage the Kubernetes cluster

# kubectl Configuration Command
# Run this command to configure kubectl to access the EKS cluster
output "kubectl_config_command" {
  description = "Command to configure kubectl for EKS cluster"
  value       = "aws eks update-kubeconfig --region ${local.region} --name ${module.eks.cluster_name}"
}

# Kubernetes Configuration Details
# Detailed cluster information for programmatic access (CI/CD, automation)
output "kubeconfig" {
  description = "Kubernetes configuration for connecting to EKS cluster"
  value = {
    cluster_name                         = module.eks.cluster_name                    # Cluster name
    endpoint                            = module.eks.cluster_endpoint                # API server endpoint
    certificate_authority_data          = module.eks.cluster_certificate_authority_data  # CA certificate
    region                              = local.region                              # AWS region
    oidc_issuer_url                     = module.eks.cluster_oidc_issuer_url        # OIDC provider URL
  }
  sensitive = true  # Hide from logs and console output for security
}

# ============================================================================
# MONITORING
# ============================================================================

output "monitoring_info" {
  description = "Monitoring and logging information"
  value = {
    log_groups = {
      kafka       = aws_cloudwatch_log_group.kafka.name
      application = aws_cloudwatch_log_group.application.name
      ml_service  = aws_cloudwatch_log_group.ml_service.name
    }
    log_retention_days = local.log_retention_days
  }
}

# ============================================================================
# ENVIRONMENT INFORMATION
# ============================================================================

output "environment_config" {
  description = "Current environment configuration"
  value = {
    environment           = var.environment
    project_name         = var.project_name
    name_prefix          = local.name_prefix
    availability_zones   = local.azs
    multi_az_enabled     = local.config.enable_multi_az
    deletion_protection  = local.config.enable_deletion_protection
    monitoring_enabled   = local.monitoring_enabled
  }
}

# =============================================================================
# LEGACY OUTPUTS - BACKWARD COMPATIBILITY
# =============================================================================
# These outputs maintain compatibility with older scripts and applications
# They provide simple, single-value outputs for common connection endpoints
# Use the structured outputs above for new applications

# EKS Cluster Endpoint (Legacy)
# Simple cluster endpoint for older kubectl configurations
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint (legacy output)"
  value       = module.eks.cluster_endpoint
}

# RDS Database Endpoint (Legacy)
# Simple database endpoint for older application configurations
output "rds_endpoint" {
  description = "RDS endpoint (legacy output)"
  value       = module.rds.db_instance_endpoint
  sensitive   = true  # Hide from logs for security
}

# Redis Cache Endpoint (Legacy)
# Simple Redis endpoint for older application configurations
output "redis_endpoint" {
  description = "Redis endpoint (legacy output)"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true  # Hide from logs for security
}

# Kafka Bootstrap Brokers (Legacy)
# Simple Kafka brokers list for older application configurations
output "kafka_bootstrap_brokers" {
  description = "Kafka bootstrap brokers (legacy output)"
  value       = aws_msk_cluster.kafka.bootstrap_brokers_tls
  sensitive   = true  # Hide from logs for security
}
