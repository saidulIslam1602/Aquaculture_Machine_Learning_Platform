# =============================================================================
# DATA SOURCES - DYNAMIC INFORMATION RETRIEVAL
# =============================================================================
# Data sources fetch information about existing AWS resources and account details.
# Unlike variables (which you set), data sources query AWS for current information.
# This makes your configuration dynamic and adaptable to different AWS accounts/regions.

# =============================================================================
# AWS ACCOUNT AND REGION INFORMATION
# =============================================================================

# Get current AWS account information
# This tells us which AWS account we're deploying to (useful for IAM policies and tagging)
data "aws_caller_identity" "current" {}

# Get current AWS region information
# This tells us which AWS region we're deploying to (useful for region-specific configurations)
data "aws_region" "current" {}

# =============================================================================
# AVAILABILITY ZONE DISCOVERY
# =============================================================================

# Get all available availability zones in the current region
# Availability zones are isolated data centers within a region
# We need multiple AZs for high availability and fault tolerance
data "aws_availability_zones" "available" {
  state = "available"  # Only get AZs that are currently operational
  
  # Filter to only get standard availability zones (not local zones or wavelength zones)
  filter {
    name   = "zone-type"
    values = ["availability-zone"]  # Standard AZs only
  }
}

# =============================================================================
# AMI (AMAZON MACHINE IMAGE) DISCOVERY
# =============================================================================

# Get the latest Amazon Linux 2 AMI for bastion hosts or other EC2 instances
# AMIs are templates for creating EC2 instances with pre-installed operating systems
# We always want the latest version for security updates
data "aws_ami" "amazon_linux" {
  most_recent = true        # Get the newest version available
  owners      = ["amazon"]  # Only trust AMIs published by Amazon
  
  # Filter for Amazon Linux 2 AMIs with specific characteristics
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]  # Amazon Linux 2, HVM, x86_64, GP2 storage
  }
  
  # Ensure we get hardware virtual machine (HVM) type (modern virtualization)
  filter {
    name   = "virtualization-type"
    values = ["hvm"]  # Hardware Virtual Machine (better performance than paravirtual)
  }
  
  # Only get AMIs that are currently available for use
  filter {
    name   = "state"
    values = ["available"]  # Ready to use
  }
}

# =============================================================================
# EKS CLUSTER INFORMATION (for Kubernetes integration)
# =============================================================================

# Get EKS cluster OIDC issuer URL for IAM Roles for Service Accounts (IRSA)
# IRSA allows Kubernetes pods to assume AWS IAM roles securely
# This is needed for pods to access AWS services like S3, RDS, etc.
data "aws_eks_cluster" "cluster" {
  name = module.eks.cluster_name  # Reference the cluster created in main.tf
  
  depends_on = [module.eks]  # Wait for the EKS cluster to be created first
}

# Get EKS cluster authentication token for kubectl access
# This token allows Terraform to communicate with the Kubernetes API
# Used by the Kubernetes and Helm providers to deploy resources to the cluster
data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name  # Reference the cluster created in main.tf
  
  depends_on = [module.eks]  # Wait for the EKS cluster to be created first
}
