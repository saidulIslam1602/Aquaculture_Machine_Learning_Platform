# =============================================================================
# TERRAFORM VERSION AND PROVIDER REQUIREMENTS
# =============================================================================
# This file defines the minimum versions for Terraform and all required providers.
# It also configures the remote state backend for team collaboration and state locking.

terraform {
  # Minimum Terraform version required to run this configuration
  # Using 1.5.0+ ensures we have access to modern Terraform features
  required_version = ">= 1.5.0"
  
  # Define all providers used in this configuration with version constraints
  required_providers {
    # AWS Provider - Main cloud provider for all infrastructure resources
    # Version ~> 5.0 means any version >= 5.0.0 but < 6.0.0
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    
    # Kubernetes Provider - For managing Kubernetes resources within EKS cluster
    # Used for creating namespaces, service accounts, and other K8s objects
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    
    # Helm Provider - For deploying Helm charts to Kubernetes cluster
    # Used for installing applications like monitoring tools, ingress controllers
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    
    # Random Provider - For generating random values like bucket suffixes
    # Ensures unique resource names to avoid conflicts
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
  
  # =============================================================================
  # REMOTE STATE BACKEND CONFIGURATION
  # =============================================================================
  # Stores Terraform state in S3 with DynamoDB locking for team collaboration
  # This prevents multiple team members from modifying infrastructure simultaneously
  backend "s3" {
    bucket         = "aquaculture-terraform-state"  # S3 bucket to store state file
    key            = "prod/terraform.tfstate"       # Path within bucket for state file
    region         = "us-east-1"                    # AWS region for state bucket
    encrypt        = true                           # Encrypt state file at rest
    dynamodb_table = "terraform-state-lock"        # DynamoDB table for state locking
  }
}
