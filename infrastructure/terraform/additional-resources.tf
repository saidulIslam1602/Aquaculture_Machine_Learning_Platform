# Additional Resources
# Resources that were referenced but not defined in main.tf

# ============================================================================
# SUBNET GROUPS
# ============================================================================

# ElastiCache Subnet Group for Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-subnet-group"
    Type = "SubnetGroup"
  })
}

# ============================================================================
# KMS KEYS
# ============================================================================

# KMS Key for Kafka Encryption
resource "aws_kms_key" "kafka" {
  description             = "KMS key for Kafka encryption in ${var.environment}"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  
  policy = local.kms_key_policy
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-kafka-kms"
    Service = "Kafka"
  })
}

resource "aws_kms_alias" "kafka" {
  name          = "alias/${local.name_prefix}-kafka"
  target_key_id = aws_kms_key.kafka.key_id
}

# KMS Key for RDS Encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption in ${var.environment}"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  
  policy = local.kms_key_policy
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-rds-kms"
    Service = "RDS"
  })
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# KMS Key for S3 Encryption
resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 encryption in ${var.environment}"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  
  policy = local.kms_key_policy
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-s3-kms"
    Service = "S3"
  })
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${local.name_prefix}-s3"
  target_key_id = aws_kms_key.s3.key_id
}

# ============================================================================
# CLOUDWATCH LOG GROUPS
# ============================================================================

# CloudWatch Log Group for Kafka
resource "aws_cloudwatch_log_group" "kafka" {
  name              = "/aws/msk/${local.name_prefix}-kafka"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.s3.arn
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-kafka-logs"
    Service = "Kafka"
  })
}

# CloudWatch Log Group for Application Logs
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/${local.name_prefix}/application"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.s3.arn
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-application-logs"
    Service = "EKS"
  })
}

# CloudWatch Log Group for ML Service
resource "aws_cloudwatch_log_group" "ml_service" {
  name              = "/aws/eks/${local.name_prefix}/ml-service"
  retention_in_days = local.log_retention_days
  kms_key_id        = aws_kms_key.s3.arn
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-ml-service-logs"
    Service = "EKS"
  })
}

# ============================================================================
# APPLICATION LOAD BALANCER
# ============================================================================

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = local.config.enable_deletion_protection
  
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb"
    Type = "LoadBalancer"
  })
}

# S3 Bucket for ALB Access Logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${local.name_prefix}-alb-logs-${random_string.bucket_suffix.result}"
  force_destroy = var.environment != "production"
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-alb-logs"
    Service = "LoadBalancer"
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  rule {
    id     = "delete_old_logs"
    status = "Enabled"
    
    expiration {
      days = local.log_retention_days
    }
    
    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Random string for unique bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ============================================================================
# ENTERPRISE SECURITY SERVICES
# ============================================================================

# AWS WAF for Application Security
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_enterprise_security ? 1 : 0
  
  name  = "${local.name_prefix}-waf"
  scope = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    action {
      block {}
    }
    
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }
  
  # AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }
  
  # SQL Injection Protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-waf"
    Type = "Security"
  })
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "main" {
  count = var.enable_enterprise_security ? 1 : 0
  
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn
}

# GuardDuty for Threat Detection
resource "aws_guardduty_detector" "main" {
  count = var.enable_enterprise_security ? 1 : 0
  
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
  
  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-guardduty"
    Type = "Security"
  })
}

# AWS Secrets Manager for Enterprise Authentication
resource "aws_secretsmanager_secret" "ldap_credentials" {
  count = var.enable_enterprise_auth ? 1 : 0
  
  name        = "${local.name_prefix}-ldap-credentials"
  description = "LDAP authentication credentials for enterprise integration"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ldap-secret"
    Type = "Authentication"
  })
}

resource "aws_secretsmanager_secret" "saml_certificates" {
  count = var.enable_enterprise_auth ? 1 : 0
  
  name        = "${local.name_prefix}-saml-certificates"
  description = "SAML certificates for enterprise SSO integration"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-saml-secret"
    Type = "Authentication"
  })
}

# ============================================================================
# ENTERPRISE COMPLIANCE & GOVERNANCE
# ============================================================================

# S3 Bucket for AWS Config
resource "aws_s3_bucket" "config" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  bucket        = "${local.name_prefix}-config-${random_string.bucket_suffix.result}"
  force_destroy = var.environment != "production"
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-config"
    Service = "Compliance"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "config" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  bucket = aws_s3_bucket.config[0].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "config" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  bucket = aws_s3_bucket.config[0].id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for CloudTrail
resource "aws_s3_bucket" "cloudtrail" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  bucket        = "${local.name_prefix}-cloudtrail-${random_string.bucket_suffix.result}"
  force_destroy = var.environment != "production"
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-cloudtrail"
    Service = "Compliance"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  bucket = aws_s3_bucket.cloudtrail[0].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  bucket = aws_s3_bucket.cloudtrail[0].id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudTrail for Audit Logging
resource "aws_cloudtrail" "main" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  name           = "${local.name_prefix}-cloudtrail"
  s3_bucket_name = aws_s3_bucket.cloudtrail[0].bucket
  
  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []
    
    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.models.arn}/*"]
    }
  }
  
  insight_selector {
    insight_type = "ApiCallRateInsight"
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cloudtrail"
    Type = "Compliance"
  })
}

# IAM Role for AWS Config
resource "aws_iam_role" "config" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  name = "${local.name_prefix}-config-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-config-role"
    Type = "Compliance"
  })
}

resource "aws_iam_role_policy_attachment" "config" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  role       = aws_iam_role.config[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# AWS Config Configuration Recorder
resource "aws_config_configuration_recorder" "main" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  name     = "${local.name_prefix}-config-recorder"
  role_arn = aws_iam_role.config[0].arn
  
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
  
  depends_on = [aws_config_delivery_channel.main]
}

resource "aws_config_delivery_channel" "main" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  name           = "${local.name_prefix}-config-delivery-channel"
  s3_bucket_name = aws_s3_bucket.config[0].bucket
}

# ============================================================================
# ENTERPRISE MONITORING SERVICES
# ============================================================================

# X-Ray for Distributed Tracing
resource "aws_xray_sampling_rule" "main" {
  count = var.enable_enterprise_monitoring ? 1 : 0
  
  rule_name      = "${local.name_prefix}-sampling-rule"
  priority       = 9000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-xray-sampling"
    Type = "Monitoring"
  })
}

# Enhanced CloudWatch Log Groups for Enterprise Monitoring
resource "aws_cloudwatch_log_group" "enterprise_audit" {
  count = var.enable_enterprise_compliance ? 1 : 0
  
  name              = "/aws/enterprise/${local.name_prefix}/audit"
  retention_in_days = local.config.log_retention_days * 3  # Keep audit logs longer
  kms_key_id        = aws_kms_key.s3.arn
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-enterprise-audit-logs"
    Service = "Compliance"
  })
}

resource "aws_cloudwatch_log_group" "security_events" {
  count = var.enable_enterprise_security ? 1 : 0
  
  name              = "/aws/security/${local.name_prefix}/events"
  retention_in_days = local.config.log_retention_days * 2  # Keep security logs longer
  kms_key_id        = aws_kms_key.s3.arn
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-security-events-logs"
    Service = "Security"
  })
}

# ============================================================================
# ECR REPOSITORIES
# ============================================================================

# ECR Repository for API Service
resource "aws_ecr_repository" "api" {
  count = var.create_ecr_repositories ? 1 : 0
  
  name                 = "${var.project_name}/api"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.s3.arn
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-api-ecr"
    Service = "API"
  })
}

# ECR Repository for ML Service
resource "aws_ecr_repository" "ml_service" {
  count = var.create_ecr_repositories ? 1 : 0
  
  name                 = "${var.project_name}/ml-service"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.s3.arn
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-ml-service-ecr"
    Service = "MLService"
  })
}

# ECR Repository for Frontend
resource "aws_ecr_repository" "frontend" {
  count = var.create_ecr_repositories ? 1 : 0
  
  name                 = "${var.project_name}/frontend"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.s3.arn
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-frontend-ecr"
    Service = "Frontend"
  })
}

# ECR Repository for Worker Service
resource "aws_ecr_repository" "worker" {
  count = var.create_ecr_repositories ? 1 : 0
  
  name                 = "${var.project_name}/worker"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.s3.arn
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-worker-ecr"
    Service = "Worker"
  })
}

# ECR Lifecycle Policies
resource "aws_ecr_lifecycle_policy" "api" {
  count      = var.create_ecr_repositories ? 1 : 0
  repository = aws_ecr_repository.api[0].name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 development images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["dev", "staging"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Apply same lifecycle policy to all ECR repositories
resource "aws_ecr_lifecycle_policy" "ml_service" {
  count      = var.create_ecr_repositories ? 1 : 0
  repository = aws_ecr_repository.ml_service[0].name
  policy     = aws_ecr_lifecycle_policy.api[0].policy
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  count      = var.create_ecr_repositories ? 1 : 0
  repository = aws_ecr_repository.frontend[0].name
  policy     = aws_ecr_lifecycle_policy.api[0].policy
}

resource "aws_ecr_lifecycle_policy" "worker" {
  count      = var.create_ecr_repositories ? 1 : 0
  repository = aws_ecr_repository.worker[0].name
  policy     = aws_ecr_lifecycle_policy.api[0].policy
}

# ============================================================================
# S3 BUCKETS
# ============================================================================

# S3 Bucket for Data Storage
resource "aws_s3_bucket" "data" {
  bucket = "${local.name_prefix}-data-${random_string.bucket_suffix.result}"
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-data"
    Service = "DataStorage"
  })
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
