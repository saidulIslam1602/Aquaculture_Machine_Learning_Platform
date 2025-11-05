{{
  config(
    materialized='view'
  )
}}

with source_data as (
    select
        id as entity_id,
        external_id,
        entity_type,
        entity_subtype,
        name as entity_name,
        description,
        metadata,
        location,
        farm_id,
        is_active,
        created_at,
        updated_at
    from {{ source('agricultural_iot', 'entities') }}
    where is_active = true
),

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
        
        -- Extract location coordinates
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
        
        -- Extract metadata fields for livestock
        case 
            when entity_type = 'livestock' then (metadata->>'species')::text
            else null
        end as species,
        
        case 
            when entity_type = 'livestock' then (metadata->>'breed')::text
            else null
        end as breed,
        
        case 
            when entity_type = 'livestock' then (metadata->>'gender')::text
            else null
        end as gender,
        
        case 
            when entity_type = 'livestock' then (metadata->>'age_months')::numeric
            else null
        end as age_months,
        
        case 
            when entity_type = 'livestock' then (metadata->>'weight_kg')::numeric
            else null
        end as weight_kg,
        
        case 
            when entity_type = 'livestock' then (metadata->>'health_status')::text
            else null
        end as health_status,
        
        case 
            when entity_type = 'livestock' and (metadata->>'birth_date') is not null 
            then (metadata->>'birth_date')::date
            else null
        end as birth_date,
        
        -- Calculate age in days if birth_date is available
        case 
            when entity_type = 'livestock' and (metadata->>'birth_date') is not null 
            then current_date - (metadata->>'birth_date')::date
            else null
        end as age_days,
        
        -- Extract aquaculture-specific metadata
        case 
            when entity_type = 'aquaculture' then (metadata->>'tank_id')::text
            else null
        end as tank_id,
        
        case 
            when entity_type = 'aquaculture' then (metadata->>'water_type')::text
            else null
        end as water_type,
        
        case 
            when entity_type = 'aquaculture' then (metadata->>'stocking_density')::numeric
            else null
        end as stocking_density,
        
        -- Full metadata for flexibility
        metadata as raw_metadata
        
    from source_data
)

select * from enriched_entities
