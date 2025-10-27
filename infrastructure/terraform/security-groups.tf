# =============================================================================
# SECURITY GROUPS - NETWORK FIREWALL RULES
# =============================================================================
# Security groups act as virtual firewalls that control network traffic to AWS resources.
# They define which ports, protocols, and IP addresses can communicate with your services.
# Think of security groups as the "bouncers" at the door of each service.
# 
# Key concepts:
# - Ingress rules: Control incoming traffic TO your resources
# - Egress rules: Control outgoing traffic FROM your resources  
# - CIDR blocks: IP address ranges (e.g., 0.0.0.0/0 = anywhere on internet)
# - Security group references: Allow traffic from other security groups

# =============================================================================
# APPLICATION LOAD BALANCER SECURITY GROUP
# =============================================================================
# Controls access to the load balancer that distributes traffic to your applications
# This is the entry point from the internet to your infrastructure

resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"  # Auto-generated unique name
  vpc_id      = module.vpc.vpc_id            # Deploy in our VPC
  description = "Security group for Application Load Balancer"
  
  # =============================================================================
  # INGRESS RULES (Incoming Traffic)
  # =============================================================================
  
  # Allow HTTP traffic from anywhere on the internet
  # Port 80 is the standard web traffic port (unencrypted)
  ingress {
    description = "HTTP from internet"
    from_port   = 80                # HTTP port
    to_port     = 80
    protocol    = "tcp"             # TCP protocol
    cidr_blocks = ["0.0.0.0/0"]    # Allow from anywhere (entire internet)
  }
  
  # Allow HTTPS traffic from anywhere on the internet
  # Port 443 is the standard secure web traffic port (encrypted)
  ingress {
    description = "HTTPS from internet"
    from_port   = 443               # HTTPS port
    to_port     = 443
    protocol    = "tcp"             # TCP protocol
    cidr_blocks = ["0.0.0.0/0"]    # Allow from anywhere (entire internet)
  }
  
  # =============================================================================
  # EGRESS RULES (Outgoing Traffic)
  # =============================================================================
  
  # Allow all outbound traffic (load balancer needs to reach backend services)
  egress {
    description = "All outbound traffic"
    from_port   = 0                 # All ports
    to_port     = 0                 # All ports
    protocol    = "-1"              # All protocols
    cidr_blocks = ["0.0.0.0/0"]    # Allow to anywhere
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-sg"  # Human-readable name
    Type = "LoadBalancer"                 # Resource type for filtering
  })
}

# =============================================================================
# EKS CLUSTER ADDITIONAL SECURITY GROUP
# =============================================================================
# Controls network access to Kubernetes worker nodes
# EKS creates a default security group, but we need additional rules for our setup

resource "aws_security_group" "eks_additional" {
  name_prefix = "${local.name_prefix}-eks-additional-"  # Auto-generated unique name
  vpc_id      = module.vpc.vpc_id                       # Deploy in our VPC
  description = "Additional security group for EKS cluster communication"
  
  # =============================================================================
  # INGRESS RULES (Incoming Traffic)
  # =============================================================================
  
  # Allow load balancer to reach Kubernetes services
  # This enables the ALB to forward traffic to pods running on worker nodes
  ingress {
    description     = "ALB to EKS nodes"
    from_port       = 0                            # All ports (Kubernetes uses dynamic ports)
    to_port         = 65535                       # All ports
    protocol        = "tcp"                        # TCP protocol
    security_groups = [aws_security_group.alb.id] # Only from our load balancer
  }
  
  # Allow Kubernetes nodes to communicate with each other
  # This is essential for pod-to-pod communication and cluster operations
  ingress {
    description = "EKS node to node communication"
    from_port   = 0      # All ports
    to_port     = 65535  # All ports
    protocol    = "-1"   # All protocols (TCP, UDP, ICMP)
    self        = true   # Allow traffic from other resources with this same security group
  }
  
  # =============================================================================
  # EGRESS RULES (Outgoing Traffic)
  # =============================================================================
  
  # Allow all outbound traffic (nodes need internet access for updates, image pulls, etc.)
  egress {
    description = "All outbound traffic"
    from_port   = 0                 # All ports
    to_port     = 0                 # All ports
    protocol    = "-1"              # All protocols
    cidr_blocks = ["0.0.0.0/0"]    # Allow to anywhere
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-eks-additional-sg"  # Human-readable name
    Type = "EKS"                                     # Resource type for filtering
  })
}

# =============================================================================
# RDS POSTGRESQL DATABASE SECURITY GROUP
# =============================================================================
# Controls access to the PostgreSQL database
# Databases should only be accessible from application servers, never directly from internet

resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"  # Auto-generated unique name
  vpc_id      = module.vpc.vpc_id            # Deploy in our VPC
  description = "Security group for RDS PostgreSQL database"
  
  # =============================================================================
  # INGRESS RULES (Incoming Traffic)
  # =============================================================================
  
  # Allow PostgreSQL connections from Kubernetes cluster
  # This enables applications running in EKS to connect to the database
  ingress {
    description = "PostgreSQL from EKS cluster"
    from_port   = 5432                        # PostgreSQL port
    to_port     = 5432
    protocol    = "tcp"                       # TCP protocol
    security_groups = [
      module.eks.cluster_security_group_id,  # EKS default security group
      aws_security_group.eks_additional.id   # Our additional EKS security group
    ]
  }
  
  # Allow PostgreSQL connections from bastion host (if created)
  # This enables secure database administration through the bastion host
  dynamic "ingress" {
    for_each = var.create_bastion ? [1] : []  # Only create if bastion is enabled
    content {
      description     = "PostgreSQL from bastion"
      from_port       = 5432                           # PostgreSQL port
      to_port         = 5432
      protocol        = "tcp"                          # TCP protocol
      security_groups = [aws_security_group.bastion[0].id]  # Only from bastion host
    }
  }
  
  # =============================================================================
  # EGRESS RULES (Outgoing Traffic)
  # =============================================================================
  # No outbound rules defined = default deny all outbound traffic
  # Databases typically don't need to initiate outbound connections
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-sg"  # Human-readable name
    Type = "Database"                     # Resource type for filtering
  })
}

# =============================================================================
# ELASTICACHE REDIS SECURITY GROUP
# =============================================================================
# Controls access to the Redis cache cluster
# Redis is used for caching and session storage, should only be accessible from applications

resource "aws_security_group" "redis" {
  name_prefix = "${local.name_prefix}-redis-"  # Auto-generated unique name
  vpc_id      = module.vpc.vpc_id              # Deploy in our VPC
  description = "Security group for ElastiCache Redis"
  
  # =============================================================================
  # INGRESS RULES (Incoming Traffic)
  # =============================================================================
  
  # Allow Redis connections from Kubernetes cluster
  # This enables applications to use Redis for caching and session storage
  ingress {
    description = "Redis from EKS cluster"
    from_port   = 6379                        # Redis port
    to_port     = 6379
    protocol    = "tcp"                       # TCP protocol
    security_groups = [
      module.eks.cluster_security_group_id,  # EKS default security group
      aws_security_group.eks_additional.id   # Our additional EKS security group
    ]
  }
  
  # Allow Redis connections from bastion host (if created)
  # This enables Redis administration and troubleshooting through the bastion host
  dynamic "ingress" {
    for_each = var.create_bastion ? [1] : []  # Only create if bastion is enabled
    content {
      description     = "Redis from bastion"
      from_port       = 6379                           # Redis port
      to_port         = 6379
      protocol        = "tcp"                          # TCP protocol
      security_groups = [aws_security_group.bastion[0].id]  # Only from bastion host
    }
  }
  
  # =============================================================================
  # EGRESS RULES (Outgoing Traffic)
  # =============================================================================
  # No outbound rules defined = default deny all outbound traffic
  # Redis cache doesn't need to initiate outbound connections
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-sg"  # Human-readable name
    Type = "Cache"                          # Resource type for filtering
  })
}

# =============================================================================
# MSK KAFKA SECURITY GROUP
# =============================================================================
# Controls access to the Kafka message streaming cluster
# Kafka is used for real-time data processing and event streaming

resource "aws_security_group" "kafka" {
  name_prefix = "${local.name_prefix}-kafka-"  # Auto-generated unique name
  vpc_id      = module.vpc.vpc_id              # Deploy in our VPC
  description = "Security group for MSK Kafka cluster"
  
  # =============================================================================
  # INGRESS RULES (Incoming Traffic)
  # =============================================================================
  
  # Allow Kafka broker connections from Kubernetes cluster
  # Kafka brokers handle message publishing and consumption
  ingress {
    description = "Kafka brokers from EKS cluster"
    from_port   = 9092                        # Kafka broker port range start
    to_port     = 9098                        # Kafka broker port range end
    protocol    = "tcp"                       # TCP protocol
    security_groups = [
      module.eks.cluster_security_group_id,  # EKS default security group
      aws_security_group.eks_additional.id   # Our additional EKS security group
    ]
  }
  
  # Allow Zookeeper connections from Kubernetes cluster
  # Zookeeper coordinates Kafka cluster operations and metadata
  ingress {
    description = "Zookeeper from EKS cluster"
    from_port   = 2181                        # Zookeeper port
    to_port     = 2181
    protocol    = "tcp"                       # TCP protocol
    security_groups = [
      module.eks.cluster_security_group_id,  # EKS default security group
      aws_security_group.eks_additional.id   # Our additional EKS security group
    ]
  }
  
  # Allow JMX monitoring connections from Kubernetes cluster
  # JMX provides metrics and monitoring data for Kafka performance
  ingress {
    description = "Kafka JMX from EKS cluster"
    from_port   = 11001                       # JMX port range start
    to_port     = 11002                       # JMX port range end
    protocol    = "tcp"                       # TCP protocol
    security_groups = [
      module.eks.cluster_security_group_id,  # EKS default security group
      aws_security_group.eks_additional.id   # Our additional EKS security group
    ]
  }
  
  # =============================================================================
  # EGRESS RULES (Outgoing Traffic)
  # =============================================================================
  # No outbound rules defined = default deny all outbound traffic
  # Kafka cluster doesn't need to initiate outbound connections
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-kafka-sg"  # Human-readable name
    Type = "Messaging"                       # Resource type for filtering
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

# =============================================================================
# ENTERPRISE DATABASE SECURITY GROUPS (OPTIONAL)
# =============================================================================
# These security groups are only created when enterprise features are enabled
# They provide access control for additional database systems like SQL Server and Oracle
# Enterprise databases are typically used for legacy system integration

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

# =============================================================================
# ENTERPRISE SECURITY AND AUTHENTICATION GROUPS (OPTIONAL)
# =============================================================================
# These security groups support enterprise features like LDAP integration and message brokers
# They are only created when specific enterprise features are enabled
# Used for integrating with existing enterprise infrastructure

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
