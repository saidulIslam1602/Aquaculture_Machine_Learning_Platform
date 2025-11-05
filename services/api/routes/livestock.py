"""
Livestock Monitoring API Routes

This module provides REST API endpoints for livestock monitoring including
animal tracking, virtual fencing, health monitoring, and telemetry data management.

Industry Standards:
    - RESTful API design with proper HTTP methods
    - Comprehensive input validation with Pydantic
    - Proper error handling and status codes
    - OpenAPI documentation with examples
    - Performance optimization with database queries
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.config import settings
from ..models.agricultural_telemetry import (
    Entity, Sensor, SensorTelemetry, VirtualFence, FenceViolation, HealthAlert
)
from ..schemas.livestock import (
    LivestockCreate, LivestockResponse, LivestockUpdate,
    AnimalCollarCreate, AnimalCollarResponse,
    TelemetryDataCreate, TelemetryDataResponse,
    VirtualFenceCreate, VirtualFenceResponse, VirtualFenceUpdate,
    FenceViolationResponse, HealthAlertResponse,
    LivestockLocationUpdate, LivestockHealthMetrics
)
from ..utils.geospatial import (
    calculate_distance, point_in_polygon, get_nearest_fence
)
from ..utils.health_analysis import analyze_animal_health
from ..utils.metrics import track_api_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/livestock", tags=["livestock"])


@router.post("/animals", response_model=LivestockResponse, status_code=201)
@track_api_metrics
async def create_animal(
    animal_data: LivestockCreate,
    db: Session = Depends(get_db)
) -> LivestockResponse:
    """
    Create a new livestock animal record.
    
    Creates a new animal entity in the system with metadata including
    species, breed, age, weight, and initial location.
    
    Args:
        animal_data: Animal creation data including metadata
        db: Database session
        
    Returns:
        LivestockResponse: Created animal information
        
    Raises:
        HTTPException: If animal with external_id already exists
    """
    try:
        # Check if animal with external_id already exists
        existing_animal = db.query(Entity).filter(
            and_(
                Entity.external_id == animal_data.external_id,
                Entity.entity_type == "livestock",
                Entity.farm_id == animal_data.farm_id
            )
        ).first()
        
        if existing_animal:
            raise HTTPException(
                status_code=400,
                detail=f"Animal with external_id '{animal_data.external_id}' already exists"
            )
        
        # Create new animal entity
        animal = Entity(
            external_id=animal_data.external_id,
            entity_type="livestock",
            entity_subtype=animal_data.species,
            name=animal_data.name,
            description=animal_data.description,
            metadata={
                "species": animal_data.species,
                "breed": animal_data.breed,
                "age_months": animal_data.age_months,
                "weight_kg": animal_data.weight_kg,
                "gender": animal_data.gender,
                "birth_date": animal_data.birth_date.isoformat() if animal_data.birth_date else None,
                "health_status": animal_data.health_status,
                "vaccination_records": animal_data.vaccination_records or [],
                "breeding_info": animal_data.breeding_info or {}
            },
            location=f"POINT({animal_data.longitude} {animal_data.latitude})" if animal_data.longitude and animal_data.latitude else None,
            farm_id=animal_data.farm_id,
            is_active=True
        )
        
        db.add(animal)
        db.commit()
        db.refresh(animal)
        
        logger.info(f"Created new animal: {animal.external_id} for farm {animal.farm_id}")
        
        return LivestockResponse(
            id=animal.id,
            external_id=animal.external_id,
            name=animal.name,
            species=animal.metadata.get("species"),
            breed=animal.metadata.get("breed"),
            age_months=animal.metadata.get("age_months"),
            weight_kg=animal.metadata.get("weight_kg"),
            gender=animal.metadata.get("gender"),
            health_status=animal.metadata.get("health_status"),
            farm_id=animal.farm_id,
            latitude=None,  # Will be populated from location if available
            longitude=None,
            is_active=animal.is_active,
            created_at=animal.created_at,
            updated_at=animal.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create animal: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create animal")


@router.get("/animals", response_model=List[LivestockResponse])
@track_api_metrics
async def get_animals(
    farm_id: str = Query(..., description="Farm identifier"),
    species: Optional[str] = Query(None, description="Filter by species"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
) -> List[LivestockResponse]:
    """
    Get livestock animals with optional filtering.
    
    Retrieves a list of livestock animals for a specific farm with
    optional filtering by species, health status, and active status.
    
    Args:
        farm_id: Farm identifier
        species: Optional species filter
        health_status: Optional health status filter
        is_active: Filter by active status
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List[LivestockResponse]: List of animals matching criteria
    """
    try:
        query = db.query(Entity).filter(
            and_(
                Entity.entity_type == "livestock",
                Entity.farm_id == farm_id,
                Entity.is_active == is_active
            )
        )
        
        if species:
            query = query.filter(Entity.entity_subtype == species)
            
        if health_status:
            query = query.filter(Entity.metadata["health_status"].astext == health_status)
        
        animals = query.offset(offset).limit(limit).all()
        
        return [
            LivestockResponse(
                id=animal.id,
                external_id=animal.external_id,
                name=animal.name,
                species=animal.metadata.get("species"),
                breed=animal.metadata.get("breed"),
                age_months=animal.metadata.get("age_months"),
                weight_kg=animal.metadata.get("weight_kg"),
                gender=animal.metadata.get("gender"),
                health_status=animal.metadata.get("health_status"),
                farm_id=animal.farm_id,
                is_active=animal.is_active,
                created_at=animal.created_at,
                updated_at=animal.updated_at
            )
            for animal in animals
        ]
        
    except Exception as e:
        logger.error(f"Failed to get animals: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve animals")


@router.get("/animals/{animal_id}", response_model=LivestockResponse)
@track_api_metrics
async def get_animal(
    animal_id: UUID = Path(..., description="Animal UUID"),
    db: Session = Depends(get_db)
) -> LivestockResponse:
    """
    Get specific animal by ID.
    
    Args:
        animal_id: Animal UUID
        db: Database session
        
    Returns:
        LivestockResponse: Animal information
        
    Raises:
        HTTPException: If animal not found
    """
    try:
        animal = db.query(Entity).filter(
            and_(
                Entity.id == animal_id,
                Entity.entity_type == "livestock"
            )
        ).first()
        
        if not animal:
            raise HTTPException(status_code=404, detail="Animal not found")
        
        return LivestockResponse(
            id=animal.id,
            external_id=animal.external_id,
            name=animal.name,
            species=animal.metadata.get("species"),
            breed=animal.metadata.get("breed"),
            age_months=animal.metadata.get("age_months"),
            weight_kg=animal.metadata.get("weight_kg"),
            gender=animal.metadata.get("gender"),
            health_status=animal.metadata.get("health_status"),
            farm_id=animal.farm_id,
            is_active=animal.is_active,
            created_at=animal.created_at,
            updated_at=animal.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get animal {animal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve animal")


@router.put("/animals/{animal_id}", response_model=LivestockResponse)
@track_api_metrics
async def update_animal(
    animal_id: UUID = Path(..., description="Animal UUID"),
    animal_data: LivestockUpdate = ...,
    db: Session = Depends(get_db)
) -> LivestockResponse:
    """
    Update animal information.
    
    Args:
        animal_id: Animal UUID
        animal_data: Updated animal data
        db: Database session
        
    Returns:
        LivestockResponse: Updated animal information
        
    Raises:
        HTTPException: If animal not found
    """
    try:
        animal = db.query(Entity).filter(
            and_(
                Entity.id == animal_id,
                Entity.entity_type == "livestock"
            )
        ).first()
        
        if not animal:
            raise HTTPException(status_code=404, detail="Animal not found")
        
        # Update fields if provided
        if animal_data.name is not None:
            animal.name = animal_data.name
        if animal_data.description is not None:
            animal.description = animal_data.description
        if animal_data.weight_kg is not None:
            animal.metadata["weight_kg"] = animal_data.weight_kg
        if animal_data.health_status is not None:
            animal.metadata["health_status"] = animal_data.health_status
        if animal_data.is_active is not None:
            animal.is_active = animal_data.is_active
        
        animal.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(animal)
        
        logger.info(f"Updated animal: {animal.external_id}")
        
        return LivestockResponse(
            id=animal.id,
            external_id=animal.external_id,
            name=animal.name,
            species=animal.metadata.get("species"),
            breed=animal.metadata.get("breed"),
            age_months=animal.metadata.get("age_months"),
            weight_kg=animal.metadata.get("weight_kg"),
            gender=animal.metadata.get("gender"),
            health_status=animal.metadata.get("health_status"),
            farm_id=animal.farm_id,
            is_active=animal.is_active,
            created_at=animal.created_at,
            updated_at=animal.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update animal {animal_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update animal")


@router.post("/animals/{animal_id}/collar", response_model=AnimalCollarResponse, status_code=201)
@track_api_metrics
async def attach_collar(
    animal_id: UUID = Path(..., description="Animal UUID"),
    collar_data: AnimalCollarCreate = ...,
    db: Session = Depends(get_db)
) -> AnimalCollarResponse:
    """
    Attach a collar sensor to an animal.
    
    Args:
        animal_id: Animal UUID
        collar_data: Collar sensor information
        db: Database session
        
    Returns:
        AnimalCollarResponse: Created collar sensor information
        
    Raises:
        HTTPException: If animal not found or collar already exists
    """
    try:
        # Verify animal exists
        animal = db.query(Entity).filter(
            and_(
                Entity.id == animal_id,
                Entity.entity_type == "livestock"
            )
        ).first()
        
        if not animal:
            raise HTTPException(status_code=404, detail="Animal not found")
        
        # Check if collar device_id already exists
        existing_collar = db.query(Sensor).filter(
            Sensor.device_id == collar_data.device_id
        ).first()
        
        if existing_collar:
            raise HTTPException(
                status_code=400,
                detail=f"Collar with device_id '{collar_data.device_id}' already exists"
            )
        
        # Create collar sensor
        collar = Sensor(
            device_id=collar_data.device_id,
            sensor_type_id=collar_data.sensor_type_id,
            entity_id=animal_id,
            firmware_version=collar_data.firmware_version,
            battery_level=collar_data.battery_level,
            configuration={
                "gps_enabled": collar_data.gps_enabled,
                "heart_rate_enabled": collar_data.heart_rate_enabled,
                "accelerometer_enabled": collar_data.accelerometer_enabled,
                "sampling_interval_seconds": collar_data.sampling_interval_seconds,
                "transmission_interval_seconds": collar_data.transmission_interval_seconds
            },
            is_active=True
        )
        
        db.add(collar)
        db.commit()
        db.refresh(collar)
        
        logger.info(f"Attached collar {collar.device_id} to animal {animal.external_id}")
        
        return AnimalCollarResponse(
            id=collar.id,
            device_id=collar.device_id,
            animal_id=animal_id,
            firmware_version=collar.firmware_version,
            battery_level=collar.battery_level,
            gps_enabled=collar.configuration.get("gps_enabled", True),
            heart_rate_enabled=collar.configuration.get("heart_rate_enabled", True),
            accelerometer_enabled=collar.configuration.get("accelerometer_enabled", True),
            sampling_interval_seconds=collar.configuration.get("sampling_interval_seconds", 60),
            transmission_interval_seconds=collar.configuration.get("transmission_interval_seconds", 300),
            is_active=collar.is_active,
            installed_at=collar.installed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to attach collar to animal {animal_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to attach collar")


@router.post("/telemetry", status_code=201)
@track_api_metrics
async def ingest_telemetry(
    telemetry_data: List[TelemetryDataCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ingest telemetry data from animal collars.
    
    Processes incoming telemetry data including GPS coordinates,
    health metrics, and sensor readings. Performs real-time analysis
    for virtual fencing and health monitoring.
    
    Args:
        telemetry_data: List of telemetry readings
        background_tasks: Background task queue
        db: Database session
        
    Returns:
        Dict with ingestion results
    """
    try:
        ingested_count = 0
        alerts_generated = 0
        
        for data in telemetry_data:
            # Verify sensor exists
            sensor = db.query(Sensor).filter(
                Sensor.device_id == data.device_id
            ).first()
            
            if not sensor:
                logger.warning(f"Unknown sensor device_id: {data.device_id}")
                continue
            
            # Create telemetry record
            telemetry = SensorTelemetry(
                timestamp=data.timestamp,
                sensor_id=sensor.id,
                entity_id=sensor.entity_id,
                metrics=data.metrics,
                location=f"POINT({data.longitude} {data.latitude})" if data.longitude and data.latitude else None,
                temperature=data.metrics.get("temperature"),
                battery_level=data.metrics.get("battery_level"),
                signal_strength=data.metrics.get("signal_strength"),
                data_quality_score=data.data_quality_score or 1.0
            )
            
            db.add(telemetry)
            ingested_count += 1
            
            # Schedule background processing for virtual fencing and health analysis
            if data.longitude and data.latitude:
                background_tasks.add_task(
                    process_location_update,
                    sensor.entity_id,
                    data.longitude,
                    data.latitude,
                    data.timestamp
                )
            
            background_tasks.add_task(
                process_health_metrics,
                sensor.entity_id,
                data.metrics,
                data.timestamp
            )
        
        db.commit()
        
        logger.info(f"Ingested {ingested_count} telemetry records")
        
        return {
            "status": "success",
            "ingested_count": ingested_count,
            "alerts_generated": alerts_generated,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest telemetry data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to ingest telemetry data")


@router.get("/animals/{animal_id}/telemetry", response_model=List[TelemetryDataResponse])
@track_api_metrics
async def get_animal_telemetry(
    animal_id: UUID = Path(..., description="Animal UUID"),
    start_time: Optional[datetime] = Query(None, description="Start time for data range"),
    end_time: Optional[datetime] = Query(None, description="End time for data range"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> List[TelemetryDataResponse]:
    """
    Get telemetry data for a specific animal.
    
    Args:
        animal_id: Animal UUID
        start_time: Optional start time filter
        end_time: Optional end time filter
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List[TelemetryDataResponse]: Telemetry data records
    """
    try:
        query = db.query(SensorTelemetry).filter(
            SensorTelemetry.entity_id == animal_id
        )
        
        if start_time:
            query = query.filter(SensorTelemetry.timestamp >= start_time)
        if end_time:
            query = query.filter(SensorTelemetry.timestamp <= end_time)
        
        telemetry_records = query.order_by(desc(SensorTelemetry.timestamp)).limit(limit).all()
        
        return [
            TelemetryDataResponse(
                timestamp=record.timestamp,
                sensor_id=record.sensor_id,
                entity_id=record.entity_id,
                metrics=record.metrics,
                latitude=None,  # Extract from location if needed
                longitude=None,
                data_quality_score=record.data_quality_score,
                is_anomaly=record.is_anomaly
            )
            for record in telemetry_records
        ]
        
    except Exception as e:
        logger.error(f"Failed to get telemetry for animal {animal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve telemetry data")


async def process_location_update(
    entity_id: UUID,
    longitude: float,
    latitude: float,
    timestamp: datetime
) -> None:
    """
    Background task to process location updates for virtual fencing.
    
    Args:
        entity_id: Animal entity ID
        longitude: GPS longitude
        latitude: GPS latitude
        timestamp: Timestamp of location update
    """
    # This would implement virtual fencing logic
    # For now, this is a placeholder for the background processing
    logger.info(f"Processing location update for entity {entity_id} at {longitude}, {latitude}")


async def process_health_metrics(
    entity_id: UUID,
    metrics: Dict[str, Any],
    timestamp: datetime
) -> None:
    """
    Background task to analyze health metrics and generate alerts.
    
    Args:
        entity_id: Animal entity ID
        metrics: Sensor metrics data
        timestamp: Timestamp of metrics
    """
    # This would implement health analysis logic
    # For now, this is a placeholder for the background processing
    logger.info(f"Processing health metrics for entity {entity_id}: {metrics}")


@router.get("/health-alerts", response_model=List[HealthAlertResponse])
@track_api_metrics
async def get_health_alerts(
    farm_id: str = Query(..., description="Farm identifier"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> List[HealthAlertResponse]:
    """
    Get health alerts for farm animals.
    
    Args:
        farm_id: Farm identifier
        severity: Optional severity filter
        status: Optional status filter
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List[HealthAlertResponse]: Health alerts
    """
    try:
        query = db.query(HealthAlert).join(Entity).filter(
            Entity.farm_id == farm_id
        )
        
        if severity:
            query = query.filter(HealthAlert.severity == severity)
        if status:
            query = query.filter(HealthAlert.status == status)
        
        alerts = query.order_by(desc(HealthAlert.alert_timestamp)).limit(limit).all()
        
        return [
            HealthAlertResponse(
                id=alert.id,
                entity_id=alert.entity_id,
                alert_timestamp=alert.alert_timestamp,
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                description=alert.description,
                confidence_score=alert.confidence_score,
                status=alert.status,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get health alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health alerts")
