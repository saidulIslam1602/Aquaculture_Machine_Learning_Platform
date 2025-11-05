"""
PySpark Batch Processing Pipeline for Agricultural IoT Data

This module provides comprehensive batch processing capabilities for large-scale
agricultural IoT data using Apache Spark. It includes data transformation,
aggregation, feature engineering, and analytics processing.

Key Features:
- Scalable batch processing with PySpark
- Advanced agricultural analytics and aggregations
- Feature engineering for ML models
- Data lake integration with Delta Lake
- Performance optimization and partitioning
- Comprehensive error handling and monitoring

Industry Standards:
- Spark SQL optimization
- Delta Lake ACID transactions
- Proper resource management
- Data quality validation
- Incremental processing patterns
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import os

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, avg, sum as spark_sum, count, max as spark_max, min as spark_min,
    stddev, percentile_approx, window, lag, lead, row_number, rank, dense_rank,
    explode, split, regexp_extract, to_timestamp, date_format, dayofweek,
    hour, minute, unix_timestamp, from_unixtime, coalesce, isnan, isnull,
    monotonically_increasing_id, broadcast, collect_list, collect_set,
    array_contains, size, sort_array, slice as spark_slice
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, 
    TimestampType, BooleanType, ArrayType, MapType, DecimalType
)
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler, StandardScaler, PCA
from pyspark.ml.clustering import KMeans
from pyspark.ml.stat import Correlation
import pyspark.sql.functions as F

from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable


class AgriculturalBatchProcessor:
    """
    Comprehensive batch processing system for agricultural IoT data.
    
    Provides scalable data processing, analytics, and feature engineering
    capabilities using Apache Spark and Delta Lake.
    """
    
    def __init__(self, app_name: str = "AgriculturalIoTBatchProcessor"):
        self.logger = logging.getLogger(__name__)
        self.app_name = app_name
        
        # Initialize Spark session with Delta Lake
        self.spark = self._create_spark_session()
        
        # Configuration
        self.config = {
            "batch_size": 100000,
            "partition_columns": ["farm_id", "date"],
            "checkpoint_location": "/tmp/spark-checkpoints",
            "delta_lake_path": "/data/delta-lake",
            "max_records_per_file": 1000000,
            "shuffle_partitions": 200
        }
        
        # Schema definitions
        self.schemas = self._define_schemas()
        
        self.logger.info(f"Initialized {app_name} with Spark {self.spark.version}")
    
    def _create_spark_session(self) -> SparkSession:
        """Create optimized Spark session with Delta Lake support."""
        try:
            # Configure Spark with Delta Lake
            builder = SparkSession.builder \
                .appName(self.app_name) \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skewJoin.enabled", "true") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10000")
            
            # Configure Delta Lake
            spark = configure_spark_with_delta_pip(builder).getOrCreate()
            
            # Set log level
            spark.sparkContext.setLogLevel("WARN")
            
            return spark
            
        except Exception as e:
            self.logger.error(f"Error creating Spark session: {e}")
            raise
    
    def _define_schemas(self) -> Dict[str, StructType]:
        """Define schemas for agricultural IoT data structures."""
        return {
            "sensor_telemetry": StructType([
                StructField("timestamp", TimestampType(), False),
                StructField("sensor_id", StringType(), False),
                StructField("entity_id", StringType(), False),
                StructField("farm_id", StringType(), False),
                StructField("latitude", DoubleType(), True),
                StructField("longitude", DoubleType(), True),
                StructField("temperature", DoubleType(), True),
                StructField("heart_rate", IntegerType(), True),
                StructField("activity_level", DoubleType(), True),
                StructField("step_count", IntegerType(), True),
                StructField("rumination_time", IntegerType(), True),
                StructField("battery_level", DoubleType(), True),
                StructField("signal_strength", DoubleType(), True),
                StructField("data_quality_score", DoubleType(), True),
                StructField("is_anomaly", BooleanType(), True)
            ]),
            
            "entities": StructType([
                StructField("id", StringType(), False),
                StructField("farm_id", StringType(), False),
                StructField("entity_type", StringType(), False),
                StructField("external_id", StringType(), True),
                StructField("entity_name", StringType(), True),
                StructField("species", StringType(), True),
                StructField("breed", StringType(), True),
                StructField("age_months", IntegerType(), True),
                StructField("weight_kg", DoubleType(), True),
                StructField("created_at", TimestampType(), False),
                StructField("is_active", BooleanType(), True)
            ]),
            
            "weather_data": StructType([
                StructField("timestamp", TimestampType(), False),
                StructField("farm_id", StringType(), False),
                StructField("temperature_celsius", DoubleType(), True),
                StructField("humidity_percent", DoubleType(), True),
                StructField("wind_speed_kmh", DoubleType(), True),
                StructField("precipitation_mm", DoubleType(), True),
                StructField("pressure_hpa", DoubleType(), True)
            ])
        }
    
    def load_data_from_timescaledb(self, table_name: str, 
                                  start_date: str, end_date: str) -> DataFrame:
        """
        Load data from TimescaleDB with optimized partitioning.
        
        Args:
            table_name: Name of the table to load
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Spark DataFrame with loaded data
        """
        try:
            self.logger.info(f"Loading {table_name} data from {start_date} to {end_date}")
            
            # JDBC connection properties
            jdbc_properties = {
                "user": "agricultural_iot",
                "password": "agricultural_iot123",
                "driver": "org.postgresql.Driver",
                "fetchsize": "10000",
                "batchsize": "10000"
            }
            
            # Construct query with date filtering
            query = f"""
                (SELECT * FROM {table_name} 
                 WHERE timestamp >= '{start_date}' 
                   AND timestamp < '{end_date}' + INTERVAL '1 day'
                ) as filtered_data
            """
            
            # Load data with partitioning
            df = self.spark.read \
                .format("jdbc") \
                .option("url", "jdbc:postgresql://timescaledb:5432/agricultural_iot_db") \
                .option("dbtable", query) \
                .options(**jdbc_properties) \
                .load()
            
            # Add derived columns
            df = df.withColumn("date", F.date_format(col("timestamp"), "yyyy-MM-dd")) \
                   .withColumn("hour", F.hour(col("timestamp"))) \
                   .withColumn("day_of_week", F.dayofweek(col("timestamp")))
            
            # Cache for multiple operations
            df.cache()
            
            record_count = df.count()
            self.logger.info(f"Loaded {record_count:,} records from {table_name}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data from {table_name}: {e}")
            raise
    
    def process_livestock_health_analytics(self, telemetry_df: DataFrame, 
                                         entities_df: DataFrame) -> DataFrame:
        """
        Process comprehensive livestock health analytics.
        
        Args:
            telemetry_df: Sensor telemetry data
            entities_df: Entity metadata
            
        Returns:
            DataFrame with health analytics
        """
        try:
            self.logger.info("Processing livestock health analytics")
            
            # Join telemetry with entity metadata
            livestock_df = telemetry_df.join(
                entities_df.filter(col("entity_type") == "livestock"),
                "entity_id",
                "inner"
            )
            
            # Define window specifications
            daily_window = Window.partitionBy("entity_id", "date").orderBy("timestamp")
            weekly_window = Window.partitionBy("entity_id").orderBy("date").rowsBetween(-6, 0)
            
            # Calculate daily health metrics
            daily_health = livestock_df.groupBy("entity_id", "farm_id", "date", "species", "breed") \
                .agg(
                    # Basic vital signs
                    avg("heart_rate").alias("avg_heart_rate"),
                    spark_min("heart_rate").alias("min_heart_rate"),
                    spark_max("heart_rate").alias("max_heart_rate"),
                    stddev("heart_rate").alias("stddev_heart_rate"),
                    
                    # Temperature metrics
                    avg("temperature").alias("avg_temperature"),
                    spark_min("temperature").alias("min_temperature"),
                    spark_max("temperature").alias("max_temperature"),
                    
                    # Activity metrics
                    avg("activity_level").alias("avg_activity_level"),
                    spark_sum("step_count").alias("total_steps"),
                    spark_sum("rumination_time").alias("total_rumination_time"),
                    
                    # Data quality metrics
                    avg("data_quality_score").alias("avg_data_quality"),
                    count("*").alias("total_readings"),
                    spark_sum(when(col("is_anomaly"), 1).otherwise(0)).alias("anomaly_count"),
                    
                    # Battery and connectivity
                    avg("battery_level").alias("avg_battery_level"),
                    avg("signal_strength").alias("avg_signal_strength")
                )
            
            # Calculate health scores using species-specific thresholds
            health_scored = daily_health.withColumn(
                "heart_rate_score",
                when(col("species") == "cattle",
                     when((col("avg_heart_rate") >= 60) & (col("avg_heart_rate") <= 80), 1.0)
                     .when((col("avg_heart_rate") >= 50) & (col("avg_heart_rate") <= 90), 0.8)
                     .otherwise(0.5)
                ).when(col("species") == "sheep",
                     when((col("avg_heart_rate") >= 70) & (col("avg_heart_rate") <= 90), 1.0)
                     .when((col("avg_heart_rate") >= 60) & (col("avg_heart_rate") <= 100), 0.8)
                     .otherwise(0.5)
                ).otherwise(0.7)
            ).withColumn(
                "activity_score",
                when(col("avg_activity_level") >= 5.0, 1.0)
                .when(col("avg_activity_level") >= 3.0, 0.8)
                .when(col("avg_activity_level") >= 1.0, 0.6)
                .otherwise(0.3)
            ).withColumn(
                "temperature_score",
                when((col("avg_temperature") >= 38.0) & (col("avg_temperature") <= 39.5), 1.0)
                .when((col("avg_temperature") >= 37.0) & (col("avg_temperature") <= 40.0), 0.8)
                .otherwise(0.5)
            )
            
            # Calculate overall health score
            health_final = health_scored.withColumn(
                "health_score",
                (col("heart_rate_score") * 0.3 + 
                 col("activity_score") * 0.3 + 
                 col("temperature_score") * 0.2 + 
                 col("avg_data_quality") * 0.2)
            ).withColumn(
                "health_status",
                when(col("health_score") >= 0.8, "excellent")
                .when(col("health_score") >= 0.6, "good")
                .when(col("health_score") >= 0.4, "fair")
                .otherwise("poor")
            )
            
            # Add trend analysis using window functions
            health_with_trends = health_final.withColumn(
                "prev_health_score",
                lag("health_score", 1).over(weekly_window)
            ).withColumn(
                "health_trend",
                when(col("health_score") > col("prev_health_score") + 0.1, "improving")
                .when(col("health_score") < col("prev_health_score") - 0.1, "declining")
                .otherwise("stable")
            ).withColumn(
                "weekly_avg_health",
                avg("health_score").over(weekly_window)
            )
            
            # Add calculated timestamp
            health_analytics = health_with_trends.withColumn(
                "calculated_at",
                F.current_timestamp()
            )
            
            self.logger.info("Livestock health analytics processing completed")
            return health_analytics
            
        except Exception as e:
            self.logger.error(f"Error processing livestock health analytics: {e}")
            raise
    
    def process_behavioral_patterns(self, telemetry_df: DataFrame) -> DataFrame:
        """
        Analyze behavioral patterns and detect anomalies.
        
        Args:
            telemetry_df: Sensor telemetry data
            
        Returns:
            DataFrame with behavioral pattern analysis
        """
        try:
            self.logger.info("Processing behavioral pattern analysis")
            
            # Define time-based windows
            hourly_window = Window.partitionBy("entity_id", "date", "hour").orderBy("timestamp")
            daily_window = Window.partitionBy("entity_id", "date").orderBy("hour")
            
            # Calculate hourly activity patterns
            hourly_patterns = telemetry_df.groupBy("entity_id", "farm_id", "date", "hour") \
                .agg(
                    avg("activity_level").alias("avg_hourly_activity"),
                    spark_sum("step_count").alias("hourly_steps"),
                    avg("heart_rate").alias("avg_hourly_heart_rate"),
                    count("*").alias("hourly_readings")
                )
            
            # Identify feeding times (high activity periods)
            feeding_patterns = hourly_patterns.withColumn(
                "is_feeding_time",
                when(col("avg_hourly_activity") > 7.0, True).otherwise(False)
            ).withColumn(
                "is_resting_time",
                when(col("avg_hourly_activity") < 2.0, True).otherwise(False)
            )
            
            # Calculate daily behavioral metrics
            daily_behavior = feeding_patterns.groupBy("entity_id", "farm_id", "date") \
                .agg(
                    # Activity distribution
                    spark_sum(when(col("is_feeding_time"), 1).otherwise(0)).alias("feeding_hours"),
                    spark_sum(when(col("is_resting_time"), 1).otherwise(0)).alias("resting_hours"),
                    spark_max("avg_hourly_activity").alias("peak_activity"),
                    spark_min("avg_hourly_activity").alias("min_activity"),
                    
                    # Movement patterns
                    spark_sum("hourly_steps").alias("daily_steps"),
                    avg("avg_hourly_heart_rate").alias("avg_daily_heart_rate"),
                    stddev("avg_hourly_activity").alias("activity_variability"),
                    
                    # Collect activity by hour for pattern analysis
                    collect_list("avg_hourly_activity").alias("hourly_activity_pattern")
                )
            
            # Add behavioral scores
            behavioral_scored = daily_behavior.withColumn(
                "activity_regularity_score",
                when(col("activity_variability") < 2.0, 1.0)
                .when(col("activity_variability") < 3.0, 0.8)
                .otherwise(0.6)
            ).withColumn(
                "movement_score",
                when(col("daily_steps") >= 5000, 1.0)
                .when(col("daily_steps") >= 3000, 0.8)
                .when(col("daily_steps") >= 1000, 0.6)
                .otherwise(0.3)
            ).withColumn(
                "rest_balance_score",
                when((col("resting_hours") >= 6) & (col("resting_hours") <= 10), 1.0)
                .when((col("resting_hours") >= 4) & (col("resting_hours") <= 12), 0.8)
                .otherwise(0.5)
            )
            
            # Calculate overall behavioral health score
            behavioral_final = behavioral_scored.withColumn(
                "behavioral_health_score",
                (col("activity_regularity_score") * 0.4 + 
                 col("movement_score") * 0.3 + 
                 col("rest_balance_score") * 0.3)
            ).withColumn(
                "behavioral_status",
                when(col("behavioral_health_score") >= 0.8, "normal")
                .when(col("behavioral_health_score") >= 0.6, "minor_concern")
                .when(col("behavioral_health_score") >= 0.4, "moderate_concern")
                .otherwise("significant_concern")
            )
            
            # Add anomaly detection flags
            behavioral_anomalies = behavioral_final.withColumn(
                "is_behavioral_anomaly",
                when((col("behavioral_health_score") < 0.4) | 
                     (col("daily_steps") < 500) | 
                     (col("peak_activity") < 1.0), True)
                .otherwise(False)
            ).withColumn(
                "calculated_at",
                F.current_timestamp()
            )
            
            self.logger.info("Behavioral pattern analysis completed")
            return behavioral_anomalies
            
        except Exception as e:
            self.logger.error(f"Error processing behavioral patterns: {e}")
            raise
    
    def process_environmental_correlation(self, telemetry_df: DataFrame, 
                                       weather_df: DataFrame) -> DataFrame:
        """
        Analyze correlation between environmental factors and animal behavior.
        
        Args:
            telemetry_df: Sensor telemetry data
            weather_df: Weather data
            
        Returns:
            DataFrame with environmental correlation analysis
        """
        try:
            self.logger.info("Processing environmental correlation analysis")
            
            # Aggregate telemetry by hour and farm
            hourly_telemetry = telemetry_df.groupBy("farm_id", "date", "hour") \
                .agg(
                    avg("activity_level").alias("avg_activity"),
                    avg("heart_rate").alias("avg_heart_rate"),
                    avg("temperature").alias("avg_body_temp"),
                    count("entity_id").alias("active_animals")
                )
            
            # Aggregate weather by hour and farm
            hourly_weather = weather_df.groupBy("farm_id", "date", "hour") \
                .agg(
                    avg("temperature_celsius").alias("ambient_temp"),
                    avg("humidity_percent").alias("humidity"),
                    avg("wind_speed_kmh").alias("wind_speed"),
                    spark_sum("precipitation_mm").alias("precipitation")
                )
            
            # Join telemetry and weather data
            combined_df = hourly_telemetry.join(
                hourly_weather,
                ["farm_id", "date", "hour"],
                "inner"
            )
            
            # Calculate environmental stress indicators
            environmental_analysis = combined_df.withColumn(
                "heat_stress_index",
                when(col("ambient_temp") > 25.0, 
                     (col("ambient_temp") - 25.0) * col("humidity") / 100.0)
                .otherwise(0.0)
            ).withColumn(
                "cold_stress_index",
                when(col("ambient_temp") < 5.0,
                     (5.0 - col("ambient_temp")) * (col("wind_speed") / 10.0))
                .otherwise(0.0)
            ).withColumn(
                "weather_comfort_score",
                when((col("ambient_temp") >= 15.0) & (col("ambient_temp") <= 25.0) &
                     (col("humidity") <= 70.0) & (col("wind_speed") <= 20.0), 1.0)
                .when((col("ambient_temp") >= 10.0) & (col("ambient_temp") <= 30.0) &
                     (col("humidity") <= 80.0), 0.8)
                .otherwise(0.5)
            )
            
            # Analyze activity correlation with weather
            weather_correlation = environmental_analysis.withColumn(
                "temp_activity_correlation",
                when(col("ambient_temp") > 30.0, 
                     when(col("avg_activity") < 3.0, "heat_reduced_activity").otherwise("heat_tolerant"))
                .when(col("ambient_temp") < 0.0,
                     when(col("avg_activity") < 2.0, "cold_reduced_activity").otherwise("cold_tolerant"))
                .otherwise("normal_activity")
            ).withColumn(
                "precipitation_impact",
                when(col("precipitation") > 5.0,
                     when(col("avg_activity") < 2.0, "rain_avoidance").otherwise("rain_tolerant"))
                .otherwise("no_precipitation_impact")
            )
            
            # Calculate daily environmental summaries
            daily_environmental = weather_correlation.groupBy("farm_id", "date") \
                .agg(
                    avg("heat_stress_index").alias("avg_heat_stress"),
                    avg("cold_stress_index").alias("avg_cold_stress"),
                    avg("weather_comfort_score").alias("avg_comfort_score"),
                    avg("avg_activity").alias("daily_avg_activity"),
                    spark_sum("precipitation").alias("daily_precipitation"),
                    spark_max("ambient_temp").alias("max_temp"),
                    spark_min("ambient_temp").alias("min_temp")
                )
            
            # Add environmental recommendations
            environmental_final = daily_environmental.withColumn(
                "environmental_recommendation",
                when(col("avg_heat_stress") > 2.0, "provide_shade_and_water")
                .when(col("avg_cold_stress") > 2.0, "provide_shelter")
                .when(col("daily_precipitation") > 20.0, "ensure_dry_areas")
                .when(col("avg_comfort_score") < 0.6, "monitor_animal_welfare")
                .otherwise("optimal_conditions")
            ).withColumn(
                "calculated_at",
                F.current_timestamp()
            )
            
            self.logger.info("Environmental correlation analysis completed")
            return environmental_final
            
        except Exception as e:
            self.logger.error(f"Error processing environmental correlation: {e}")
            raise
    
    def create_ml_features(self, telemetry_df: DataFrame, 
                          entities_df: DataFrame) -> DataFrame:
        """
        Create comprehensive feature set for machine learning models.
        
        Args:
            telemetry_df: Sensor telemetry data
            entities_df: Entity metadata
            
        Returns:
            DataFrame with ML features
        """
        try:
            self.logger.info("Creating ML feature set")
            
            # Join with entity metadata
            featured_df = telemetry_df.join(entities_df, "entity_id", "inner")
            
            # Time-based features
            time_features = featured_df.withColumn(
                "hour_sin", F.sin(2 * 3.14159 * col("hour") / 24)
            ).withColumn(
                "hour_cos", F.cos(2 * 3.14159 * col("hour") / 24)
            ).withColumn(
                "day_sin", F.sin(2 * 3.14159 * col("day_of_week") / 7)
            ).withColumn(
                "day_cos", F.cos(2 * 3.14159 * col("day_of_week") / 7)
            ).withColumn(
                "is_weekend", when(col("day_of_week").isin([1, 7]), 1).otherwise(0)
            ).withColumn(
                "is_night", when((col("hour") >= 22) | (col("hour") <= 6), 1).otherwise(0)
            )
            
            # Rolling window features (3-hour windows)
            window_3h = Window.partitionBy("entity_id").orderBy("timestamp").rowsBetween(-11, 0)
            
            rolling_features = time_features.withColumn(
                "heart_rate_3h_avg", avg("heart_rate").over(window_3h)
            ).withColumn(
                "heart_rate_3h_std", stddev("heart_rate").over(window_3h)
            ).withColumn(
                "activity_3h_avg", avg("activity_level").over(window_3h)
            ).withColumn(
                "activity_3h_max", spark_max("activity_level").over(window_3h)
            ).withColumn(
                "temp_3h_avg", avg("temperature").over(window_3h)
            ).withColumn(
                "steps_3h_sum", spark_sum("step_count").over(window_3h)
            )
            
            # Lag features
            lag_features = rolling_features.withColumn(
                "heart_rate_lag_1h", lag("heart_rate", 4).over(window_3h)
            ).withColumn(
                "activity_lag_1h", lag("activity_level", 4).over(window_3h)
            ).withColumn(
                "temp_lag_1h", lag("temperature", 4).over(window_3h)
            )
            
            # Derived features
            derived_features = lag_features.withColumn(
                "heart_rate_change", col("heart_rate") - col("heart_rate_lag_1h")
            ).withColumn(
                "activity_change", col("activity_level") - col("activity_lag_1h")
            ).withColumn(
                "temp_change", col("temperature") - col("temp_lag_1h")
            ).withColumn(
                "heart_rate_normalized", 
                (col("heart_rate") - col("heart_rate_3h_avg")) / 
                coalesce(col("heart_rate_3h_std"), F.lit(1.0))
            ).withColumn(
                "activity_intensity", 
                col("activity_level") / coalesce(col("activity_3h_avg"), F.lit(1.0))
            )
            
            # Animal-specific features
            animal_features = derived_features.withColumn(
                "age_category",
                when(col("age_months") < 6, "young")
                .when(col("age_months") < 24, "adult")
                .otherwise("mature")
            ).withColumn(
                "weight_category",
                when(col("weight_kg") < 200, "light")
                .when(col("weight_kg") < 500, "medium")
                .otherwise("heavy")
            )
            
            # Data quality features
            quality_features = animal_features.withColumn(
                "signal_quality_category",
                when(col("signal_strength") > -70, "excellent")
                .when(col("signal_strength") > -85, "good")
                .when(col("signal_strength") > -100, "fair")
                .otherwise("poor")
            ).withColumn(
                "battery_status",
                when(col("battery_level") > 80, "high")
                .when(col("battery_level") > 50, "medium")
                .when(col("battery_level") > 20, "low")
                .otherwise("critical")
            )
            
            # Select final feature set
            ml_features = quality_features.select(
                # Identifiers
                "entity_id", "farm_id", "timestamp", "date", "hour",
                
                # Raw sensor data
                "heart_rate", "activity_level", "temperature", "step_count",
                "rumination_time", "battery_level", "signal_strength",
                
                # Time features
                "hour_sin", "hour_cos", "day_sin", "day_cos", "is_weekend", "is_night",
                
                # Rolling features
                "heart_rate_3h_avg", "heart_rate_3h_std", "activity_3h_avg", 
                "activity_3h_max", "temp_3h_avg", "steps_3h_sum",
                
                # Lag and change features
                "heart_rate_lag_1h", "activity_lag_1h", "temp_lag_1h",
                "heart_rate_change", "activity_change", "temp_change",
                
                # Normalized features
                "heart_rate_normalized", "activity_intensity",
                
                # Categorical features
                "species", "breed", "age_category", "weight_category",
                "signal_quality_category", "battery_status",
                
                # Target variables
                "data_quality_score", "is_anomaly"
            )
            
            self.logger.info("ML feature creation completed")
            return ml_features
            
        except Exception as e:
            self.logger.error(f"Error creating ML features: {e}")
            raise
    
    def save_to_delta_lake(self, df: DataFrame, table_name: str, 
                          partition_columns: List[str] = None) -> None:
        """
        Save DataFrame to Delta Lake with optimized partitioning.
        
        Args:
            df: DataFrame to save
            table_name: Name of the Delta table
            partition_columns: Columns to partition by
        """
        try:
            self.logger.info(f"Saving {table_name} to Delta Lake")
            
            delta_path = f"{self.config['delta_lake_path']}/{table_name}"
            partition_cols = partition_columns or self.config["partition_columns"]
            
            # Write to Delta Lake with optimizations
            writer = df.write \
                .format("delta") \
                .mode("overwrite") \
                .option("mergeSchema", "true") \
                .option("overwriteSchema", "true")
            
            if partition_cols:
                writer = writer.partitionBy(*partition_cols)
            
            writer.save(delta_path)
            
            # Optimize table
            delta_table = DeltaTable.forPath(self.spark, delta_path)
            delta_table.optimize().executeCompaction()
            
            # Generate statistics
            self.spark.sql(f"ANALYZE TABLE delta.`{delta_path}` COMPUTE STATISTICS")
            
            record_count = df.count()
            self.logger.info(f"Saved {record_count:,} records to {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error saving to Delta Lake: {e}")
            raise
    
    def run_comprehensive_batch_processing(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Run comprehensive batch processing pipeline.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Processing summary
        """
        try:
            self.logger.info(f"Starting comprehensive batch processing: {start_date} to {end_date}")
            
            processing_summary = {
                "start_time": datetime.utcnow().isoformat(),
                "date_range": {"start": start_date, "end": end_date},
                "tables_processed": {},
                "processing_metrics": {}
            }
            
            # Load source data
            telemetry_df = self.load_data_from_timescaledb("sensor_telemetry", start_date, end_date)
            entities_df = self.load_data_from_timescaledb("entities", start_date, end_date)
            
            # Process livestock health analytics
            health_analytics = self.process_livestock_health_analytics(telemetry_df, entities_df)
            self.save_to_delta_lake(health_analytics, "livestock_health_analytics")
            processing_summary["tables_processed"]["livestock_health_analytics"] = health_analytics.count()
            
            # Process behavioral patterns
            behavioral_patterns = self.process_behavioral_patterns(telemetry_df)
            self.save_to_delta_lake(behavioral_patterns, "behavioral_patterns")
            processing_summary["tables_processed"]["behavioral_patterns"] = behavioral_patterns.count()
            
            # Create ML features
            ml_features = self.create_ml_features(telemetry_df, entities_df)
            self.save_to_delta_lake(ml_features, "ml_features", ["farm_id", "date", "hour"])
            processing_summary["tables_processed"]["ml_features"] = ml_features.count()
            
            # Calculate processing metrics
            processing_summary["processing_metrics"] = {
                "total_records_processed": telemetry_df.count(),
                "total_entities": entities_df.count(),
                "processing_duration_minutes": (
                    datetime.utcnow() - datetime.fromisoformat(processing_summary["start_time"])
                ).total_seconds() / 60
            }
            
            processing_summary["end_time"] = datetime.utcnow().isoformat()
            processing_summary["status"] = "completed"
            
            self.logger.info("Comprehensive batch processing completed successfully")
            return processing_summary
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive batch processing: {e}")
            processing_summary["status"] = "failed"
            processing_summary["error"] = str(e)
            raise
    
    def cleanup(self):
        """Clean up Spark resources."""
        try:
            if self.spark:
                self.spark.stop()
                self.logger.info("Spark session stopped")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Initialize batch processor
batch_processor = AgriculturalBatchProcessor()


def run_batch_processing_job(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Run the complete batch processing job.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Processing summary
    """
    try:
        # Run comprehensive processing
        summary = batch_processor.run_comprehensive_batch_processing(start_date, end_date)
        
        return summary
        
    except Exception as e:
        logging.error(f"Error in batch processing job: {e}")
        raise
    finally:
        # Cleanup resources
        batch_processor.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run batch processing for yesterday
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    summary = run_batch_processing_job(yesterday, yesterday)
    print(json.dumps(summary, indent=2, default=str))
