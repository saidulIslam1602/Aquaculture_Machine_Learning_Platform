"""
TimescaleDB Utilities and Extensions

This module provides TimescaleDB-specific functionality including hypertable creation,
compression policies, retention policies, and time-series optimizations.

Industry Standards:
    - Proper hypertable configuration for time-series data
    - Automated compression for storage optimization
    - Data retention policies for compliance
    - Continuous aggregates for performance
    - Proper indexing strategies for time-series queries
"""

from sqlalchemy import text, MetaData
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from .database import engine
from .config import settings

logger = logging.getLogger(__name__)


class TimescaleDBManager:
    """
    TimescaleDB Management Utilities
    
    Provides methods for managing TimescaleDB-specific features including
    hypertables, compression, retention policies, and continuous aggregates.
    """
    
    def __init__(self):
        self.engine = engine
        
    def create_extension(self) -> bool:
        """
        Create TimescaleDB extension if not exists.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
                conn.commit()
                logger.info("TimescaleDB extension created successfully")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create TimescaleDB extension: {e}")
            return False
    
    def create_hypertable(
        self, 
        table_name: str, 
        time_column: str = "timestamp",
        chunk_time_interval: str = None,
        if_not_exists: bool = True
    ) -> bool:
        """
        Create a TimescaleDB hypertable for time-series data.
        
        Args:
            table_name: Name of the table to convert to hypertable
            time_column: Name of the time column for partitioning
            chunk_time_interval: Time interval for chunks (e.g., '1 day', '1 hour')
            if_not_exists: Whether to use IF NOT EXISTS clause
            
        Returns:
            bool: True if successful, False otherwise
        """
        chunk_interval = chunk_time_interval or settings.TIMESCALEDB_CHUNK_TIME_INTERVAL
        if_not_exists_clause = "IF NOT EXISTS" if if_not_exists else ""
        
        try:
            with self.engine.connect() as conn:
                query = text(f"""
                    SELECT create_hypertable(
                        '{table_name}', 
                        '{time_column}',
                        chunk_time_interval => INTERVAL '{chunk_interval}',
                        if_not_exists => {if_not_exists}
                    );
                """)
                conn.execute(query)
                conn.commit()
                logger.info(f"Hypertable created for {table_name} with {chunk_interval} chunks")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create hypertable for {table_name}: {e}")
            return False
    
    def enable_compression(
        self, 
        table_name: str, 
        segment_by_columns: List[str] = None,
        order_by_columns: List[str] = None,
        compress_after: str = "7 days"
    ) -> bool:
        """
        Enable compression on a hypertable.
        
        Args:
            table_name: Name of the hypertable
            segment_by_columns: Columns to segment by for compression
            order_by_columns: Columns to order by within segments
            compress_after: Time after which to compress chunks
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Enable compression
                segment_by = f"segmentby => '{','.join(segment_by_columns)}'" if segment_by_columns else ""
                order_by = f"orderby => '{','.join(order_by_columns)}'" if order_by_columns else ""
                
                compression_options = []
                if segment_by:
                    compression_options.append(segment_by)
                if order_by:
                    compression_options.append(order_by)
                
                options_clause = f", {', '.join(compression_options)}" if compression_options else ""
                
                query = text(f"""
                    ALTER TABLE {table_name} SET (
                        timescaledb.compress = true{options_clause}
                    );
                """)
                conn.execute(query)
                
                # Add compression policy
                policy_query = text(f"""
                    SELECT add_compression_policy('{table_name}', INTERVAL '{compress_after}');
                """)
                conn.execute(policy_query)
                
                conn.commit()
                logger.info(f"Compression enabled for {table_name} with {compress_after} policy")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to enable compression for {table_name}: {e}")
            return False
    
    def add_retention_policy(
        self, 
        table_name: str, 
        retention_period: str = None
    ) -> bool:
        """
        Add data retention policy to automatically drop old data.
        
        Args:
            table_name: Name of the hypertable
            retention_period: How long to retain data (e.g., '90 days')
            
        Returns:
            bool: True if successful, False otherwise
        """
        retention = retention_period or settings.TIMESCALEDB_RETENTION_POLICY
        
        try:
            with self.engine.connect() as conn:
                query = text(f"""
                    SELECT add_retention_policy('{table_name}', INTERVAL '{retention}');
                """)
                conn.execute(query)
                conn.commit()
                logger.info(f"Retention policy added for {table_name}: {retention}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to add retention policy for {table_name}: {e}")
            return False
    
    def create_continuous_aggregate(
        self,
        view_name: str,
        table_name: str,
        time_column: str,
        bucket_width: str,
        select_clause: str,
        group_by_clause: str = None,
        with_no_data: bool = True
    ) -> bool:
        """
        Create a continuous aggregate view for pre-computed aggregations.
        
        Args:
            view_name: Name of the continuous aggregate view
            table_name: Source hypertable name
            time_column: Time column for bucketing
            bucket_width: Time bucket width (e.g., '1 hour', '1 day')
            select_clause: SELECT clause for aggregation
            group_by_clause: Additional GROUP BY columns
            with_no_data: Whether to create with no initial data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                group_by_extra = f", {group_by_clause}" if group_by_clause else ""
                with_data_clause = "WITH NO DATA" if with_no_data else "WITH DATA"
                
                query = text(f"""
                    CREATE MATERIALIZED VIEW {view_name}
                    {with_data_clause}
                    AS SELECT 
                        time_bucket('{bucket_width}', {time_column}) AS time_bucket,
                        {select_clause}
                    FROM {table_name}
                    GROUP BY time_bucket{group_by_extra}
                    ORDER BY time_bucket;
                """)
                conn.execute(query)
                conn.commit()
                logger.info(f"Continuous aggregate {view_name} created for {table_name}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create continuous aggregate {view_name}: {e}")
            return False
    
    def add_refresh_policy(
        self,
        view_name: str,
        refresh_interval: str = "1 hour",
        refresh_lag: str = "30 minutes"
    ) -> bool:
        """
        Add automatic refresh policy for continuous aggregate.
        
        Args:
            view_name: Name of the continuous aggregate view
            refresh_interval: How often to refresh
            refresh_lag: Lag time to avoid refreshing incomplete data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                query = text(f"""
                    SELECT add_continuous_aggregate_policy(
                        '{view_name}',
                        start_offset => INTERVAL '{refresh_lag}',
                        end_offset => INTERVAL '1 minute',
                        schedule_interval => INTERVAL '{refresh_interval}'
                    );
                """)
                conn.execute(query)
                conn.commit()
                logger.info(f"Refresh policy added for {view_name}: {refresh_interval}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to add refresh policy for {view_name}: {e}")
            return False
    
    def get_hypertable_info(self, table_name: str) -> Optional[Dict]:
        """
        Get information about a hypertable.
        
        Args:
            table_name: Name of the hypertable
            
        Returns:
            Dict with hypertable information or None if not found
        """
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        hypertable_name,
                        owner,
                        num_dimensions,
                        num_chunks,
                        compression_enabled,
                        tablespace
                    FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = :table_name;
                """)
                result = conn.execute(query, {"table_name": table_name}).fetchone()
                
                if result:
                    return {
                        "hypertable_name": result[0],
                        "owner": result[1],
                        "num_dimensions": result[2],
                        "num_chunks": result[3],
                        "compression_enabled": result[4],
                        "tablespace": result[5]
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get hypertable info for {table_name}: {e}")
            return None
    
    def get_chunk_info(self, table_name: str) -> List[Dict]:
        """
        Get information about chunks for a hypertable.
        
        Args:
            table_name: Name of the hypertable
            
        Returns:
            List of dictionaries with chunk information
        """
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        chunk_name,
                        range_start,
                        range_end,
                        is_compressed,
                        chunk_size
                    FROM timescaledb_information.chunks 
                    WHERE hypertable_name = :table_name
                    ORDER BY range_start DESC;
                """)
                results = conn.execute(query, {"table_name": table_name}).fetchall()
                
                return [
                    {
                        "chunk_name": row[0],
                        "range_start": row[1],
                        "range_end": row[2],
                        "is_compressed": row[3],
                        "chunk_size": row[4]
                    }
                    for row in results
                ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get chunk info for {table_name}: {e}")
            return []


def initialize_timescaledb() -> bool:
    """
    Initialize TimescaleDB with required hypertables and policies.
    
    This function sets up all the necessary TimescaleDB configurations
    for the agricultural IoT platform including hypertables, compression,
    and retention policies.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    manager = TimescaleDBManager()
    
    try:
        # Create TimescaleDB extension
        if not manager.create_extension():
            return False
        
        # Create hypertable for sensor telemetry
        if not manager.create_hypertable(
            table_name="sensor_telemetry",
            time_column="timestamp",
            chunk_time_interval=settings.TIMESCALEDB_CHUNK_TIME_INTERVAL
        ):
            return False
        
        # Enable compression on sensor telemetry
        if settings.TIMESCALEDB_COMPRESSION_ENABLED:
            manager.enable_compression(
                table_name="sensor_telemetry",
                segment_by_columns=["entity_id"],
                order_by_columns=["timestamp", "sensor_id"],
                compress_after="7 days"
            )
        
        # Add retention policy
        manager.add_retention_policy(
            table_name="sensor_telemetry",
            retention_period=settings.TIMESCALEDB_RETENTION_POLICY
        )
        
        # Create continuous aggregates for common queries
        
        # Hourly aggregates
        manager.create_continuous_aggregate(
            view_name="sensor_telemetry_hourly",
            table_name="sensor_telemetry",
            time_column="timestamp",
            bucket_width="1 hour",
            select_clause="""
                entity_id,
                COUNT(*) as reading_count,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(battery_level) as avg_battery_level,
                AVG(data_quality_score) as avg_quality_score
            """,
            group_by_clause="entity_id"
        )
        
        # Daily aggregates
        manager.create_continuous_aggregate(
            view_name="sensor_telemetry_daily",
            table_name="sensor_telemetry",
            time_column="timestamp",
            bucket_width="1 day",
            select_clause="""
                entity_id,
                COUNT(*) as reading_count,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(battery_level) as avg_battery_level,
                COUNT(CASE WHEN is_anomaly = true THEN 1 END) as anomaly_count
            """,
            group_by_clause="entity_id"
        )
        
        # Add refresh policies for continuous aggregates
        manager.add_refresh_policy(
            view_name="sensor_telemetry_hourly",
            refresh_interval="30 minutes",
            refresh_lag="15 minutes"
        )
        
        manager.add_refresh_policy(
            view_name="sensor_telemetry_daily",
            refresh_interval="1 hour",
            refresh_lag="30 minutes"
        )
        
        logger.info("TimescaleDB initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"TimescaleDB initialization failed: {e}")
        return False


def get_timescaledb_stats() -> Dict:
    """
    Get TimescaleDB statistics and health information.
    
    Returns:
        Dict with TimescaleDB statistics
    """
    manager = TimescaleDBManager()
    
    try:
        with manager.engine.connect() as conn:
            # Get hypertable statistics
            hypertable_query = text("""
                SELECT 
                    COUNT(*) as total_hypertables,
                    SUM(num_chunks) as total_chunks,
                    COUNT(CASE WHEN compression_enabled THEN 1 END) as compressed_hypertables
                FROM timescaledb_information.hypertables;
            """)
            hypertable_stats = conn.execute(hypertable_query).fetchone()
            
            # Get database size
            size_query = text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_size_pretty(
                        SUM(pg_total_relation_size(schemaname||'.'||tablename))
                    ) as hypertable_size
                FROM timescaledb_information.hypertables;
            """)
            size_stats = conn.execute(size_query).fetchone()
            
            return {
                "total_hypertables": hypertable_stats[0] if hypertable_stats else 0,
                "total_chunks": hypertable_stats[1] if hypertable_stats else 0,
                "compressed_hypertables": hypertable_stats[2] if hypertable_stats else 0,
                "database_size": size_stats[0] if size_stats else "Unknown",
                "hypertable_size": size_stats[1] if size_stats else "Unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to get TimescaleDB stats: {e}")
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
