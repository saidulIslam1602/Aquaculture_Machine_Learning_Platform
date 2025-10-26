# Monitoring and Alerting
# CloudWatch alarms, SNS topics, and monitoring resources

# ============================================================================
# SNS TOPICS FOR ALERTS
# ============================================================================

# SNS Topic for Critical Alerts
resource "aws_sns_topic" "critical_alerts" {
  count = local.monitoring_enabled ? 1 : 0
  
  name = "${local.name_prefix}-critical-alerts"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-critical-alerts"
    Type = "Monitoring"
  })
}

# SNS Topic for Warning Alerts
resource "aws_sns_topic" "warning_alerts" {
  count = local.monitoring_enabled ? 1 : 0
  
  name = "${local.name_prefix}-warning-alerts"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-warning-alerts"
    Type = "Monitoring"
  })
}

# Email subscription for critical alerts
resource "aws_sns_topic_subscription" "critical_email" {
  count = local.monitoring_enabled && var.owner_email != "" ? 1 : 0
  
  topic_arn = aws_sns_topic.critical_alerts[0].arn
  protocol  = "email"
  endpoint  = var.owner_email
}

# ============================================================================
# EKS CLUSTER MONITORING
# ============================================================================

# EKS Cluster CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "eks_cpu_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-eks-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EKS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EKS cluster CPU utilization"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  ok_actions          = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    ClusterName = module.eks.cluster_name
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-eks-cpu-high"
    Service = "EKS"
    Severity = "Warning"
  })
}

# EKS Node Group Memory Utilization
resource "aws_cloudwatch_metric_alarm" "eks_memory_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-eks-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/EKS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors EKS cluster memory utilization"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    ClusterName = module.eks.cluster_name
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-eks-memory-high"
    Service = "EKS"
    Severity = "Warning"
  })
}

# ============================================================================
# RDS DATABASE MONITORING
# ============================================================================

# RDS CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    DBInstanceIdentifier = module.rds.db_instance_identifier
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-rds-cpu-high"
    Service = "RDS"
    Severity = "Warning"
  })
}

# RDS Database Connections Alarm
resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS database connections"
  alarm_actions       = [aws_sns_topic.critical_alerts[0].arn]
  
  dimensions = {
    DBInstanceIdentifier = module.rds.db_instance_identifier
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-rds-connections-high"
    Service = "RDS"
    Severity = "Critical"
  })
}

# RDS Free Storage Space Alarm
resource "aws_cloudwatch_metric_alarm" "rds_free_storage_low" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-rds-free-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "2000000000"  # 2GB in bytes
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = [aws_sns_topic.critical_alerts[0].arn]
  
  dimensions = {
    DBInstanceIdentifier = module.rds.db_instance_identifier
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-rds-free-storage-low"
    Service = "RDS"
    Severity = "Critical"
  })
}

# ============================================================================
# ELASTICACHE REDIS MONITORING
# ============================================================================

# Redis CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "This metric monitors Redis CPU utilization"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    CacheClusterId = "${aws_elasticache_replication_group.redis.replication_group_id}-001"
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-redis-cpu-high"
    Service = "ElastiCache"
    Severity = "Warning"
  })
}

# Redis Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors Redis memory utilization"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    CacheClusterId = "${aws_elasticache_replication_group.redis.replication_group_id}-001"
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-redis-memory-high"
    Service = "ElastiCache"
    Severity = "Warning"
  })
}

# ============================================================================
# APPLICATION LOAD BALANCER MONITORING
# ============================================================================

# ALB Target Response Time Alarm
resource "aws_cloudwatch_metric_alarm" "alb_response_time_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-alb-response-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"  # 1 second
  alarm_description   = "This metric monitors ALB target response time"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-alb-response-time-high"
    Service = "ALB"
    Severity = "Warning"
  })
}

# ALB HTTP 5xx Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5xx error count"
  alarm_actions       = [aws_sns_topic.critical_alerts[0].arn]
  
  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-alb-5xx-errors"
    Service = "ALB"
    Severity = "Critical"
  })
}

# ============================================================================
# KAFKA MONITORING
# ============================================================================

# Kafka Disk Usage Alarm
resource "aws_cloudwatch_metric_alarm" "kafka_disk_usage_high" {
  count = local.monitoring_enabled ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-kafka-disk-usage-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "KafkaDataLogsDiskUsed"
  namespace           = "AWS/Kafka"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors Kafka disk usage percentage"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    "Cluster Name" = aws_msk_cluster.kafka.cluster_name
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-kafka-disk-usage-high"
    Service = "Kafka"
    Severity = "Warning"
  })
}

# ============================================================================
# ENTERPRISE DATABASE MONITORING
# ============================================================================

# SQL Server CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "sqlserver_cpu_high" {
  count = local.monitoring_enabled && var.enable_enterprise_databases ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-sqlserver-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors SQL Server CPU utilization"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.sqlserver[0].identifier
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-sqlserver-cpu-high"
    Service = "SQLServer"
    Severity = "Warning"
  })
}

# SQL Server Database Connections Alarm
resource "aws_cloudwatch_metric_alarm" "sqlserver_connections_high" {
  count = local.monitoring_enabled && var.enable_enterprise_databases ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-sqlserver-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors SQL Server database connections"
  alarm_actions       = [aws_sns_topic.critical_alerts[0].arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.sqlserver[0].identifier
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-sqlserver-connections-high"
    Service = "SQLServer"
    Severity = "Critical"
  })
}

# ============================================================================
# ENTERPRISE SECURITY MONITORING
# ============================================================================

# WAF Blocked Requests Alarm
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests_high" {
  count = local.monitoring_enabled && var.enable_enterprise_security ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-waf-blocked-requests-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "This metric monitors high number of WAF blocked requests"
  alarm_actions       = [aws_sns_topic.warning_alerts[0].arn]
  
  dimensions = {
    WebACL = aws_wafv2_web_acl.main[0].name
    Region = local.region
  }
  
  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-waf-blocked-requests-high"
    Service = "WAF"
    Severity = "Warning"
  })
}

# GuardDuty Finding Alarm
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  count = var.enable_enterprise_security ? 1 : 0
  
  name        = "${local.name_prefix}-guardduty-findings"
  description = "Capture GuardDuty findings"
  
  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9]
    }
  })
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-guardduty-findings"
    Type = "Security"
  })
}

resource "aws_cloudwatch_event_target" "guardduty_sns" {
  count = var.enable_enterprise_security ? 1 : 0
  
  rule      = aws_cloudwatch_event_rule.guardduty_findings[0].name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.critical_alerts[0].arn
}

# ============================================================================
# CUSTOM DASHBOARDS
# ============================================================================

# CloudWatch Dashboard for Infrastructure Overview
resource "aws_cloudwatch_dashboard" "infrastructure_overview" {
  count = local.monitoring_enabled ? 1 : 0
  
  dashboard_name = "${local.name_prefix}-infrastructure-overview"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/EKS", "CPUUtilization", "ClusterName", module.eks.cluster_name],
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", module.rds.db_instance_identifier],
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${aws_elasticache_replication_group.redis.replication_group_id}-001"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = local.region
          title   = "CPU Utilization"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = local.region
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      }
    ]
  })
}
