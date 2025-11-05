"""
Agricultural IoT Data Pipeline - Apache Airflow DAG

This DAG orchestrates the complete data pipeline for agricultural IoT telemetry data,
from ingestion through transformation to analytics warehouse loading.

Pipeline Architecture:
1. Data Ingestion: Extract from IoT sensors and external APIs
2. Data Quality: Validate and clean incoming data
3. Data Transformation: Process and enrich data using dbt
4. Data Loading: Load to BigQuery and other destinations
5. Data Monitoring: Track pipeline health and data quality

Industry Standards:
- Proper error handling and retry logic
- Data quality validation at each stage
- Comprehensive monitoring and alerting
- Idempotent operations for reliability
- Proper dependency management
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateDatasetOperator,
    BigQueryInsertJobOperator,
    BigQueryCheckOperator
)
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.sensors.filesystem import FileSensor
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule

import pandas as pd
import logging
from sqlalchemy import create_engine

# DAG Configuration
DAG_ID = "agricultural_iot_data_pipeline"
SCHEDULE_INTERVAL = "0 */6 * * *"  # Every 6 hours
MAX_ACTIVE_RUNS = 1
CATCHUP = False

# Default arguments
default_args = {
    "owner": "data-engineering-team",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

# Pipeline configuration
PIPELINE_CONFIG = {
    "timescaledb_conn_id": "timescaledb_default",
    "bigquery_conn_id": "bigquery_default",
    "data_quality_threshold": 0.85,
    "batch_size": 10000,
    "lookback_hours": 6,
}


def extract_sensor_telemetry(**context) -> Dict[str, Any]:
    """
    Extract sensor telemetry data from TimescaleDB.
    
    Implements incremental extraction based on execution date
    and data quality filtering.
    """
    execution_date = context["execution_date"]
    lookback_hours = PIPELINE_CONFIG["lookback_hours"]
    
    start_time = execution_date - timedelta(hours=lookback_hours)
    end_time = execution_date
    
    logging.info(f"Extracting telemetry data from {start_time} to {end_time}")
    
    # Connect to TimescaleDB
    postgres_hook = PostgresHook(postgres_conn_id=PIPELINE_CONFIG["timescaledb_conn_id"])
    
    # Extract query with data quality filtering
    extract_query = """
        SELECT 
            st.timestamp,
            st.sensor_id::text,
            st.entity_id::text,
            e.farm_id,
            e.entity_type,
            e.entity_metadata->>'species' as species,
            ST_Y(st.location::geometry) as latitude,
            ST_X(st.location::geometry) as longitude,
            (st.metrics->>'heart_rate')::numeric as heart_rate,
            st.temperature,
            (st.metrics->>'activity_level')::numeric as activity_level,
            (st.metrics->>'rumination_time')::integer as rumination_time,
            (st.metrics->>'step_count')::integer as step_count,
            st.battery_level,
            st.signal_strength,
            st.data_quality_score,
            st.is_anomaly,
            st.metrics as raw_metrics
        FROM sensor_telemetry st
        JOIN entities e ON st.entity_id = e.id
        WHERE st.timestamp >= %s 
            AND st.timestamp < %s
            AND st.data_quality_score >= %s
            AND e.is_active = true
        ORDER BY st.timestamp
    """
    
    # Execute extraction
    df = postgres_hook.get_pandas_df(
        extract_query,
        parameters=[
            start_time,
            end_time,
            PIPELINE_CONFIG["data_quality_threshold"]
        ]
    )
    
    logging.info(f"Extracted {len(df)} telemetry records")
    
    # Store extraction metadata
    extraction_stats = {
        "records_extracted": len(df),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "data_quality_threshold": PIPELINE_CONFIG["data_quality_threshold"],
        "extraction_timestamp": datetime.utcnow().isoformat()
    }
    
    # Push to XCom for downstream tasks
    context["task_instance"].xcom_push(key="extraction_stats", value=extraction_stats)
    context["task_instance"].xcom_push(key="extracted_records", value=len(df))
    
    return extraction_stats


def validate_data_quality(**context) -> Dict[str, Any]:
    """
    Validate data quality using Great Expectations framework.
    
    Performs comprehensive data validation including:
    - Schema validation
    - Data completeness checks
    - Value range validation
    - Business rule validation
    """
    import great_expectations as ge
    from great_expectations.core import ExpectationSuite
    
    logging.info("Starting data quality validation")
    
    # Get extraction stats from upstream task
    extraction_stats = context["task_instance"].xcom_pull(
        task_ids="extract_sensor_telemetry",
        key="extraction_stats"
    )
    
    if not extraction_stats or extraction_stats["records_extracted"] == 0:
        raise ValueError("No data extracted for validation")
    
    # Connect to TimescaleDB and get recent data
    postgres_hook = PostgresHook(postgres_conn_id=PIPELINE_CONFIG["timescaledb_conn_id"])
    
    validation_query = """
        SELECT * FROM sensor_telemetry 
        WHERE timestamp >= NOW() - INTERVAL '%s hours'
        LIMIT 1000
    """ % PIPELINE_CONFIG["lookback_hours"]
    
    df = postgres_hook.get_pandas_df(validation_query)
    ge_df = ge.from_pandas(df)
    
    # Define data quality expectations
    validation_results = {}
    
    # Schema validation
    validation_results["schema_valid"] = ge_df.expect_table_columns_to_match_ordered_list([
        "timestamp", "sensor_id", "entity_id", "metrics", "location",
        "temperature", "battery_level", "signal_strength", "data_quality_score", "is_anomaly"
    ]).success
    
    # Completeness validation
    validation_results["timestamp_complete"] = ge_df.expect_column_values_to_not_be_null("timestamp").success
    validation_results["sensor_id_complete"] = ge_df.expect_column_values_to_not_be_null("sensor_id").success
    validation_results["entity_id_complete"] = ge_df.expect_column_values_to_not_be_null("entity_id").success
    
    # Value range validation
    validation_results["temperature_range"] = ge_df.expect_column_values_to_be_between(
        "temperature", min_value=-10, max_value=50
    ).success
    
    validation_results["battery_range"] = ge_df.expect_column_values_to_be_between(
        "battery_level", min_value=0, max_value=100
    ).success
    
    validation_results["quality_score_range"] = ge_df.expect_column_values_to_be_between(
        "data_quality_score", min_value=0, max_value=1
    ).success
    
    # Business rule validation
    validation_results["recent_data"] = ge_df.expect_column_values_to_be_dateutil_parseable("timestamp").success
    
    # Calculate overall validation score
    passed_validations = sum(1 for result in validation_results.values() if result)
    total_validations = len(validation_results)
    validation_score = passed_validations / total_validations
    
    validation_summary = {
        "validation_score": validation_score,
        "validations_passed": passed_validations,
        "total_validations": total_validations,
        "validation_details": validation_results,
        "validation_timestamp": datetime.utcnow().isoformat()
    }
    
    logging.info(f"Data quality validation completed: {validation_score:.2%} passed")
    
    # Fail if validation score is too low
    if validation_score < 0.8:
        raise ValueError(f"Data quality validation failed: {validation_score:.2%} < 80%")
    
    # Push results to XCom
    context["task_instance"].xcom_push(key="validation_summary", value=validation_summary)
    
    return validation_summary


def run_dbt_transformations(**context) -> Dict[str, Any]:
    """
    Execute dbt transformations for data modeling.
    
    Runs the complete dbt pipeline including:
    - Staging models
    - Intermediate transformations  
    - Mart models
    - Data quality tests
    """
    import subprocess
    import os
    
    logging.info("Starting dbt transformations")
    
    # Set dbt environment variables
    dbt_env = os.environ.copy()
    dbt_env.update({
        "DBT_PROFILES_DIR": "/opt/airflow/dbt",
        "DBT_PROJECT_DIR": "/opt/airflow/dbt/agricultural_analytics"
    })
    
    try:
        # Run dbt deps to install packages
        deps_result = subprocess.run(
            ["dbt", "deps"],
            cwd="/opt/airflow/dbt/agricultural_analytics",
            env=dbt_env,
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("dbt deps completed successfully")
        
        # Run dbt models
        run_result = subprocess.run(
            ["dbt", "run", "--profiles-dir", "/opt/airflow/dbt"],
            cwd="/opt/airflow/dbt/agricultural_analytics",
            env=dbt_env,
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("dbt run completed successfully")
        
        # Run dbt tests
        test_result = subprocess.run(
            ["dbt", "test", "--profiles-dir", "/opt/airflow/dbt"],
            cwd="/opt/airflow/dbt/agricultural_analytics",
            env=dbt_env,
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("dbt test completed successfully")
        
        # Parse dbt results
        transformation_summary = {
            "dbt_deps_success": True,
            "dbt_run_success": True,
            "dbt_test_success": True,
            "dbt_run_output": run_result.stdout,
            "dbt_test_output": test_result.stdout,
            "transformation_timestamp": datetime.utcnow().isoformat()
        }
        
    except subprocess.CalledProcessError as e:
        logging.error(f"dbt command failed: {e}")
        transformation_summary = {
            "dbt_deps_success": "deps" not in str(e),
            "dbt_run_success": "run" not in str(e),
            "dbt_test_success": "test" not in str(e),
            "error_message": str(e),
            "error_output": e.stderr,
            "transformation_timestamp": datetime.utcnow().isoformat()
        }
        raise
    
    # Push results to XCom
    context["task_instance"].xcom_push(key="transformation_summary", value=transformation_summary)
    
    return transformation_summary


def sync_to_bigquery(**context) -> Dict[str, Any]:
    """
    Sync transformed data to BigQuery analytics warehouse.
    
    Implements incremental loading with proper error handling
    and data quality validation.
    """
    from google.cloud import bigquery
    from google.oauth2 import service_account
    
    logging.info("Starting BigQuery sync")
    
    # Get transformation results
    transformation_summary = context["task_instance"].xcom_pull(
        task_ids="run_dbt_transformations",
        key="transformation_summary"
    )
    
    if not transformation_summary.get("dbt_run_success"):
        raise ValueError("dbt transformations failed, skipping BigQuery sync")
    
    # Initialize BigQuery client
    credentials_path = Variable.get("BIGQUERY_CREDENTIALS_PATH")
    project_id = Variable.get("BIGQUERY_PROJECT_ID")
    dataset_id = Variable.get("BIGQUERY_DATASET_ID")
    
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    client = bigquery.Client(project=project_id, credentials=credentials)
    
    # Connect to TimescaleDB for data extraction
    postgres_hook = PostgresHook(postgres_conn_id=PIPELINE_CONFIG["timescaledb_conn_id"])
    
    # Sync livestock health daily data
    sync_query = """
        SELECT 
            entity_id::text,
            farm_id,
            external_id,
            entity_name,
            species,
            breed,
            age_months,
            date,
            avg_heart_rate,
            min_heart_rate,
            max_heart_rate,
            avg_temperature,
            avg_activity_level,
            total_steps,
            total_rumination_time,
            health_score,
            health_status,
            total_readings,
            anomaly_count,
            avg_battery_level,
            calculated_at
        FROM livestock_health_daily
        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
    """
    
    df = postgres_hook.get_pandas_df(sync_query)
    
    if len(df) == 0:
        logging.warning("No data to sync to BigQuery")
        return {"records_synced": 0, "sync_timestamp": datetime.utcnow().isoformat()}
    
    # Load to BigQuery
    table_id = f"{project_id}.{dataset_id}.livestock_health_daily"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for job completion
    
    sync_summary = {
        "records_synced": len(df),
        "table_id": table_id,
        "job_id": job.job_id,
        "sync_timestamp": datetime.utcnow().isoformat()
    }
    
    logging.info(f"Successfully synced {len(df)} records to BigQuery")
    
    # Push results to XCom
    context["task_instance"].xcom_push(key="sync_summary", value=sync_summary)
    
    return sync_summary


def generate_pipeline_report(**context) -> Dict[str, Any]:
    """
    Generate comprehensive pipeline execution report.
    
    Collects metrics from all pipeline stages and creates
    a summary report for monitoring and alerting.
    """
    logging.info("Generating pipeline execution report")
    
    # Collect results from all tasks
    extraction_stats = context["task_instance"].xcom_pull(
        task_ids="extract_sensor_telemetry", key="extraction_stats"
    )
    
    validation_summary = context["task_instance"].xcom_pull(
        task_ids="validate_data_quality", key="validation_summary"
    )
    
    transformation_summary = context["task_instance"].xcom_pull(
        task_ids="run_dbt_transformations", key="transformation_summary"
    )
    
    sync_summary = context["task_instance"].xcom_pull(
        task_ids="sync_to_bigquery", key="sync_summary"
    )
    
    # Generate comprehensive report
    pipeline_report = {
        "dag_id": DAG_ID,
        "execution_date": context["execution_date"].isoformat(),
        "pipeline_status": "SUCCESS",
        "execution_summary": {
            "extraction": extraction_stats,
            "validation": validation_summary,
            "transformation": transformation_summary,
            "sync": sync_summary
        },
        "pipeline_metrics": {
            "total_records_processed": extraction_stats.get("records_extracted", 0),
            "data_quality_score": validation_summary.get("validation_score", 0),
            "records_synced_to_bigquery": sync_summary.get("records_synced", 0),
            "pipeline_duration_minutes": (
                datetime.utcnow() - context["execution_date"]
            ).total_seconds() / 60
        },
        "report_timestamp": datetime.utcnow().isoformat()
    }
    
    logging.info(f"Pipeline report generated: {pipeline_report['pipeline_metrics']}")
    
    # Store report for monitoring
    context["task_instance"].xcom_push(key="pipeline_report", value=pipeline_report)
    
    return pipeline_report


# Create DAG
dag = DAG(
    DAG_ID,
    default_args=default_args,
    description="Agricultural IoT Data Pipeline - Complete ETL orchestration",
    schedule_interval=SCHEDULE_INTERVAL,
    max_active_runs=MAX_ACTIVE_RUNS,
    catchup=CATCHUP,
    tags=["agricultural-iot", "etl", "data-engineering", "timescaledb", "bigquery"],
)

# Task definitions
start_pipeline = DummyOperator(
    task_id="start_pipeline",
    dag=dag,
)

# Data extraction task
extract_telemetry = PythonOperator(
    task_id="extract_sensor_telemetry",
    python_callable=extract_sensor_telemetry,
    dag=dag,
)

# Data quality validation task
validate_quality = PythonOperator(
    task_id="validate_data_quality",
    python_callable=validate_data_quality,
    dag=dag,
)

# dbt transformation task
transform_data = PythonOperator(
    task_id="run_dbt_transformations",
    python_callable=run_dbt_transformations,
    dag=dag,
)

# BigQuery sync task
sync_bigquery = PythonOperator(
    task_id="sync_to_bigquery",
    python_callable=sync_to_bigquery,
    dag=dag,
)

# Pipeline monitoring and reporting
generate_report = PythonOperator(
    task_id="generate_pipeline_report",
    python_callable=generate_pipeline_report,
    dag=dag,
    trigger_rule=TriggerRule.ALL_DONE,  # Run even if upstream tasks fail
)

# Health check tasks
with TaskGroup("health_checks", dag=dag) as health_checks:
    
    # TimescaleDB health check
    timescaledb_health = PostgresOperator(
        task_id="check_timescaledb_health",
        postgres_conn_id=PIPELINE_CONFIG["timescaledb_conn_id"],
        sql="""
            SELECT 
                COUNT(*) as hypertable_count,
                pg_size_pretty(pg_database_size(current_database())) as db_size
            FROM timescaledb_information.hypertables;
        """,
        dag=dag,
    )
    
    # API health check
    api_health = HttpSensor(
        task_id="check_api_health",
        http_conn_id="agricultural_api",
        endpoint="/health",
        timeout=30,
        poke_interval=10,
        dag=dag,
    )

# Cleanup task
cleanup_pipeline = BashOperator(
    task_id="cleanup_pipeline",
    bash_command="""
        echo "Pipeline cleanup completed"
        # Add any cleanup commands here
    """,
    dag=dag,
    trigger_rule=TriggerRule.ALL_DONE,
)

# Define task dependencies
start_pipeline >> health_checks >> extract_telemetry
extract_telemetry >> validate_quality >> transform_data
transform_data >> sync_bigquery >> generate_report
generate_report >> cleanup_pipeline
