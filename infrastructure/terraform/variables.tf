# =============================================================================
# TERRAFORM INPUT VARIABLES
# =============================================================================
# This file defines all configurable parameters for the infrastructure.
# Variables allow customization without modifying the main configuration files.
# Each variable includes validation rules to prevent configuration errors.

# =============================================================================
# BASIC CONFIGURATION VARIABLES
# =============================================================================
# These variables control the fundamental aspects of your infrastructure deployment

# AWS Region Selection
# Determines where all your infrastructure will be deployed
# Different regions have different costs, latency, and compliance requirements
variable "aws_region" {
  description = "AWS region for deploying resources"
  type        = string
  default     = "us-east-1"  # Virginia region - typically lowest cost
  
  # Validation ensures the region format is correct (e.g., us-east-1, eu-west-1)
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be in format: us-east-1, eu-west-1, etc."
  }
}

# Environment Configuration
# Controls resource sizing, costs, and features based on deployment stage
# - development: Smaller, cheaper resources for testing
# - staging: Medium resources for pre-production testing  
# - production: Full-scale, highly available resources
variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
  
  # Only allow specific environment names to prevent typos and ensure consistency
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

# Project Name for Resource Identification
# Used as a prefix for all AWS resource names to keep them organized
# Also used for cost tracking and resource grouping via tags
variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "aquaculture-ml"
  
  # Ensure project name follows AWS naming conventions (lowercase, no spaces)
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.project_name))
    error_message = "Project name must start with letter, contain only lowercase letters, numbers, and hyphens, and end with alphanumeric character."
  }
  
  # Prevent names that are too short or too long for AWS resource limits
  validation {
    condition     = length(var.project_name) >= 3 && length(var.project_name) <= 50
    error_message = "Project name must be between 3 and 50 characters."
  }
}

# Owner Email for Notifications and Accountability
# Used for sending alerts when infrastructure issues occur
# Also tagged on all resources for cost tracking and ownership identification
variable "owner_email" {
  description = "Owner email address for resource tagging and notifications"
  type        = string
  
  # Validate email format to ensure alerts can be delivered successfully
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.owner_email))
    error_message = "Owner email must be a valid email address."
  }
}

# =============================================================================
# NETWORKING CONFIGURATION VARIABLES
# =============================================================================
# These variables control the network setup including VPC, subnets, and IP ranges
# Proper network design is crucial for security and performance

# VPC IP Address Range
# Defines the private IP address space for your entire network (65,536 addresses)
# 10.0.0.0/16 provides addresses from 10.0.0.1 to 10.0.255.254
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"  # Private IP range - not routable on internet
  
  # Ensure the CIDR block is valid IPv4 format
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

# =============================================================================
# SECURITY CONFIGURATION VARIABLES
# =============================================================================
# These variables control security features like bastion hosts and access controls
# Security should be configured based on your organization's requirements

# Bastion Host for Secure Database Access
# A bastion host is a secure server that provides access to private resources
# Only enable if you need to directly access databases for troubleshooting
variable "create_bastion" {
  description = "Whether to create a bastion host for secure access"
  type        = bool
  default     = false  # Disabled by default for security
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

# =============================================================================
# MONITORING AND LOGGING CONFIGURATION
# =============================================================================
# These variables control how your infrastructure is monitored and logged
# Proper monitoring is essential for maintaining system health

# Infrastructure Monitoring Toggle
# Enables CloudWatch alarms, dashboards, and detailed metrics collection
# Recommended to keep enabled for production systems
variable "enable_monitoring" {
  description = "Enable detailed monitoring and logging"
  type        = bool
  default     = true  # Always monitor production systems
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

# =============================================================================
# RESOURCE SIZING OVERRIDES
# =============================================================================
# These variables allow you to override default instance types for specific needs
# Useful for cost optimization or performance tuning

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

# =============================================================================
# FEATURE FLAGS
# =============================================================================
# These boolean variables enable or disable specific infrastructure features
# Use these to control costs and complexity based on your needs

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

# =============================================================================
# ENTERPRISE FEATURE FLAGS
# =============================================================================
# These variables enable advanced enterprise features like additional databases,
# enhanced security, compliance monitoring, and enterprise authentication
# Enable only if you have enterprise requirements and budget

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

# =============================================================================
# RESOURCE TAGGING CONFIGURATION
# =============================================================================
# Tags help organize resources, track costs, and enforce governance policies
# Proper tagging is essential for managing large infrastructure deployments

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
