"""
Agricultural Telemetry Data Models

This module defines SQLAlchemy models for agricultural sensor telemetry data
supporting both aquaculture and livestock monitoring use cases with TimescaleDB
time-series optimization.

Industry Standards:
    - TimescaleDB hypertables for time-series data
    - Proper indexing for high-performance queries
    - JSONB for flexible sensor metrics
    - PostGIS for geospatial data
    - Proper foreign key relationships
"""

from sqlalchemy import (
    Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ..core.database import Base


class SensorType(Base):
    """
    Sensor Type Configuration
    
    Defines different types of sensors used across agricultural domains.
    Supports both aquaculture and livestock monitoring sensors.
    """
    __tablename__ = "sensor_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # 'aquaculture', 'livestock', 'environmental'
    description = Column(Text)
    metrics_schema = Column(JSONB)  # JSON schema for expected metrics
    unit_of_measurement = Column(String(20))
    sampling_frequency_seconds = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="sensor_type")
    
    def __repr__(self) -> str:
        return f"<SensorType(name='{self.name}', category='{self.category}')>"


class Entity(Base):
    """
    Agricultural Entity (Animal, Tank, Field, etc.)
    
    Represents any monitored entity in agricultural operations.
    Can be fish, livestock animals, tanks, fields, or equipment.
    """
    __tablename__ = "entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100), nullable=False)  # Customer-provided ID
    entity_type = Column(String(50), nullable=False)  # 'fish', 'cow', 'sheep', 'tank', 'field'
    entity_subtype = Column(String(50))  # Species, breed, equipment model
    name = Column(String(200))
    description = Column(Text)
    entity_metadata = Column(JSONB)  # Flexible metadata (age, weight, breed, etc.)
    location = Column(Geography('POINT', srid=4326))  # GPS coordinates
    farm_id = Column(String(100), nullable=False)  # Farm identifier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="entity")
    telemetry_data = relationship("SensorTelemetry", back_populates="entity")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_entities_type_farm', 'entity_type', 'farm_id'),
        Index('idx_entities_external_id', 'external_id'),
        Index('idx_entities_location', 'location', postgresql_using='gist'),
    )
    
    def __repr__(self) -> str:
        return f"<Entity(external_id='{self.external_id}', type='{self.entity_type}')>"


class Sensor(Base):
    """
    Physical Sensor Device
    
    Represents individual sensor devices attached to entities.
    Supports various sensor types from simple temperature sensors
    to complex animal collar devices.
    """
    __tablename__ = "sensors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), nullable=False, unique=True)
    sensor_type_id = Column(UUID(as_uuid=True), ForeignKey('sensor_types.id'), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('entities.id'), nullable=False)
    firmware_version = Column(String(50))
    battery_level = Column(Float)  # Battery percentage (0-100)
    signal_strength = Column(Float)  # Signal strength in dBm
    last_seen = Column(DateTime(timezone=True))
    configuration = Column(JSONB)  # Sensor-specific configuration
    is_active = Column(Boolean, default=True)
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sensor_type = relationship("SensorType", back_populates="sensors")
    entity = relationship("Entity", back_populates="sensors")
    telemetry_data = relationship("SensorTelemetry", back_populates="sensor")
    
    # Indexes
    __table_args__ = (
        Index('idx_sensors_device_id', 'device_id'),
        Index('idx_sensors_entity_type', 'entity_id', 'sensor_type_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Sensor(device_id='{self.device_id}', entity_id='{self.entity_id}')>"


class SensorTelemetry(Base):
    """
    Time-Series Sensor Telemetry Data
    
    Main table for storing all sensor telemetry data across agricultural domains.
    Optimized for TimescaleDB with proper partitioning and compression.
    """
    __tablename__ = "sensor_telemetry"
    
    # TimescaleDB requires time column to be first in composite primary key
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey('sensors.id'), primary_key=True, nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('entities.id'), nullable=False)
    
    # Sensor readings stored as flexible JSONB
    metrics = Column(JSONB, nullable=False)
    
    # Common fields extracted for performance
    location = Column(Geography('POINT', srid=4326))  # GPS coordinates if available
    temperature = Column(Float)  # Temperature in Celsius
    battery_level = Column(Float)  # Battery percentage
    signal_strength = Column(Float)  # Signal strength in dBm
    
    # Data quality indicators
    data_quality_score = Column(Float, default=1.0)  # 0-1 quality score
    is_anomaly = Column(Boolean, default=False)
    processing_flags = Column(JSONB)  # Processing metadata
    
    # Relationships
    sensor = relationship("Sensor", back_populates="telemetry_data")
    entity = relationship("Entity", back_populates="telemetry_data")
    
    # TimescaleDB-optimized indexes
    __table_args__ = (
        Index('idx_telemetry_timestamp_entity', 'timestamp', 'entity_id'),
        Index('idx_telemetry_sensor_timestamp', 'sensor_id', 'timestamp'),
        Index('idx_telemetry_location', 'location', postgresql_using='gist'),
        Index('idx_telemetry_metrics_gin', 'metrics', postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<SensorTelemetry(timestamp='{self.timestamp}', sensor_id='{self.sensor_id}')>"


class VirtualFence(Base):
    """
    Virtual Fence Boundaries
    
    Defines virtual boundaries for livestock management.
    Supports complex polygon geometries for flexible fence shapes.
    """
    __tablename__ = "virtual_fences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    farm_id = Column(String(100), nullable=False)
    
    # Geospatial boundary definition
    boundary = Column(Geography('POLYGON', srid=4326), nullable=False)
    buffer_zone_meters = Column(Float, default=10.0)  # Warning zone before boundary
    
    # Fence configuration
    fence_type = Column(String(50), default='containment')  # 'containment', 'exclusion'
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Higher priority overrides lower
    
    # Alert settings
    alert_on_entry = Column(Boolean, default=True)
    alert_on_exit = Column(Boolean, default=True)
    notification_delay_seconds = Column(Integer, default=30)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    fence_violations = relationship("FenceViolation", back_populates="fence")
    
    # Indexes
    __table_args__ = (
        Index('idx_virtual_fences_boundary', 'boundary', postgresql_using='gist'),
        Index('idx_virtual_fences_farm_active', 'farm_id', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<VirtualFence(name='{self.name}', farm_id='{self.farm_id}')>"


class FenceViolation(Base):
    """
    Virtual Fence Violation Events
    
    Records when entities cross virtual fence boundaries.
    Used for alerts and behavioral analysis.
    """
    __tablename__ = "fence_violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('entities.id'), nullable=False)
    fence_id = Column(UUID(as_uuid=True), ForeignKey('virtual_fences.id'), nullable=False)
    
    violation_timestamp = Column(DateTime(timezone=True), nullable=False)
    violation_type = Column(String(20), nullable=False)  # 'entry', 'exit'
    location = Column(Geography('POINT', srid=4326), nullable=False)
    
    # Violation details
    distance_from_boundary = Column(Float)  # Distance in meters
    duration_seconds = Column(Integer)  # How long the violation lasted
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high'
    
    # Response tracking
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime(timezone=True))
    response_action = Column(String(100))  # Action taken in response
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    entity = relationship("Entity")
    fence = relationship("VirtualFence", back_populates="fence_violations")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_fence_violations_timestamp', 'violation_timestamp'),
        Index('idx_fence_violations_entity_time', 'entity_id', 'violation_timestamp'),
        Index('idx_fence_violations_fence_time', 'fence_id', 'violation_timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<FenceViolation(entity_id='{self.entity_id}', type='{self.violation_type}')>"


class HealthAlert(Base):
    """
    Animal Health Alerts
    
    Stores health-related alerts generated from sensor data analysis.
    Supports both aquaculture and livestock health monitoring.
    """
    __tablename__ = "health_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('entities.id'), nullable=False)
    
    alert_timestamp = Column(DateTime(timezone=True), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'health_anomaly', 'behavior_change', etc.
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Alert details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    confidence_score = Column(Float)  # ML model confidence (0-1)
    
    # Source information
    source_sensor_ids = Column(JSONB)  # Array of sensor IDs that triggered alert
    trigger_metrics = Column(JSONB)  # Metrics that caused the alert
    ml_model_version = Column(String(50))  # Model version used for detection
    
    # Status tracking
    status = Column(String(20), default='open')  # 'open', 'investigating', 'resolved', 'false_positive'
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Relationships
    entity = relationship("Entity")
    
    # Indexes
    __table_args__ = (
        Index('idx_health_alerts_timestamp', 'alert_timestamp'),
        Index('idx_health_alerts_entity_time', 'entity_id', 'alert_timestamp'),
        Index('idx_health_alerts_severity_status', 'severity', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<HealthAlert(entity_id='{self.entity_id}', type='{self.alert_type}')>"
