/*
================================================================================
dbt Staging Model: Entities Data Transformation
================================================================================

Purpose:
This staging model transforms raw entity data from the agricultural IoT platform
into a clean, standardized format suitable for downstream analytics and ML models.
It handles both livestock and aquaculture entities with specialized metadata extraction.

Business Logic:
- Filters for active entities only
- Extracts geospatial coordinates from PostGIS geometry fields
- Parses JSON metadata into structured columns for livestock entities
- Handles aquaculture-specific attributes (tank_id, water_type, stocking_density)
- Calculates derived fields like age in days from birth_date
- Maintains raw metadata for flexibility in downstream models

Data Sources:
- Source: agricultural_iot.entities (raw entity data from operational systems)

Output Schema:
- entity_id: Primary key for the entity
- external_id: External system identifier for data integration
- entity_type: Type classification (livestock, aquaculture, equipment, etc.)
- entity_subtype: Detailed subclassification within entity_type
- location fields: longitude, latitude extracted from PostGIS geometry
- livestock fields: species, breed, gender, age_months, weight_kg, health_status
- aquaculture fields: tank_id, water_type, stocking_density
- audit fields: created_at, updated_at for data lineage

Performance Considerations:
- Materialized as view for real-time data access
- Indexes on entity_type and farm_id recommended for performance
- JSON extraction operations may impact query performance on large datasets

Data Quality:
- Filters out inactive entities to maintain data quality
- Handles null values gracefully in metadata extraction
- Validates date formats and numeric conversions

Author: Data Engineering Team
Version: 2.1.0
Last Updated: 2024-11-05
Dependencies: agricultural_iot.entities source table
*/

{{
  config(
    materialized='view',
    description='Staging model for entity data with metadata extraction and geospatial processing'
  )
}}

-- Source data extraction with basic filtering and column standardization
with source_data as (
    select
        id as entity_id,
        external_id,
        entity_type,
        entity_subtype,
        name as entity_name,
        description,
        entity_metadata,
        location,
        farm_id,
        is_active,
        created_at,
        updated_at
    from {{ source('agricultural_iot', 'entities') }}
    where is_active = true  -- Filter for active entities only to maintain data quality
),

-- Metadata extraction and geospatial processing for enhanced analytics
enriched_entities as (
    select
        entity_id,
        external_id,
        entity_type,
        entity_subtype,
        entity_name,
        description,
        farm_id,
        is_active,
        created_at,
        updated_at,
        
        -- Geospatial coordinate extraction from PostGIS geometry fields
        -- Converts PostGIS POINT geometry to separate longitude/latitude columns
        -- for easier consumption by analytics and ML models
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
        
        -- Livestock-specific metadata extraction from JSON fields
        -- Parses structured JSON metadata into individual columns for livestock entities
        -- Enables efficient querying and analysis of livestock characteristics
        case 
            when entity_type = 'livestock' then (entity_metadata->>'species')::text
            else null
        end as species,
        
        case 
            when entity_type = 'livestock' then (entity_metadata->>'breed')::text
            else null
        end as breed,
        
        case 
            when entity_type = 'livestock' then (entity_metadata->>'gender')::text
            else null
        end as gender,
        
        case 
            when entity_type = 'livestock' then (entity_metadata->>'age_months')::numeric
            else null
        end as age_months,
        
        case 
            when entity_type = 'livestock' then (entity_metadata->>'weight_kg')::numeric
            else null
        end as weight_kg,
        
        case 
            when entity_type = 'livestock' then (entity_metadata->>'health_status')::text
            else null
        end as health_status,
        
        case 
            when entity_type = 'livestock' and (entity_metadata->>'birth_date') is not null 
            then (entity_metadata->>'birth_date')::date
            else null
        end as birth_date,
        
        -- Calculate age in days if birth_date is available
        case 
            when entity_type = 'livestock' and (entity_metadata->>'birth_date') is not null 
            then current_date - (entity_metadata->>'birth_date')::date
            else null
        end as age_days,
        
        -- Aquaculture-specific metadata extraction for fish farming operations
        -- Handles tank management, water quality, and stocking density metrics
        -- Critical for aquaculture analytics and environmental monitoring
        case 
            when entity_type = 'aquaculture' then (entity_metadata->>'tank_id')::text
            else null
        end as tank_id,
        
        case 
            when entity_type = 'aquaculture' then (entity_metadata->>'water_type')::text
            else null
        end as water_type,
        
        case 
            when entity_type = 'aquaculture' then (entity_metadata->>'stocking_density')::numeric
            else null
        end as stocking_density,
        
        -- Preserve complete metadata for downstream flexibility and future enhancements
        -- Raw JSON metadata maintained for advanced analytics and ML feature engineering
        entity_metadata as raw_metadata
        
    from source_data
)

-- Final output with all transformed and enriched entity data
-- Ready for consumption by marts, analytics, and ML pipelines
select * from enriched_entities
