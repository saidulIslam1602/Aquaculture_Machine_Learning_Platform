"""
Livestock Monitoring Pydantic Schemas

This module defines Pydantic models for request/response validation
in the livestock monitoring API endpoints.

Industry Standards:
    - Comprehensive input validation with type hints
    - Clear field descriptions for API documentation
    - Proper use of Optional types for nullable fields
    - Example values for OpenAPI documentation
    - Consistent naming conventions
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class AnimalSpecies(str, Enum):
    """Supported animal species"""
    CATTLE = "cattle"
    SHEEP = "sheep"
    GOAT = "goat"
    PIG = "pig"
    HORSE = "horse"
    CHICKEN = "chicken"
    OTHER = "other"


class HealthStatus(str, Enum):
    """Animal health status options"""
    HEALTHY = "healthy"
    MONITORING = "monitoring"
    SICK = "sick"
    QUARANTINE = "quarantine"
    TREATMENT = "treatment"
    RECOVERED = "recovered"


class Gender(str, Enum):
    """Animal gender options"""
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status options"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# Livestock Animal Schemas

class LivestockBase(BaseModel):
    """Base livestock animal schema"""
    external_id: str = Field(..., description="Customer-provided animal identifier", min_length=1, max_length=100)
    name: Optional[str] = Field(None, description="Animal name", max_length=200)
    description: Optional[str] = Field(None, description="Animal description")
    species: AnimalSpecies = Field(..., description="Animal species")
    breed: Optional[str] = Field(None, description="Animal breed", max_length=100)
    gender: Optional[Gender] = Field(None, description="Animal gender")
    farm_id: str = Field(..., description="Farm identifier", min_length=1, max_length=100)


class LivestockCreate(LivestockBase):
    """Schema for creating a new livestock animal"""
    age_months: Optional[int] = Field(None, description="Animal age in months", ge=0, le=300)
    weight_kg: Optional[float] = Field(None, description="Animal weight in kilograms", ge=0, le=2000)
    birth_date: Optional[datetime] = Field(None, description="Animal birth date")
    health_status: HealthStatus = Field(HealthStatus.HEALTHY, description="Current health status")
    latitude: Optional[float] = Field(None, description="Initial GPS latitude", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Initial GPS longitude", ge=-180, le=180)
    vaccination_records: Optional[List[Dict[str, Any]]] = Field(None, description="Vaccination history")
    breeding_info: Optional[Dict[str, Any]] = Field(None, description="Breeding information")

    class Config:
        schema_extra = {
            "example": {
                "external_id": "COW-001",
                "name": "Bessie",
                "species": "cattle",
                "breed": "Holstein",
                "gender": "female",
                "age_months": 24,
                "weight_kg": 450.5,
                "health_status": "healthy",
                "farm_id": "FARM-123",
                "latitude": 59.9139,
                "longitude": 10.7522,
                "vaccination_records": [
                    {
                        "vaccine": "FMD",
                        "date": "2024-01-15",
                        "veterinarian": "Dr. Smith"
                    }
                ]
            }
        }


class LivestockUpdate(BaseModel):
    """Schema for updating livestock animal information"""
    name: Optional[str] = Field(None, description="Animal name", max_length=200)
    description: Optional[str] = Field(None, description="Animal description")
    weight_kg: Optional[float] = Field(None, description="Updated weight in kilograms", ge=0, le=2000)
    health_status: Optional[HealthStatus] = Field(None, description="Updated health status")
    is_active: Optional[bool] = Field(None, description="Whether animal is active")

    class Config:
        schema_extra = {
            "example": {
                "weight_kg": 465.2,
                "health_status": "monitoring"
            }
        }


class LivestockResponse(LivestockBase):
    """Schema for livestock animal response"""
    id: UUID = Field(..., description="Animal UUID")
    age_months: Optional[int] = Field(None, description="Animal age in months")
    weight_kg: Optional[float] = Field(None, description="Animal weight in kilograms")
    health_status: Optional[str] = Field(None, description="Current health status")
    latitude: Optional[float] = Field(None, description="Current GPS latitude")
    longitude: Optional[float] = Field(None, description="Current GPS longitude")
    is_active: bool = Field(..., description="Whether animal is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "external_id": "COW-001",
                "name": "Bessie",
                "species": "cattle",
                "breed": "Holstein",
                "gender": "female",
                "age_months": 24,
                "weight_kg": 450.5,
                "health_status": "healthy",
                "farm_id": "FARM-123",
                "is_active": True,
                "created_at": "2024-01-01T10:00:00Z"
            }
        }


# Animal Collar Schemas

class AnimalCollarCreate(BaseModel):
    """Schema for creating an animal collar sensor"""
    device_id: str = Field(..., description="Unique collar device identifier", min_length=1, max_length=100)
    sensor_type_id: UUID = Field(..., description="Sensor type UUID")
    firmware_version: Optional[str] = Field(None, description="Collar firmware version", max_length=50)
    battery_level: Optional[float] = Field(None, description="Initial battery level percentage", ge=0, le=100)
    gps_enabled: bool = Field(True, description="Whether GPS tracking is enabled")
    heart_rate_enabled: bool = Field(True, description="Whether heart rate monitoring is enabled")
    accelerometer_enabled: bool = Field(True, description="Whether accelerometer is enabled")
    sampling_interval_seconds: int = Field(60, description="Sensor sampling interval in seconds", ge=1, le=3600)
    transmission_interval_seconds: int = Field(300, description="Data transmission interval in seconds", ge=60, le=86400)

    class Config:
        schema_extra = {
            "example": {
                "device_id": "COLLAR-ABC123",
                "sensor_type_id": "123e4567-e89b-12d3-a456-426614174000",
                "firmware_version": "v2.1.0",
                "battery_level": 95.0,
                "gps_enabled": True,
                "heart_rate_enabled": True,
                "accelerometer_enabled": True,
                "sampling_interval_seconds": 60,
                "transmission_interval_seconds": 300
            }
        }


class AnimalCollarResponse(BaseModel):
    """Schema for animal collar response"""
    id: UUID = Field(..., description="Collar sensor UUID")
    device_id: str = Field(..., description="Collar device identifier")
    animal_id: UUID = Field(..., description="Associated animal UUID")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    battery_level: Optional[float] = Field(None, description="Current battery level percentage")
    gps_enabled: bool = Field(..., description="GPS tracking status")
    heart_rate_enabled: bool = Field(..., description="Heart rate monitoring status")
    accelerometer_enabled: bool = Field(..., description="Accelerometer status")
    sampling_interval_seconds: int = Field(..., description="Sampling interval in seconds")
    transmission_interval_seconds: int = Field(..., description="Transmission interval in seconds")
    is_active: bool = Field(..., description="Whether collar is active")
    installed_at: datetime = Field(..., description="Installation timestamp")

    class Config:
        orm_mode = True


# Telemetry Data Schemas

class TelemetryDataCreate(BaseModel):
    """Schema for creating telemetry data"""
    device_id: str = Field(..., description="Sensor device identifier")
    timestamp: datetime = Field(..., description="Measurement timestamp")
    metrics: Dict[str, Any] = Field(..., description="Sensor metrics data")
    latitude: Optional[float] = Field(None, description="GPS latitude", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="GPS longitude", ge=-180, le=180)
    data_quality_score: Optional[float] = Field(1.0, description="Data quality score", ge=0, le=1)

    @validator('metrics')
    def validate_metrics(cls, v):
        """Validate that metrics contains required fields"""
        if not isinstance(v, dict):
            raise ValueError('Metrics must be a dictionary')
        return v

    class Config:
        schema_extra = {
            "example": {
                "device_id": "COLLAR-ABC123",
                "timestamp": "2024-01-01T12:00:00Z",
                "metrics": {
                    "heart_rate": 72,
                    "temperature": 38.5,
                    "activity_level": 0.7,
                    "battery_level": 94.0,
                    "signal_strength": -65
                },
                "latitude": 59.9139,
                "longitude": 10.7522,
                "data_quality_score": 0.95
            }
        }


class TelemetryDataResponse(BaseModel):
    """Schema for telemetry data response"""
    timestamp: datetime = Field(..., description="Measurement timestamp")
    sensor_id: UUID = Field(..., description="Sensor UUID")
    entity_id: UUID = Field(..., description="Entity UUID")
    metrics: Dict[str, Any] = Field(..., description="Sensor metrics data")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    data_quality_score: float = Field(..., description="Data quality score")
    is_anomaly: bool = Field(..., description="Whether data is flagged as anomaly")

    class Config:
        orm_mode = True


# Location and Health Schemas

class LivestockLocationUpdate(BaseModel):
    """Schema for updating animal location"""
    latitude: float = Field(..., description="GPS latitude", ge=-90, le=90)
    longitude: float = Field(..., description="GPS longitude", ge=-180, le=180)
    timestamp: datetime = Field(..., description="Location timestamp")
    accuracy_meters: Optional[float] = Field(None, description="GPS accuracy in meters", ge=0)

    class Config:
        schema_extra = {
            "example": {
                "latitude": 59.9139,
                "longitude": 10.7522,
                "timestamp": "2024-01-01T12:00:00Z",
                "accuracy_meters": 5.0
            }
        }


class LivestockHealthMetrics(BaseModel):
    """Schema for animal health metrics"""
    heart_rate: Optional[int] = Field(None, description="Heart rate in BPM", ge=0, le=300)
    body_temperature: Optional[float] = Field(None, description="Body temperature in Celsius", ge=30, le=45)
    activity_level: Optional[float] = Field(None, description="Activity level score", ge=0, le=1)
    rumination_time: Optional[int] = Field(None, description="Rumination time in minutes", ge=0)
    step_count: Optional[int] = Field(None, description="Daily step count", ge=0)
    lying_time: Optional[int] = Field(None, description="Lying time in minutes", ge=0)
    eating_time: Optional[int] = Field(None, description="Eating time in minutes", ge=0)

    class Config:
        schema_extra = {
            "example": {
                "heart_rate": 72,
                "body_temperature": 38.5,
                "activity_level": 0.7,
                "rumination_time": 480,
                "step_count": 8500,
                "lying_time": 720,
                "eating_time": 300
            }
        }


# Virtual Fence Schemas

class VirtualFenceCreate(BaseModel):
    """Schema for creating a virtual fence"""
    name: str = Field(..., description="Fence name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Fence description")
    farm_id: str = Field(..., description="Farm identifier")
    boundary_coordinates: List[List[float]] = Field(..., description="Polygon boundary coordinates [[lng, lat], ...]")
    buffer_zone_meters: float = Field(10.0, description="Buffer zone in meters", ge=0, le=1000)
    fence_type: str = Field("containment", description="Fence type: containment or exclusion")
    alert_on_entry: bool = Field(True, description="Alert when animal enters")
    alert_on_exit: bool = Field(True, description="Alert when animal exits")
    notification_delay_seconds: int = Field(30, description="Notification delay in seconds", ge=0, le=3600)

    @validator('boundary_coordinates')
    def validate_boundary(cls, v):
        """Validate boundary coordinates"""
        if len(v) < 3:
            raise ValueError('Boundary must have at least 3 coordinates')
        for coord in v:
            if len(coord) != 2:
                raise ValueError('Each coordinate must be [longitude, latitude]')
            if not (-180 <= coord[0] <= 180):
                raise ValueError('Longitude must be between -180 and 180')
            if not (-90 <= coord[1] <= 90):
                raise ValueError('Latitude must be between -90 and 90')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "North Pasture",
                "description": "Main grazing area for cattle",
                "farm_id": "FARM-123",
                "boundary_coordinates": [
                    [10.7522, 59.9139],
                    [10.7530, 59.9145],
                    [10.7540, 59.9135],
                    [10.7522, 59.9139]
                ],
                "buffer_zone_meters": 15.0,
                "fence_type": "containment",
                "alert_on_exit": True,
                "notification_delay_seconds": 60
            }
        }


class VirtualFenceUpdate(BaseModel):
    """Schema for updating a virtual fence"""
    name: Optional[str] = Field(None, description="Fence name", max_length=200)
    description: Optional[str] = Field(None, description="Fence description")
    buffer_zone_meters: Optional[float] = Field(None, description="Buffer zone in meters", ge=0, le=1000)
    is_active: Optional[bool] = Field(None, description="Whether fence is active")
    alert_on_entry: Optional[bool] = Field(None, description="Alert when animal enters")
    alert_on_exit: Optional[bool] = Field(None, description="Alert when animal exits")
    notification_delay_seconds: Optional[int] = Field(None, description="Notification delay in seconds", ge=0, le=3600)


class VirtualFenceResponse(BaseModel):
    """Schema for virtual fence response"""
    id: UUID = Field(..., description="Fence UUID")
    name: str = Field(..., description="Fence name")
    description: Optional[str] = Field(None, description="Fence description")
    farm_id: str = Field(..., description="Farm identifier")
    fence_type: str = Field(..., description="Fence type")
    buffer_zone_meters: float = Field(..., description="Buffer zone in meters")
    is_active: bool = Field(..., description="Whether fence is active")
    alert_on_entry: bool = Field(..., description="Alert on entry setting")
    alert_on_exit: bool = Field(..., description="Alert on exit setting")
    notification_delay_seconds: int = Field(..., description="Notification delay in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        orm_mode = True


# Fence Violation Schemas

class FenceViolationResponse(BaseModel):
    """Schema for fence violation response"""
    id: UUID = Field(..., description="Violation UUID")
    entity_id: UUID = Field(..., description="Animal UUID")
    fence_id: UUID = Field(..., description="Fence UUID")
    violation_timestamp: datetime = Field(..., description="Violation timestamp")
    violation_type: str = Field(..., description="Violation type: entry or exit")
    latitude: float = Field(..., description="Violation location latitude")
    longitude: float = Field(..., description="Violation location longitude")
    distance_from_boundary: Optional[float] = Field(None, description="Distance from boundary in meters")
    duration_seconds: Optional[int] = Field(None, description="Violation duration in seconds")
    severity: str = Field(..., description="Violation severity")
    alert_sent: bool = Field(..., description="Whether alert was sent")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    class Config:
        orm_mode = True


# Health Alert Schemas

class HealthAlertResponse(BaseModel):
    """Schema for health alert response"""
    id: UUID = Field(..., description="Alert UUID")
    entity_id: UUID = Field(..., description="Animal UUID")
    alert_timestamp: datetime = Field(..., description="Alert timestamp")
    alert_type: str = Field(..., description="Alert type")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    description: Optional[str] = Field(None, description="Alert description")
    confidence_score: Optional[float] = Field(None, description="ML confidence score")
    status: AlertStatus = Field(..., description="Alert status")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "entity_id": "456e7890-e89b-12d3-a456-426614174000",
                "alert_timestamp": "2024-01-01T14:30:00Z",
                "alert_type": "health_anomaly",
                "severity": "medium",
                "title": "Elevated Heart Rate Detected",
                "description": "Animal COW-001 showing elevated heart rate for extended period",
                "confidence_score": 0.85,
                "status": "open"
            }
        }
