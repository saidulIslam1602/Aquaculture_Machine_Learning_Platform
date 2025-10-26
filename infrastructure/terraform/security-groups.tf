# Security Groups
# Define network security rules for all services

# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for Application Load Balancer"
  
  # HTTP access from anywhere
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # HTTPS access from anywhere
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
    Type = "LoadBalancer"
  })
}

# EKS Additional Security Group
resource "aws_security_group" "eks_additional" {
  name_prefix = "${local.name_prefix}-eks-additional-"
  vpc_id      = module.vpc.vpc_id
  description = "Additional security group for EKS cluster communication"
  
  # Allow ALB to communicate with EKS nodes
  ingress {
    description     = "ALB to EKS nodes"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Allow EKS nodes to communicate with each other
  ingress {
    description = "EKS node to node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    self        = true
  }
  
  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eks-additional-sg"
    Type = "EKS"
  })
}

# RDS PostgreSQL Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for RDS PostgreSQL database"
  
  # PostgreSQL access from EKS cluster
  ingress {
    description = "PostgreSQL from EKS cluster"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # PostgreSQL access from bastion (if exists)
  dynamic "ingress" {
    for_each = var.create_bastion ? [1] : []
    content {
      description     = "PostgreSQL from bastion"
      from_port       = 5432
      to_port         = 5432
      protocol        = "tcp"
      security_groups = [aws_security_group.bastion[0].id]
    }
  }
  
  # No outbound rules (default deny)
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-sg"
    Type = "Database"
  })
}

# ElastiCache Redis Security Group
resource "aws_security_group" "redis" {
  name_prefix = "${local.name_prefix}-redis-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for ElastiCache Redis"
  
  # Redis access from EKS cluster
  ingress {
    description = "Redis from EKS cluster"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Redis access from bastion (if exists)
  dynamic "ingress" {
    for_each = var.create_bastion ? [1] : []
    content {
      description     = "Redis from bastion"
      from_port       = 6379
      to_port         = 6379
      protocol        = "tcp"
      security_groups = [aws_security_group.bastion[0].id]
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-sg"
    Type = "Cache"
  })
}

# MSK Kafka Security Group
resource "aws_security_group" "kafka" {
  name_prefix = "${local.name_prefix}-kafka-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for MSK Kafka cluster"
  
  # Kafka broker access from EKS cluster
  ingress {
    description = "Kafka brokers from EKS cluster"
    from_port   = 9092
    to_port     = 9098
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Zookeeper access from EKS cluster
  ingress {
    description = "Zookeeper from EKS cluster"
    from_port   = 2181
    to_port     = 2181
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Kafka JMX access (for monitoring)
  ingress {
    description = "Kafka JMX from EKS cluster"
    from_port   = 11001
    to_port     = 11002
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-kafka-sg"
    Type = "Messaging"
  })
}

# Bastion Host Security Group (Optional)
resource "aws_security_group" "bastion" {
  count = var.create_bastion ? 1 : 0
  
  name_prefix = "${local.name_prefix}-bastion-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for bastion host"
  
  # SSH access from allowed IPs
  ingress {
    description = "SSH from allowed IPs"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.bastion_allowed_cidr_blocks
  }
  
  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-bastion-sg"
    Type = "Bastion"
  })
}

# VPC Endpoints Security Group
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${local.name_prefix}-vpc-endpoints-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for VPC endpoints"
  
  # HTTPS access from VPC
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
  
  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc-endpoints-sg"
    Type = "VPCEndpoints"
  })
}

# ============================================================================
# ENTERPRISE DATABASE SECURITY GROUPS
# ============================================================================

# SQL Server Security Group
resource "aws_security_group" "sqlserver" {
  count = var.enable_enterprise_databases ? 1 : 0
  
  name_prefix = "${local.name_prefix}-sqlserver-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for RDS SQL Server database"
  
  # SQL Server access from EKS cluster
  ingress {
    description = "SQL Server from EKS cluster"
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # SQL Server access from bastion (if exists)
  dynamic "ingress" {
    for_each = var.create_bastion ? [1] : []
    content {
      description     = "SQL Server from bastion"
      from_port       = 1433
      to_port         = 1433
      protocol        = "tcp"
      security_groups = [aws_security_group.bastion[0].id]
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-sqlserver-sg"
    Type = "Database"
  })
}

# Oracle Database Security Group (if needed)
resource "aws_security_group" "oracle" {
  count = var.enable_enterprise_databases && var.enable_oracle_database ? 1 : 0
  
  name_prefix = "${local.name_prefix}-oracle-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for RDS Oracle database"
  
  # Oracle access from EKS cluster
  ingress {
    description = "Oracle from EKS cluster"
    from_port   = 1521
    to_port     = 1521
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Oracle access from bastion (if exists)
  dynamic "ingress" {
    for_each = var.create_bastion ? [1] : []
    content {
      description     = "Oracle from bastion"
      from_port       = 1521
      to_port         = 1521
      protocol        = "tcp"
      security_groups = [aws_security_group.bastion[0].id]
    }
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-oracle-sg"
    Type = "Database"
  })
}

# ============================================================================
# ENTERPRISE SECURITY SERVICE GROUPS
# ============================================================================

# LDAP/Active Directory Security Group
resource "aws_security_group" "ldap" {
  count = var.enable_enterprise_auth ? 1 : 0
  
  name_prefix = "${local.name_prefix}-ldap-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for LDAP/Active Directory integration"
  
  # LDAP access from EKS cluster
  ingress {
    description = "LDAP from EKS cluster"
    from_port   = 389
    to_port     = 389
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # LDAPS (secure LDAP) access from EKS cluster
  ingress {
    description = "LDAPS from EKS cluster"
    from_port   = 636
    to_port     = 636
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Global Catalog LDAP (for Active Directory)
  ingress {
    description = "Global Catalog LDAP from EKS cluster"
    from_port   = 3268
    to_port     = 3268
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Global Catalog LDAPS (for Active Directory)
  ingress {
    description = "Global Catalog LDAPS from EKS cluster"
    from_port   = 3269
    to_port     = 3269
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ldap-sg"
    Type = "Authentication"
  })
}

# Enterprise Message Broker Security Group (RabbitMQ/ActiveMQ)
resource "aws_security_group" "enterprise_messaging" {
  count = var.enable_enterprise_messaging ? 1 : 0
  
  name_prefix = "${local.name_prefix}-enterprise-messaging-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for enterprise message brokers"
  
  # AMQP access from EKS cluster
  ingress {
    description = "AMQP from EKS cluster"
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # AMQPS (secure AMQP) access from EKS cluster
  ingress {
    description = "AMQPS from EKS cluster"
    from_port   = 5671
    to_port     = 5671
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  # Management UI access (RabbitMQ)
  ingress {
    description = "Management UI from EKS cluster"
    from_port   = 15672
    to_port     = 15672
    protocol    = "tcp"
    security_groups = [
      module.eks.cluster_security_group_id,
      aws_security_group.eks_additional.id
    ]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-enterprise-messaging-sg"
    Type = "Messaging"
  })
}
