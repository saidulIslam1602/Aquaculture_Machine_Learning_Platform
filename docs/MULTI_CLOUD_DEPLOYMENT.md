# 🌐 Multi-Cloud Deployment Guide

This guide covers deploying the Aquaculture ML Platform across AWS, Azure, and Google Cloud Platform.

## 🗄️ Database Compatibility Matrix

| Feature | PostgreSQL | SQL Server | MySQL |
|---------|------------|------------|-------|
| **AWS** | ✅ RDS PostgreSQL | ✅ RDS SQL Server | ✅ RDS MySQL |
| **Azure** | ✅ Azure Database for PostgreSQL | ✅ Azure SQL Database | ✅ Azure Database for MySQL |
| **GCP** | ✅ Cloud SQL PostgreSQL | ❌ Not Available | ✅ Cloud SQL MySQL |
| **Multi-Cloud** | ✅ **Recommended** | ⚠️ Limited | ✅ Good |

## 🎯 **Recommended: PostgreSQL for Multi-Cloud**

PostgreSQL is the best choice for multi-cloud deployment because:
- ✅ Available on all major cloud providers
- ✅ Consistent feature set across clouds
- ✅ Best performance for JSON/JSONB data
- ✅ Advanced indexing and query optimization
- ✅ Strong ACID compliance

## 🚀 Cloud-Specific Deployment Instructions

### 🔶 **AWS Deployment**

#### 1. Database Setup
```bash
# Using AWS RDS PostgreSQL
aws rds create-db-instance \
    --db-instance-identifier aquaculture-ml-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 15.4 \
    --master-username aquaculture \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 100 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-subnet-group-name aquaculture-subnet-group \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted
```

#### 2. Environment Configuration
```bash
# .env.aws.production
DATABASE_URL=postgresql://aquaculture:password@aquaculture-ml-db.xxxxx.us-east-1.rds.amazonaws.com:5432/aquaculture_db
REDIS_URL=redis://aquaculture-ml-cache.xxxxx.cache.amazonaws.com:6379/0
AWS_REGION=us-east-1
AWS_S3_BUCKET=aquaculture-ml-models-prod
MODEL_STORAGE_URL=s3://aquaculture-ml-models-prod/models/
```

#### 3. Deploy with Terraform
```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars for AWS
terraform init
terraform plan
terraform apply
```

### 🔷 **Azure Deployment**

#### 1. Database Setup
```bash
# Using Azure Database for PostgreSQL
az postgres server create \
    --resource-group aquaculture-ml-rg \
    --name aquaculture-ml-db \
    --location eastus \
    --admin-user aquaculture \
    --admin-password "YourSecurePassword123!" \
    --sku-name GP_Gen5_2 \
    --storage-size 102400 \
    --version 15
```

#### 2. Environment Configuration
```bash
# .env.azure.production
DATABASE_URL=postgresql://aquaculture:password@aquaculture-ml-db.postgres.database.azure.com:5432/aquaculture_db?sslmode=require
REDIS_URL=redis://aquaculture-ml-cache.redis.cache.windows.net:6380/0?ssl=true
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=aquaculture-ml-rg
MODEL_STORAGE_URL=https://aquaculturemlstorage.blob.core.windows.net/models/
```

#### 3. Deploy with ARM Templates
```bash
# Deploy using Azure Resource Manager
az deployment group create \
    --resource-group aquaculture-ml-rg \
    --template-file infrastructure/azure/main.json \
    --parameters @infrastructure/azure/parameters.json
```

### 🟡 **Google Cloud Deployment**

#### 1. Database Setup
```bash
# Using Cloud SQL PostgreSQL
gcloud sql instances create aquaculture-ml-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-2-7680 \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=100GB \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04
```

#### 2. Environment Configuration
```bash
# .env.gcp.production
DATABASE_URL=postgresql://aquaculture:password@/aquaculture_db?host=/cloudsql/project-id:us-central1:aquaculture-ml-db
REDIS_URL=redis://10.0.0.3:6379/0
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
MODEL_STORAGE_URL=gs://aquaculture-ml-models-prod/models/
```

#### 3. Deploy with Deployment Manager
```bash
# Deploy using Google Cloud Deployment Manager
gcloud deployment-manager deployments create aquaculture-ml \
    --config infrastructure/gcp/deployment.yaml
```

## 🔄 Database Migration Process

### 1. **From Azure SQL Studio to Production**

If you create your schema in Azure SQL Studio, here's how to migrate:

#### Option A: Export Schema Only
```sql
-- In Azure SQL Studio, generate CREATE scripts
-- Right-click database → Tasks → Generate Scripts
-- Select "Script Indexes" and "Script Data" as needed
```

#### Option B: Use Our Migration Script
```bash
# Our migration works with any PostgreSQL database
cd /path/to/project
source venv/bin/activate

# Set your production database URL
export DATABASE_URL="postgresql://user:pass@prod-host:5432/dbname"

# Run migration
python -m alembic upgrade head

# Seed initial data
python scripts/seed_production_data.py
```

### 2. **Cross-Cloud Migration**

To migrate between cloud providers:

```bash
# 1. Export data from source
pg_dump -h source-host -U username -d database_name > backup.sql

# 2. Import to target
psql -h target-host -U username -d database_name < backup.sql

# 3. Update connection strings
# Update your .env files with new database URLs
```

## 🔐 Security Considerations

### Database Security
```bash
# 1. Enable SSL/TLS
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# 2. Use connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# 3. Enable audit logging (cloud-specific)
# AWS: Enable RDS Performance Insights
# Azure: Enable Azure SQL Database Auditing  
# GCP: Enable Cloud SQL Audit Logs
```

### Secrets Management
```bash
# AWS: Use AWS Secrets Manager
aws secretsmanager create-secret \
    --name aquaculture-ml/database \
    --secret-string '{"username":"aquaculture","password":"SecurePass123!"}'

# Azure: Use Azure Key Vault
az keyvault secret set \
    --vault-name aquaculture-ml-kv \
    --name database-password \
    --value "SecurePass123!"

# GCP: Use Secret Manager
gcloud secrets create database-password \
    --data-file=password.txt
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_predictions_created_at_species 
ON predictions (created_at, predicted_species_id);

CREATE INDEX CONCURRENTLY idx_predictions_confidence_desc 
ON predictions (confidence DESC);

-- Enable query optimization
ANALYZE;
```

### Connection Pooling
```python
# In production configuration
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

## 🔍 Monitoring & Alerting

### Database Monitoring
```yaml
# Prometheus alerts for database
groups:
  - name: database
    rules:
      - alert: DatabaseConnectionHigh
        expr: database_connections_active / database_connections_max > 0.8
        for: 5m
        
      - alert: DatabaseSlowQueries
        expr: database_query_duration_p95 > 1000
        for: 2m
```

### Cloud-Specific Monitoring
- **AWS**: CloudWatch + RDS Performance Insights
- **Azure**: Azure Monitor + SQL Analytics
- **GCP**: Cloud Monitoring + Cloud SQL Insights

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Database schema created and tested
- [ ] Environment variables configured
- [ ] Secrets properly managed
- [ ] SSL/TLS certificates obtained
- [ ] Backup strategy implemented
- [ ] Monitoring configured

### Post-Deployment
- [ ] Database connectivity tested
- [ ] Initial data seeded
- [ ] Health checks passing
- [ ] Performance metrics baseline established
- [ ] Backup restoration tested
- [ ] Security scan completed

## 🆘 Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Test database connectivity
psql -h hostname -U username -d database_name -c "SELECT version();"

# Check SSL requirements
psql "postgresql://user:pass@host:5432/db?sslmode=require"
```

#### Performance Issues
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'predictions';
```

#### Migration Issues
```bash
# Check migration status
python -m alembic current

# Show migration history
python -m alembic history

# Rollback if needed
python -m alembic downgrade -1
```

## 📞 Support

For deployment issues:
1. Check cloud provider documentation
2. Review application logs
3. Verify network connectivity
4. Confirm security group/firewall rules
5. Test database connectivity independently

---

**✅ Your database created in Azure SQL Studio will work perfectly with this multi-cloud setup!** Just use our migration scripts to deploy the same schema to any cloud provider.
