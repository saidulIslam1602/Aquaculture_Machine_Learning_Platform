{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['entity_id', 'date'], 'unique': true},
      {'columns': ['farm_id', 'date'], 'type': 'btree'},
      {'columns': ['health_score'], 'type': 'btree'}
    ],
    post_hook="CREATE INDEX IF NOT EXISTS idx_livestock_health_daily_composite ON {{ this }} (farm_id, date, health_score)"
  )
}}

with daily_telemetry as (
    select
        t.entity_id,
        e.farm_id,
        e.external_id,
        e.entity_name,
        e.species,
        e.breed,
        e.age_months,
        t.date_bucket as date,
        
        -- Vital signs aggregations
        avg(t.heart_rate) as avg_heart_rate,
        min(t.heart_rate) as min_heart_rate,
        max(t.heart_rate) as max_heart_rate,
        stddev(t.heart_rate) as stddev_heart_rate,
        
        avg(t.temperature) as avg_temperature,
        min(t.temperature) as min_temperature,
        max(t.temperature) as max_temperature,
        
        -- Activity metrics
        avg(t.activity_level) as avg_activity_level,
        sum(t.step_count) as total_steps,
        sum(t.lying_time) as total_lying_time,
        sum(t.eating_time) as total_eating_time,
        sum(t.rumination_time) as total_rumination_time,
        
        -- Data quality metrics
        avg(t.data_quality_score) as avg_data_quality,
        count(*) as total_readings,
        count(case when t.is_anomaly then 1 end) as anomaly_count,
        
        -- Device health
        avg(t.battery_level) as avg_battery_level,
        min(t.battery_level) as min_battery_level,
        avg(t.signal_strength) as avg_signal_strength
        
    from {{ ref('stg_sensor_telemetry') }} t
    join {{ ref('stg_entities') }} e on t.entity_id = e.entity_id
    where 
        e.entity_type = 'livestock'
        and t.date_bucket >= current_date - interval '90 days'
    group by 
        t.entity_id, e.farm_id, e.external_id, e.entity_name, 
        e.species, e.breed, e.age_months, t.date_bucket
),

health_scoring as (
    select
        *,
        
        -- Calculate health score based on multiple factors
        case
            -- Heart rate scoring (0-1 scale)
            when avg_heart_rate is null then 0.5
            when species = 'cattle' then
                case
                    when avg_heart_rate between 48 and 84 then 1.0
                    when avg_heart_rate between 40 and 96 then 0.7
                    else 0.3
                end
            when species = 'sheep' then
                case
                    when avg_heart_rate between 70 and 120 then 1.0
                    when avg_heart_rate between 60 and 140 then 0.7
                    else 0.3
                end
            else 0.5
        end as heart_rate_score,
        
        -- Temperature scoring
        case
            when avg_temperature is null then 0.5
            when species = 'cattle' then
                case
                    when avg_temperature between 37.5 and 39.5 then 1.0
                    when avg_temperature between 36.5 and 40.5 then 0.7
                    else 0.3
                end
            when species = 'sheep' then
                case
                    when avg_temperature between 38.5 and 40.0 then 1.0
                    when avg_temperature between 37.5 and 41.0 then 0.7
                    else 0.3
                end
            else 0.5
        end as temperature_score,
        
        -- Activity scoring
        case
            when avg_activity_level is null then 0.5
            when avg_activity_level between 0.3 and 0.9 then 1.0
            when avg_activity_level between 0.1 and 1.0 then 0.7
            else 0.3
        end as activity_score,
        
        -- Rumination scoring (for ruminants)
        case
            when species not in ('cattle', 'sheep', 'goat') then 1.0  -- N/A for non-ruminants
            when total_rumination_time is null then 0.5
            when species = 'cattle' then
                case
                    when total_rumination_time between 300 and 600 then 1.0
                    when total_rumination_time between 180 and 720 then 0.7
                    else 0.3
                end
            when species in ('sheep', 'goat') then
                case
                    when total_rumination_time between 240 and 480 then 1.0
                    when total_rumination_time between 120 and 600 then 0.7
                    else 0.3
                end
            else 0.5
        end as rumination_score,
        
        -- Data quality impact
        case
            when avg_data_quality >= 0.9 then 1.0
            when avg_data_quality >= 0.7 then 0.9
            when avg_data_quality >= 0.5 then 0.7
            else 0.5
        end as data_quality_factor,
        
        -- Anomaly impact
        case
            when total_readings = 0 then 0.5
            when (anomaly_count::float / total_readings) <= 0.05 then 1.0
            when (anomaly_count::float / total_readings) <= 0.15 then 0.8
            when (anomaly_count::float / total_readings) <= 0.30 then 0.6
            else 0.4
        end as anomaly_factor
        
    from daily_telemetry
),

final_health_scores as (
    select
        *,
        
        -- Calculate composite health score
        (
            heart_rate_score * 0.25 +
            temperature_score * 0.25 +
            activity_score * 0.20 +
            rumination_score * 0.20 +
            (1.0 * 0.10)  -- Base score component
        ) * data_quality_factor * anomaly_factor as health_score,
        
        -- Determine health status
        case
            when (
                heart_rate_score * 0.25 +
                temperature_score * 0.25 +
                activity_score * 0.20 +
                rumination_score * 0.20 +
                0.10
            ) * data_quality_factor * anomaly_factor >= 0.9 then 'healthy'
            when (
                heart_rate_score * 0.25 +
                temperature_score * 0.25 +
                activity_score * 0.20 +
                rumination_score * 0.20 +
                0.10
            ) * data_quality_factor * anomaly_factor >= 0.7 then 'monitoring'
            when (
                heart_rate_score * 0.25 +
                temperature_score * 0.25 +
                activity_score * 0.20 +
                rumination_score * 0.20 +
                0.10
            ) * data_quality_factor * anomaly_factor >= 0.5 then 'concern'
            else 'alert'
        end as health_status,
        
        current_timestamp as calculated_at
        
    from health_scoring
)

select
    entity_id,
    farm_id,
    external_id,
    entity_name,
    species,
    breed,
    age_months,
    date,
    
    -- Vital signs
    avg_heart_rate,
    min_heart_rate,
    max_heart_rate,
    stddev_heart_rate,
    avg_temperature,
    min_temperature,
    max_temperature,
    
    -- Activity metrics
    avg_activity_level,
    total_steps,
    total_lying_time,
    total_eating_time,
    total_rumination_time,
    
    -- Health scoring
    health_score,
    health_status,
    heart_rate_score,
    temperature_score,
    activity_score,
    rumination_score,
    
    -- Data quality
    avg_data_quality,
    total_readings,
    anomaly_count,
    round((anomaly_count::float / nullif(total_readings, 0)) * 100, 2) as anomaly_percentage,
    
    -- Device metrics
    avg_battery_level,
    min_battery_level,
    avg_signal_strength,
    
    calculated_at
    
from final_health_scores
order by entity_id, date desc
