-- TimescaleDB Initialization Script for Agricultural IoT Platform
-- This script sets up the database with TimescaleDB extension and PostGIS for geospatial data

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create additional useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create schemas for different data domains
CREATE SCHEMA IF NOT EXISTS agricultural_iot;
CREATE SCHEMA IF NOT EXISTS dbt_dev;
CREATE SCHEMA IF NOT EXISTS dbt_prod;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS seeds;
CREATE SCHEMA IF NOT EXISTS snapshots;

-- Set default search path
ALTER DATABASE agricultural_iot_db SET search_path TO agricultural_iot, public;

-- Create roles for different access levels
CREATE ROLE IF NOT EXISTS agricultural_iot_read;
CREATE ROLE IF NOT EXISTS agricultural_iot_write;
CREATE ROLE IF NOT EXISTS agricultural_iot_admin;

-- Grant permissions
GRANT CONNECT ON DATABASE agricultural_iot_db TO agricultural_iot_read;
GRANT CONNECT ON DATABASE agricultural_iot_db TO agricultural_iot_write;
GRANT CONNECT ON DATABASE agricultural_iot_db TO agricultural_iot_admin;

GRANT USAGE ON SCHEMA agricultural_iot TO agricultural_iot_read;
GRANT USAGE ON SCHEMA agricultural_iot TO agricultural_iot_write;
GRANT ALL ON SCHEMA agricultural_iot TO agricultural_iot_admin;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA agricultural_iot 
    GRANT SELECT ON TABLES TO agricultural_iot_read;

ALTER DEFAULT PRIVILEGES IN SCHEMA agricultural_iot 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO agricultural_iot_write;

ALTER DEFAULT PRIVILEGES IN SCHEMA agricultural_iot 
    GRANT ALL ON TABLES TO agricultural_iot_admin;

-- Create function to automatically create hypertables
CREATE OR REPLACE FUNCTION create_hypertable_if_not_exists(
    table_name TEXT,
    time_column TEXT,
    chunk_time_interval INTERVAL DEFAULT INTERVAL '1 day'
) RETURNS VOID AS $$
BEGIN
    -- Check if table is already a hypertable
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables 
        WHERE hypertable_name = table_name
    ) THEN
        -- Create hypertable
        PERFORM create_hypertable(table_name, time_column, chunk_time_interval => chunk_time_interval);
        RAISE NOTICE 'Created hypertable: %', table_name;
    ELSE
        RAISE NOTICE 'Hypertable already exists: %', table_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create function to setup compression policy
CREATE OR REPLACE FUNCTION setup_compression_policy(
    table_name TEXT,
    compress_after INTERVAL DEFAULT INTERVAL '7 days',
    segment_by TEXT[] DEFAULT NULL,
    order_by TEXT[] DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    compression_sql TEXT;
BEGIN
    -- Enable compression
    compression_sql := format('ALTER TABLE %I SET (timescaledb.compress = true', table_name);
    
    IF segment_by IS NOT NULL THEN
        compression_sql := compression_sql || format(', timescaledb.compress_segmentby = %L', array_to_string(segment_by, ','));
    END IF;
    
    IF order_by IS NOT NULL THEN
        compression_sql := compression_sql || format(', timescaledb.compress_orderby = %L', array_to_string(order_by, ','));
    END IF;
    
    compression_sql := compression_sql || ')';
    
    EXECUTE compression_sql;
    
    -- Add compression policy
    PERFORM add_compression_policy(table_name, compress_after);
    
    RAISE NOTICE 'Setup compression for table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- Create function to setup retention policy
CREATE OR REPLACE FUNCTION setup_retention_policy(
    table_name TEXT,
    retention_period INTERVAL DEFAULT INTERVAL '90 days'
) RETURNS VOID AS $$
BEGIN
    PERFORM add_retention_policy(table_name, retention_period);
    RAISE NOTICE 'Setup retention policy for table: % (retain for %)', table_name, retention_period;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for common query patterns
CREATE OR REPLACE FUNCTION create_timeseries_indexes(
    table_name TEXT,
    time_column TEXT DEFAULT 'timestamp',
    entity_column TEXT DEFAULT 'entity_id'
) RETURNS VOID AS $$
BEGIN
    -- Create indexes for common query patterns
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_time_entity ON %I (%I DESC, %I)', 
                   table_name, table_name, time_column, entity_column);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_entity_time ON %I (%I, %I DESC)', 
                   table_name, table_name, entity_column, time_column);
    
    RAISE NOTICE 'Created time-series indexes for table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view refresh function
CREATE OR REPLACE FUNCTION refresh_continuous_aggregates() RETURNS VOID AS $$
DECLARE
    agg_record RECORD;
BEGIN
    FOR agg_record IN 
        SELECT view_name 
        FROM timescaledb_information.continuous_aggregates 
        WHERE materialized_only = false
    LOOP
        EXECUTE format('CALL refresh_continuous_aggregate(%L, NULL, NULL)', agg_record.view_name);
        RAISE NOTICE 'Refreshed continuous aggregate: %', agg_record.view_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create data quality check function
CREATE OR REPLACE FUNCTION check_data_quality(
    table_name TEXT,
    time_column TEXT DEFAULT 'timestamp',
    quality_column TEXT DEFAULT 'data_quality_score',
    threshold NUMERIC DEFAULT 0.7
) RETURNS TABLE(
    total_rows BIGINT,
    low_quality_rows BIGINT,
    quality_percentage NUMERIC,
    latest_data TIMESTAMP,
    oldest_data TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY EXECUTE format('
        SELECT 
            COUNT(*)::BIGINT as total_rows,
            COUNT(CASE WHEN %I < %s THEN 1 END)::BIGINT as low_quality_rows,
            ROUND(
                (COUNT(CASE WHEN %I >= %s THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC) * 100, 2
            ) as quality_percentage,
            MAX(%I) as latest_data,
            MIN(%I) as oldest_data
        FROM %I
        WHERE %I >= NOW() - INTERVAL ''24 hours''',
        quality_column, threshold,
        quality_column, threshold,
        time_column,
        time_column,
        table_name,
        time_column
    );
END;
$$ LANGUAGE plpgsql;

-- Create performance monitoring view
CREATE OR REPLACE VIEW timescaledb_stats AS
SELECT 
    h.hypertable_name,
    h.owner,
    h.num_dimensions,
    h.num_chunks,
    h.compression_enabled,
    pg_size_pretty(
        (SELECT SUM(pg_total_relation_size(format('%I.%I', chunk_schema, chunk_name)))
         FROM timescaledb_information.chunks c 
         WHERE c.hypertable_name = h.hypertable_name)
    ) as total_size,
    (SELECT COUNT(*) 
     FROM timescaledb_information.chunks c 
     WHERE c.hypertable_name = h.hypertable_name 
     AND c.is_compressed = true) as compressed_chunks
FROM timescaledb_information.hypertables h;

-- Grant permissions on utility functions
GRANT EXECUTE ON FUNCTION create_hypertable_if_not_exists TO agricultural_iot_admin;
GRANT EXECUTE ON FUNCTION setup_compression_policy TO agricultural_iot_admin;
GRANT EXECUTE ON FUNCTION setup_retention_policy TO agricultural_iot_admin;
GRANT EXECUTE ON FUNCTION create_timeseries_indexes TO agricultural_iot_admin;
GRANT EXECUTE ON FUNCTION refresh_continuous_aggregates TO agricultural_iot_admin;
GRANT EXECUTE ON FUNCTION check_data_quality TO agricultural_iot_read, agricultural_iot_write, agricultural_iot_admin;

GRANT SELECT ON timescaledb_stats TO agricultural_iot_read, agricultural_iot_write, agricultural_iot_admin;

-- Create notification for successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialization completed successfully';
    RAISE NOTICE 'Database: agricultural_iot_db';
    RAISE NOTICE 'Extensions: timescaledb, postgis, uuid-ossp, pg_stat_statements';
    RAISE NOTICE 'Schemas: agricultural_iot, dbt_dev, dbt_prod, staging, marts, seeds, snapshots';
    RAISE NOTICE 'Utility functions and views created';
END $$;
