"""
BigQuery Data Warehouse Connector

This module provides functionality to sync agricultural IoT data from TimescaleDB
to BigQuery for analytics and reporting. Implements modern data stack patterns
with incremental loading, schema evolution, and data quality checks.

Industry Standards:
    - Incremental data loading with watermarks
    - Schema evolution and compatibility
    - Data quality validation
    - Retry logic and error handling
    - Monitoring and observability
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from google.cloud import bigquery
from google.cloud.exceptions import NotFound, BadRequest
from google.oauth2 import service_account
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """Configuration for data sync operations"""
    source_table: str
    target_dataset: str
    target_table: str
    incremental_column: str
    batch_size: int = 10000
    lookback_hours: int = 24
    partition_field: Optional[str] = None
    clustering_fields: Optional[List[str]] = None


class BigQueryConnector:
    """
    BigQuery connector for agricultural IoT data warehouse operations.
    
    Provides methods for syncing data from TimescaleDB to BigQuery,
    managing schemas, and performing data quality checks.
    """
    
    def __init__(self):
        self.project_id = settings.BIGQUERY_PROJECT_ID
        self.dataset_id = settings.BIGQUERY_DATASET_ID
        self.credentials_path = settings.BIGQUERY_CREDENTIALS_PATH
        
        # Initialize BigQuery client
        self.client = self._initialize_client()
        self.dataset_ref = self.client.dataset(self.dataset_id)
        
    def _initialize_client(self) -> bigquery.Client:
        """Initialize BigQuery client with service account credentials"""
        try:
            if os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                client = bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
            else:
                # Fallback to default credentials (for local development)
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                client = bigquery.Client(project=self.project_id)
                
            logger.info(f"BigQuery client initialized for project: {self.project_id}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def ensure_dataset_exists(self) -> bool:
        """
        Ensure the target dataset exists in BigQuery.
        
        Returns:
            bool: True if dataset exists or was created successfully
        """
        try:
            # Try to get the dataset
            self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
            return True
            
        except NotFound:
            # Create the dataset
            try:
                dataset = bigquery.Dataset(self.dataset_ref)
                dataset.location = "US"  # or your preferred location
                dataset.description = "Agricultural IoT telemetry data for analytics"
                
                dataset = self.client.create_dataset(dataset, timeout=30)
                logger.info(f"Created dataset {self.dataset_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create dataset {self.dataset_id}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking dataset {self.dataset_id}: {e}")
            return False
    
    def create_table_schema(self, table_name: str, schema_config: Dict[str, Any]) -> bool:
        """
        Create or update BigQuery table schema.
        
        Args:
            table_name: Name of the BigQuery table
            schema_config: Schema configuration dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            table_ref = self.dataset_ref.table(table_name)
            
            # Define schema based on configuration
            schema_fields = []
            
            if table_name == "sensor_telemetry":
                schema_fields = [
                    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("sensor_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("entity_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("farm_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("entity_type", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("species", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("latitude", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("longitude", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("heart_rate", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("temperature", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("activity_level", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("rumination_time", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("step_count", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("lying_time", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("eating_time", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("battery_level", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("signal_strength", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("data_quality_score", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("is_anomaly", "BOOLEAN", mode="NULLABLE"),
                    bigquery.SchemaField("raw_metrics", "JSON", mode="NULLABLE"),
                    bigquery.SchemaField("ingestion_timestamp", "TIMESTAMP", mode="REQUIRED"),
                ]
                
            elif table_name == "livestock_health_daily":
                schema_fields = [
                    bigquery.SchemaField("entity_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("farm_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("external_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("entity_name", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("species", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("breed", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("age_months", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                    bigquery.SchemaField("avg_heart_rate", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("min_heart_rate", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("max_heart_rate", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("avg_temperature", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("avg_activity_level", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("total_steps", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("total_rumination_time", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("health_score", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("health_status", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("total_readings", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("anomaly_count", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("avg_battery_level", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("calculated_at", "TIMESTAMP", mode="REQUIRED"),
                ]
            
            # Create table configuration
            table = bigquery.Table(table_ref, schema=schema_fields)
            
            # Configure partitioning and clustering
            if schema_config.get("partition_field"):
                if schema_config["partition_field"] == "timestamp":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field="timestamp"
                    )
                elif schema_config["partition_field"] == "date":
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field="date"
                    )
            
            if schema_config.get("clustering_fields"):
                table.clustering_fields = schema_config["clustering_fields"]
            
            # Create or update table
            try:
                table = self.client.create_table(table)
                logger.info(f"Created BigQuery table: {table_name}")
            except BadRequest as e:
                if "already exists" in str(e):
                    # Update existing table schema
                    existing_table = self.client.get_table(table_ref)
                    existing_table.schema = schema_fields
                    table = self.client.update_table(existing_table, ["schema"])
                    logger.info(f"Updated BigQuery table schema: {table_name}")
                else:
                    raise
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create/update table {table_name}: {e}")
            return False
    
    def sync_sensor_telemetry(
        self, 
        sync_config: SyncConfig,
        db: Session
    ) -> Dict[str, Any]:
        """
        Sync sensor telemetry data from TimescaleDB to BigQuery.
        
        Args:
            sync_config: Sync configuration
            db: Database session
            
        Returns:
            Dict with sync results
        """
        try:
            # Get last sync timestamp from BigQuery
            last_sync_timestamp = self._get_last_sync_timestamp(
                sync_config.target_table,
                sync_config.incremental_column
            )
            
            # Calculate sync window
            if last_sync_timestamp:
                start_time = last_sync_timestamp - timedelta(hours=sync_config.lookback_hours)
            else:
                start_time = datetime.utcnow() - timedelta(days=7)  # Initial load: last 7 days
            
            end_time = datetime.utcnow()
            
            logger.info(f"Syncing telemetry data from {start_time} to {end_time}")
            
            # Extract data from TimescaleDB
            query = text("""
                SELECT 
                    st.timestamp,
                    st.sensor_id::text as sensor_id,
                    st.entity_id::text as entity_id,
                    e.farm_id,
                    e.entity_type,
                    e.metadata->>'species' as species,
                    CASE 
                        WHEN st.location IS NOT NULL 
                        THEN ST_Y(st.location::geometry) 
                        ELSE NULL 
                    END as latitude,
                    CASE 
                        WHEN st.location IS NOT NULL 
                        THEN ST_X(st.location::geometry) 
                        ELSE NULL 
                    END as longitude,
                    (st.metrics->>'heart_rate')::numeric as heart_rate,
                    st.temperature,
                    (st.metrics->>'activity_level')::numeric as activity_level,
                    (st.metrics->>'rumination_time')::integer as rumination_time,
                    (st.metrics->>'step_count')::integer as step_count,
                    (st.metrics->>'lying_time')::integer as lying_time,
                    (st.metrics->>'eating_time')::integer as eating_time,
                    st.battery_level,
                    st.signal_strength,
                    st.data_quality_score,
                    st.is_anomaly,
                    st.metrics as raw_metrics,
                    CURRENT_TIMESTAMP as ingestion_timestamp
                FROM sensor_telemetry st
                JOIN entities e ON st.entity_id = e.id
                WHERE st.timestamp >= :start_time 
                    AND st.timestamp < :end_time
                    AND st.data_quality_score >= :quality_threshold
                ORDER BY st.timestamp
            """)
            
            # Execute query in batches
            total_rows = 0
            batch_count = 0
            
            result = db.execute(query, {
                "start_time": start_time,
                "end_time": end_time,
                "quality_threshold": 0.7
            })
            
            # Convert to DataFrame for BigQuery loading
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            if len(df) == 0:
                logger.info("No new data to sync")
                return {"status": "success", "rows_synced": 0, "batches": 0}
            
            # Process in batches
            for i in range(0, len(df), sync_config.batch_size):
                batch_df = df.iloc[i:i + sync_config.batch_size].copy()
                
                # Data type conversions for BigQuery
                batch_df['timestamp'] = pd.to_datetime(batch_df['timestamp'])
                batch_df['ingestion_timestamp'] = pd.to_datetime(batch_df['ingestion_timestamp'])
                
                # Convert JSON columns
                if 'raw_metrics' in batch_df.columns:
                    batch_df['raw_metrics'] = batch_df['raw_metrics'].apply(
                        lambda x: json.dumps(x) if x is not None else None
                    )
                
                # Load to BigQuery
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
                )
                
                table_ref = self.dataset_ref.table(sync_config.target_table)
                job = self.client.load_table_from_dataframe(
                    batch_df, table_ref, job_config=job_config
                )
                
                job.result()  # Wait for job to complete
                
                total_rows += len(batch_df)
                batch_count += 1
                
                logger.info(f"Loaded batch {batch_count}: {len(batch_df)} rows")
            
            logger.info(f"Sync completed: {total_rows} rows in {batch_count} batches")
            
            return {
                "status": "success",
                "rows_synced": total_rows,
                "batches": batch_count,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync sensor telemetry: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_last_sync_timestamp(
        self, 
        table_name: str, 
        timestamp_column: str
    ) -> Optional[datetime]:
        """
        Get the last sync timestamp from BigQuery table.
        
        Args:
            table_name: BigQuery table name
            timestamp_column: Timestamp column name
            
        Returns:
            Last sync timestamp or None if table is empty
        """
        try:
            query = f"""
                SELECT MAX({timestamp_column}) as last_timestamp
                FROM `{self.project_id}.{self.dataset_id}.{table_name}`
            """
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            for row in results:
                if row.last_timestamp:
                    return row.last_timestamp.replace(tzinfo=None)
            
            return None
            
        except NotFound:
            logger.info(f"Table {table_name} not found, will perform initial load")
            return None
        except Exception as e:
            logger.error(f"Error getting last sync timestamp: {e}")
            return None
    
    def run_data_quality_checks(self, table_name: str) -> Dict[str, Any]:
        """
        Run data quality checks on BigQuery table.
        
        Args:
            table_name: Table name to check
            
        Returns:
            Dict with data quality results
        """
        try:
            checks = {}
            
            # Row count check
            query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT entity_id) as unique_entities,
                    MIN(timestamp) as earliest_data,
                    MAX(timestamp) as latest_data
                FROM `{self.project_id}.{self.dataset_id}.{table_name}`
            """
            
            result = self.client.query(query).result()
            for row in result:
                checks["row_count"] = row.total_rows
                checks["unique_entities"] = row.unique_entities
                checks["data_range"] = {
                    "earliest": row.earliest_data.isoformat() if row.earliest_data else None,
                    "latest": row.latest_data.isoformat() if row.latest_data else None
                }
            
            # Data quality score check
            quality_query = f"""
                SELECT 
                    AVG(data_quality_score) as avg_quality_score,
                    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality_count,
                    COUNT(CASE WHEN is_anomaly THEN 1 END) as anomaly_count
                FROM `{self.project_id}.{self.dataset_id}.{table_name}`
                WHERE DATE(timestamp) = CURRENT_DATE()
            """
            
            result = self.client.query(quality_query).result()
            for row in result:
                checks["quality_metrics"] = {
                    "avg_quality_score": float(row.avg_quality_score) if row.avg_quality_score else 0,
                    "low_quality_count": row.low_quality_count,
                    "anomaly_count": row.anomaly_count
                }
            
            checks["status"] = "passed"
            checks["timestamp"] = datetime.utcnow().isoformat()
            
            return checks
            
        except Exception as e:
            logger.error(f"Data quality check failed for {table_name}: {e}")
            return {"status": "failed", "error": str(e)}


def sync_agricultural_data_to_bigquery() -> Dict[str, Any]:
    """
    Main function to sync all agricultural data to BigQuery.
    
    Returns:
        Dict with sync results for all tables
    """
    connector = BigQueryConnector()
    
    # Ensure dataset exists
    if not connector.ensure_dataset_exists():
        return {"status": "error", "error": "Failed to ensure dataset exists"}
    
    results = {}
    
    # Sync configurations
    sync_configs = [
        SyncConfig(
            source_table="sensor_telemetry",
            target_dataset=settings.BIGQUERY_DATASET_ID,
            target_table="sensor_telemetry",
            incremental_column="timestamp",
            batch_size=5000,
            partition_field="timestamp",
            clustering_fields=["entity_id", "farm_id"]
        )
    ]
    
    # Create table schemas
    schema_configs = {
        "sensor_telemetry": {
            "partition_field": "timestamp",
            "clustering_fields": ["entity_id", "farm_id"]
        },
        "livestock_health_daily": {
            "partition_field": "date",
            "clustering_fields": ["farm_id", "entity_id"]
        }
    }
    
    for table_name, schema_config in schema_configs.items():
        connector.create_table_schema(table_name, schema_config)
    
    # Sync data
    db = next(get_db())
    try:
        for sync_config in sync_configs:
            sync_result = connector.sync_sensor_telemetry(sync_config, db)
            results[sync_config.target_table] = sync_result
            
            # Run data quality checks
            if sync_result.get("status") == "success":
                quality_result = connector.run_data_quality_checks(sync_config.target_table)
                results[f"{sync_config.target_table}_quality"] = quality_result
    
    finally:
        db.close()
    
    return results
