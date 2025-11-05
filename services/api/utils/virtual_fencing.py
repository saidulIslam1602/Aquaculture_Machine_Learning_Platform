"""
Virtual Fencing Algorithms for Livestock Management

This module implements advanced virtual fencing algorithms for livestock monitoring
including boundary detection, violation alerts, and behavioral analysis.

Industry Standards:
    - Real-time geospatial processing
    - Configurable alert thresholds
    - Machine learning-ready feature extraction
    - Scalable algorithms for large herds
    - Integration with IoT sensor data
"""

import math
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from shapely.geometry import Point, Polygon
from shapely.ops import transform
import numpy as np

from .geospatial import (
    point_in_polygon, distance_to_polygon_boundary, 
    calculate_distance, calculate_bearing
)

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of fence violations"""
    ENTRY = "entry"
    EXIT = "exit"
    BREACH = "breach"
    APPROACH = "approach"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FenceConfig:
    """Virtual fence configuration"""
    fence_id: str
    name: str
    boundary_coordinates: List[List[float]]
    fence_type: str  # 'containment' or 'exclusion'
    buffer_zone_meters: float
    alert_on_entry: bool
    alert_on_exit: bool
    notification_delay_seconds: int
    is_active: bool


@dataclass
class AnimalLocation:
    """Animal location data"""
    entity_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading_degrees: Optional[float] = None


@dataclass
class ViolationEvent:
    """Fence violation event"""
    violation_id: str
    entity_id: str
    fence_id: str
    violation_type: ViolationType
    timestamp: datetime
    location: Tuple[float, float]  # (latitude, longitude)
    distance_from_boundary: float
    severity: AlertSeverity
    confidence_score: float
    metadata: Dict[str, Any]


class VirtualFenceEngine:
    """
    Advanced virtual fencing engine for livestock management.
    
    Provides real-time fence monitoring, violation detection,
    and behavioral analysis for agricultural IoT systems.
    """
    
    def __init__(self):
        self.active_fences: Dict[str, FenceConfig] = {}
        self.animal_locations: Dict[str, List[AnimalLocation]] = {}
        self.violation_history: Dict[str, List[ViolationEvent]] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}
        
    def register_fence(self, fence_config: FenceConfig) -> bool:
        """
        Register a virtual fence in the system.
        
        Args:
            fence_config: Fence configuration
            
        Returns:
            bool: True if successfully registered
        """
        try:
            # Validate fence configuration
            if not self._validate_fence_config(fence_config):
                return False
            
            self.active_fences[fence_config.fence_id] = fence_config
            logger.info(f"Registered virtual fence: {fence_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register fence {fence_config.fence_id}: {e}")
            return False
    
    def process_location_update(
        self, 
        location: AnimalLocation
    ) -> List[ViolationEvent]:
        """
        Process animal location update and check for fence violations.
        
        Args:
            location: Animal location data
            
        Returns:
            List of violation events detected
        """
        try:
            violations = []
            
            # Store location history
            if location.entity_id not in self.animal_locations:
                self.animal_locations[location.entity_id] = []
            
            self.animal_locations[location.entity_id].append(location)
            
            # Keep only recent locations (last 24 hours)
            cutoff_time = location.timestamp - timedelta(hours=24)
            self.animal_locations[location.entity_id] = [
                loc for loc in self.animal_locations[location.entity_id]
                if loc.timestamp >= cutoff_time
            ]
            
            # Check against all active fences
            for fence_id, fence_config in self.active_fences.items():
                if not fence_config.is_active:
                    continue
                
                violation = self._check_fence_violation(location, fence_config)
                if violation:
                    violations.append(violation)
                    
                    # Store violation history
                    if location.entity_id not in self.violation_history:
                        self.violation_history[location.entity_id] = []
                    self.violation_history[location.entity_id].append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error processing location update for {location.entity_id}: {e}")
            return []
    
    def _check_fence_violation(
        self, 
        location: AnimalLocation, 
        fence_config: FenceConfig
    ) -> Optional[ViolationEvent]:
        """
        Check if location violates a specific fence.
        
        Args:
            location: Animal location
            fence_config: Fence configuration
            
        Returns:
            ViolationEvent if violation detected, None otherwise
        """
        try:
            # Check if animal is inside fence boundary
            inside_fence = point_in_polygon(
                location.latitude, 
                location.longitude, 
                fence_config.boundary_coordinates
            )
            
            # Calculate distance to boundary
            distance_to_boundary = abs(distance_to_polygon_boundary(
                location.latitude,
                location.longitude,
                fence_config.boundary_coordinates
            ))
            
            # Get previous location for movement analysis
            previous_location = self._get_previous_location(location.entity_id)
            
            # Determine violation type
            violation_type = None
            severity = AlertSeverity.LOW
            
            if fence_config.fence_type == "containment":
                # Containment fence - animals should stay inside
                if not inside_fence and fence_config.alert_on_exit:
                    violation_type = ViolationType.EXIT
                    severity = self._calculate_severity(distance_to_boundary, fence_config)
                elif inside_fence and distance_to_boundary <= fence_config.buffer_zone_meters:
                    violation_type = ViolationType.APPROACH
                    severity = AlertSeverity.LOW
                    
            elif fence_config.fence_type == "exclusion":
                # Exclusion fence - animals should stay outside
                if inside_fence and fence_config.alert_on_entry:
                    violation_type = ViolationType.ENTRY
                    severity = self._calculate_severity(distance_to_boundary, fence_config)
                elif not inside_fence and distance_to_boundary <= fence_config.buffer_zone_meters:
                    violation_type = ViolationType.APPROACH
                    severity = AlertSeverity.LOW
            
            # Check if violation should trigger alert
            if violation_type and self._should_trigger_alert(
                location.entity_id, 
                fence_config.fence_id, 
                violation_type,
                location.timestamp,
                fence_config.notification_delay_seconds
            ):
                # Calculate confidence score based on GPS accuracy and movement
                confidence_score = self._calculate_confidence_score(
                    location, previous_location, distance_to_boundary
                )
                
                # Create violation event
                violation = ViolationEvent(
                    violation_id=f"{location.entity_id}_{fence_config.fence_id}_{int(location.timestamp.timestamp())}",
                    entity_id=location.entity_id,
                    fence_id=fence_config.fence_id,
                    violation_type=violation_type,
                    timestamp=location.timestamp,
                    location=(location.latitude, location.longitude),
                    distance_from_boundary=distance_to_boundary,
                    severity=severity,
                    confidence_score=confidence_score,
                    metadata={
                        "fence_name": fence_config.name,
                        "fence_type": fence_config.fence_type,
                        "gps_accuracy": location.accuracy_meters,
                        "animal_speed": location.speed_kmh,
                        "animal_heading": location.heading_degrees
                    }
                )
                
                # Update alert cooldown
                cooldown_key = f"{location.entity_id}_{fence_config.fence_id}"
                self.alert_cooldowns[cooldown_key] = location.timestamp
                
                return violation
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking fence violation: {e}")
            return None
    
    def _validate_fence_config(self, fence_config: FenceConfig) -> bool:
        """Validate fence configuration"""
        try:
            # Check required fields
            if not fence_config.fence_id or not fence_config.boundary_coordinates:
                return False
            
            # Validate boundary coordinates
            if len(fence_config.boundary_coordinates) < 3:
                return False
            
            for coord in fence_config.boundary_coordinates:
                if len(coord) != 2:
                    return False
                if not (-90 <= coord[1] <= 90) or not (-180 <= coord[0] <= 180):
                    return False
            
            # Validate fence type
            if fence_config.fence_type not in ["containment", "exclusion"]:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _get_previous_location(self, entity_id: str) -> Optional[AnimalLocation]:
        """Get the previous location for an animal"""
        if entity_id not in self.animal_locations:
            return None
        
        locations = self.animal_locations[entity_id]
        if len(locations) < 2:
            return None
        
        # Return second-to-last location (last is current)
        return locations[-2]
    
    def _calculate_severity(
        self, 
        distance_to_boundary: float, 
        fence_config: FenceConfig
    ) -> AlertSeverity:
        """Calculate violation severity based on distance"""
        if distance_to_boundary > fence_config.buffer_zone_meters * 3:
            return AlertSeverity.CRITICAL
        elif distance_to_boundary > fence_config.buffer_zone_meters * 2:
            return AlertSeverity.HIGH
        elif distance_to_boundary > fence_config.buffer_zone_meters:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _should_trigger_alert(
        self,
        entity_id: str,
        fence_id: str,
        violation_type: ViolationType,
        timestamp: datetime,
        delay_seconds: int
    ) -> bool:
        """Check if alert should be triggered based on cooldown"""
        cooldown_key = f"{entity_id}_{fence_id}"
        
        if cooldown_key not in self.alert_cooldowns:
            return True
        
        last_alert = self.alert_cooldowns[cooldown_key]
        time_since_last = (timestamp - last_alert).total_seconds()
        
        return time_since_last >= delay_seconds
    
    def _calculate_confidence_score(
        self,
        current_location: AnimalLocation,
        previous_location: Optional[AnimalLocation],
        distance_to_boundary: float
    ) -> float:
        """Calculate confidence score for violation detection"""
        try:
            confidence = 0.5  # Base confidence
            
            # GPS accuracy factor
            if current_location.accuracy_meters:
                if current_location.accuracy_meters <= 5:
                    confidence += 0.3
                elif current_location.accuracy_meters <= 10:
                    confidence += 0.2
                elif current_location.accuracy_meters <= 20:
                    confidence += 0.1
            
            # Movement consistency factor
            if previous_location:
                time_diff = (current_location.timestamp - previous_location.timestamp).total_seconds()
                if time_diff > 0:
                    distance = calculate_distance(
                        previous_location.latitude, previous_location.longitude,
                        current_location.latitude, current_location.longitude
                    )
                    calculated_speed = (distance / time_diff) * 3.6  # m/s to km/h
                    
                    # Check if calculated speed is reasonable for livestock
                    if 0 <= calculated_speed <= 25:  # Reasonable speed range
                        confidence += 0.2
            
            # Distance factor - closer to boundary = higher confidence
            if distance_to_boundary <= 5:
                confidence += 0.2
            elif distance_to_boundary <= 10:
                confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.5
    
    def get_fence_status(self, fence_id: str) -> Dict[str, Any]:
        """
        Get status information for a specific fence.
        
        Args:
            fence_id: Fence identifier
            
        Returns:
            Dict with fence status information
        """
        try:
            if fence_id not in self.active_fences:
                return {"error": "Fence not found"}
            
            fence_config = self.active_fences[fence_id]
            
            # Count recent violations
            recent_violations = 0
            animals_in_violation = set()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            for entity_id, violations in self.violation_history.items():
                for violation in violations:
                    if (violation.fence_id == fence_id and 
                        violation.timestamp >= cutoff_time):
                        recent_violations += 1
                        animals_in_violation.add(entity_id)
            
            return {
                "fence_id": fence_id,
                "name": fence_config.name,
                "fence_type": fence_config.fence_type,
                "is_active": fence_config.is_active,
                "recent_violations_24h": recent_violations,
                "animals_in_violation": len(animals_in_violation),
                "buffer_zone_meters": fence_config.buffer_zone_meters,
                "notification_delay_seconds": fence_config.notification_delay_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting fence status for {fence_id}: {e}")
            return {"error": str(e)}
    
    def get_animal_status(self, entity_id: str) -> Dict[str, Any]:
        """
        Get status information for a specific animal.
        
        Args:
            entity_id: Animal entity identifier
            
        Returns:
            Dict with animal status information
        """
        try:
            status = {
                "entity_id": entity_id,
                "last_location": None,
                "location_history_count": 0,
                "recent_violations": [],
                "current_fence_status": []
            }
            
            # Get location information
            if entity_id in self.animal_locations:
                locations = self.animal_locations[entity_id]
                status["location_history_count"] = len(locations)
                
                if locations:
                    last_location = locations[-1]
                    status["last_location"] = {
                        "timestamp": last_location.timestamp.isoformat(),
                        "latitude": last_location.latitude,
                        "longitude": last_location.longitude,
                        "accuracy_meters": last_location.accuracy_meters
                    }
            
            # Get recent violations
            if entity_id in self.violation_history:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                recent_violations = [
                    {
                        "violation_id": v.violation_id,
                        "fence_id": v.fence_id,
                        "violation_type": v.violation_type.value,
                        "timestamp": v.timestamp.isoformat(),
                        "severity": v.severity.value,
                        "distance_from_boundary": v.distance_from_boundary
                    }
                    for v in self.violation_history[entity_id]
                    if v.timestamp >= cutoff_time
                ]
                status["recent_violations"] = recent_violations
            
            # Check current fence status
            if entity_id in self.animal_locations and self.animal_locations[entity_id]:
                last_location = self.animal_locations[entity_id][-1]
                
                for fence_id, fence_config in self.active_fences.items():
                    if not fence_config.is_active:
                        continue
                    
                    inside_fence = point_in_polygon(
                        last_location.latitude,
                        last_location.longitude,
                        fence_config.boundary_coordinates
                    )
                    
                    distance = abs(distance_to_polygon_boundary(
                        last_location.latitude,
                        last_location.longitude,
                        fence_config.boundary_coordinates
                    ))
                    
                    status["current_fence_status"].append({
                        "fence_id": fence_id,
                        "fence_name": fence_config.name,
                        "inside_fence": inside_fence,
                        "distance_to_boundary": distance,
                        "within_buffer_zone": distance <= fence_config.buffer_zone_meters
                    })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting animal status for {entity_id}: {e}")
            return {"error": str(e)}
    
    def analyze_movement_patterns(
        self, 
        entity_id: str, 
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze animal movement patterns for behavioral insights.
        
        Args:
            entity_id: Animal entity identifier
            hours_back: Hours of history to analyze
            
        Returns:
            Dict with movement analysis
        """
        try:
            if entity_id not in self.animal_locations:
                return {"error": "No location data available"}
            
            locations = self.animal_locations[entity_id]
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Filter to recent locations
            recent_locations = [
                loc for loc in locations 
                if loc.timestamp >= cutoff_time
            ]
            
            if len(recent_locations) < 2:
                return {"error": "Insufficient location data"}
            
            # Calculate movement statistics
            total_distance = 0
            speeds = []
            
            for i in range(1, len(recent_locations)):
                prev_loc = recent_locations[i-1]
                curr_loc = recent_locations[i]
                
                distance = calculate_distance(
                    prev_loc.latitude, prev_loc.longitude,
                    curr_loc.latitude, curr_loc.longitude
                )
                
                time_diff = (curr_loc.timestamp - prev_loc.timestamp).total_seconds()
                
                if time_diff > 0:
                    speed = (distance / time_diff) * 3.6  # Convert to km/h
                    speeds.append(speed)
                    total_distance += distance
            
            # Calculate statistics
            analysis = {
                "entity_id": entity_id,
                "analysis_period_hours": hours_back,
                "total_locations": len(recent_locations),
                "total_distance_meters": total_distance,
                "avg_speed_kmh": np.mean(speeds) if speeds else 0,
                "max_speed_kmh": np.max(speeds) if speeds else 0,
                "movement_variance": np.var(speeds) if speeds else 0,
                "stationary_periods": 0,
                "active_periods": 0
            }
            
            # Identify stationary vs active periods
            stationary_threshold = 0.5  # km/h
            
            for speed in speeds:
                if speed <= stationary_threshold:
                    analysis["stationary_periods"] += 1
                else:
                    analysis["active_periods"] += 1
            
            # Calculate activity ratio
            total_periods = len(speeds)
            if total_periods > 0:
                analysis["activity_ratio"] = analysis["active_periods"] / total_periods
            else:
                analysis["activity_ratio"] = 0
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing movement patterns for {entity_id}: {e}")
            return {"error": str(e)}
