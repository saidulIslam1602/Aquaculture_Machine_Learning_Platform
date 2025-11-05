{{
  config(
    materialized='view',
    indexes=[
      {'columns': ['entity_id', 'timestamp'], 'type': 'btree'},
      {'columns': ['sensor_id', 'timestamp'], 'type': 'btree'},
      {'columns': ['timestamp'], 'type': 'btree'}
    ]
  )
}}

with source_data as (
    select
        timestamp,
        sensor_id,
        entity_id,
        metrics,
        location,
        temperature,
        battery_level,
        signal_strength,
        data_quality_score,
        is_anomaly,
        processing_flags
    from {{ source('agricultural_iot', 'sensor_telemetry') }}
    where 
        timestamp >= '{{ var("start_date") }}'
        and data_quality_score >= {{ var("data_quality_threshold") }}
),

enriched_data as (
    select
        timestamp,
        sensor_id,
        entity_id,
        
        -- Extract GPS coordinates from PostGIS geometry
        case 
            when location is not null 
            then st_x(location::geometry) 
            else null 
        end as longitude,
        
        case 
            when location is not null 
            then st_y(location::geometry) 
            else null 
        end as latitude,
        
        -- Extract common metrics from JSONB
        (metrics->>'heart_rate')::numeric as heart_rate,
        (metrics->>'activity_level')::numeric as activity_level,
        (metrics->>'rumination_time')::numeric as rumination_time,
        (metrics->>'step_count')::numeric as step_count,
        (metrics->>'lying_time')::numeric as lying_time,
        (metrics->>'eating_time')::numeric as eating_time,
        
        -- Environmental metrics
        temperature,
        (metrics->>'humidity')::numeric as humidity,
        (metrics->>'air_pressure')::numeric as air_pressure,
        
        -- Device metrics
        battery_level,
        signal_strength,
        (metrics->>'firmware_version')::text as firmware_version,
        
        -- Data quality indicators
        data_quality_score,
        is_anomaly,
        
        -- Time-based features for analysis
        extract(hour from timestamp) as hour_of_day,
        extract(dow from timestamp) as day_of_week,
        date_trunc('hour', timestamp) as hour_bucket,
        date_trunc('day', timestamp) as date_bucket,
        
        -- Full metrics JSONB for flexibility
        metrics as raw_metrics,
        processing_flags
        
    from source_data
)

select * from enriched_data

-- Data quality tests
{{ dbt_utils.generate_alias_name('sensor_telemetry_staging') }}
