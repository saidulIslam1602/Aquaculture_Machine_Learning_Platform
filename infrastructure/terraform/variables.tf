# Terraform Variables
# Define all configurable parameters with validation and descriptions

# ============================================================================
# BASIC CONFIGURATION
# ============================================================================

variable "aws_region" {
  description = "AWS region for deploying resources"
  type        = string
  default     = "us-east-1"
  
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be in format: us-east-1, eu-west-1, etc."
  }
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "aquaculture-ml"
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.project_name))
    error_message = "Project name must start with letter, contain only lowercase letters, numbers, and hyphens, and end with alphanumeric character."
  }
  
  validation {
    condition     = length(var.project_name) >= 3 && length(var.project_name) <= 50
    error_message = "Project name must be between 3 and 50 characters."
  }
}

variable "owner_email" {
  description = "Owner email address for resource tagging and notifications"
  type        = string
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.owner_email))
    error_message = "Owner email must be a valid email address."
  }
}

# ============================================================================
# NETWORKING CONFIGURATION
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones to use (leave empty to use all available)"
  type        = list(string)
  default     = []
  
  validation {
    condition     = length(var.availability_zones) == 0 || length(var.availability_zones) >= 2
    error_message = "Must specify at least 2 availability zones or leave empty for auto-selection."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (leave empty for auto-calculation)"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for cidr in var.private_subnet_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All private subnet CIDRs must be valid IPv4 CIDR blocks."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (leave empty for auto-calculation)"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for cidr in var.public_subnet_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All public subnet CIDRs must be valid IPv4 CIDR blocks."
  }
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

variable "create_bastion" {
  description = "Whether to create a bastion host for secure access"
  type        = bool
  default     = false
}

variable "bastion_allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access bastion host via SSH"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for cidr in var.bastion_allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All bastion allowed CIDR blocks must be valid IPv4 CIDR blocks."
  }
}

# ============================================================================
# MONITORING AND LOGGING
# ============================================================================

variable "enable_monitoring" {
  description = "Enable detailed monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be one of the valid CloudWatch log retention periods."
  }
}

# ============================================================================
# RESOURCE SIZING
# ============================================================================

variable "force_instance_types" {
  description = "Force specific instance types (overrides environment defaults)"
  type = object({
    eks_nodes = optional(string)
    rds       = optional(string)
    redis     = optional(string)
    kafka     = optional(string)
    sqlserver = optional(string)
    oracle    = optional(string)
  })
  default = {}
  
  validation {
    condition = alltrue([
      for k, v in var.force_instance_types : v == null || can(regex("^[a-z0-9]+\\.[a-z0-9]+$", v))
    ])
    error_message = "Instance types must be in format like 't3.medium', 'db.t3.small', etc."
  }
}

# ============================================================================
# FEATURE FLAGS
# ============================================================================

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for network monitoring"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources (overrides environment default)"
  type        = bool
  default     = null
}

variable "create_ecr_repositories" {
  description = "Create ECR repositories for container images"
  type        = bool
  default     = true
}

# ============================================================================
# ENTERPRISE FEATURE FLAGS
# ============================================================================

variable "enable_enterprise_databases" {
  description = "Enable enterprise database support (SQL Server, Oracle)"
  type        = bool
  default     = false
}

variable "enable_oracle_database" {
  description = "Enable Oracle database support (requires enable_enterprise_databases)"
  type        = bool
  default     = false
}

variable "enable_enterprise_security" {
  description = "Enable enterprise security features (WAF, GuardDuty, advanced monitoring)"
  type        = bool
  default     = false
}

variable "enable_enterprise_compliance" {
  description = "Enable enterprise compliance features (Config, CloudTrail, audit logging)"
  type        = bool
  default     = false
}

variable "enable_enterprise_auth" {
  description = "Enable enterprise authentication features (LDAP, SAML, Secrets Manager)"
  type        = bool
  default     = false
}

variable "enable_enterprise_monitoring" {
  description = "Enable enterprise monitoring features (X-Ray, enhanced CloudWatch)"
  type        = bool
  default     = false
}

variable "enable_enterprise_messaging" {
  description = "Enable enterprise messaging features (RabbitMQ, ActiveMQ support)"
  type        = bool
  default     = false
}

# ============================================================================
# TAGGING
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
  
  validation {
    condition = alltrue([
      for k, v in var.additional_tags : can(regex("^[a-zA-Z0-9\\s\\-_.:/@]+$", k)) && can(regex("^[a-zA-Z0-9\\s\\-_.:/@]+$", v))
    ])
    error_message = "Tag keys and values must contain only alphanumeric characters, spaces, and the following special characters: - _ . : / @"
  }
}

variable "cost_center" {
  description = "Cost center for billing and resource allocation"
  type        = string
  default     = "Engineering"
}

variable "compliance_level" {
  description = "Compliance level for the infrastructure (low, medium, high)"
  type        = string
  default     = "medium"
  
  validation {
    condition     = contains(["low", "medium", "high"], var.compliance_level)
    error_message = "Compliance level must be low, medium, or high."
  }
}
