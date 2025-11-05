"""
Geospatial Utilities for Agricultural IoT Platform

This module provides geospatial functions for virtual fencing, location tracking,
and spatial analysis of agricultural entities.

Industry Standards:
    - Use of standard geospatial libraries (Shapely, GeoPandas)
    - Proper coordinate system handling (WGS84)
    - Efficient spatial algorithms
    - Error handling for edge cases
    - Performance optimization for real-time processing
"""

import math
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj
from functools import partial
import logging

logger = logging.getLogger(__name__)


def calculate_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Uses the Haversine formula to calculate the distance between two points
    on the Earth's surface given their latitude and longitude coordinates.
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees
        
    Returns:
        float: Distance between points in meters
        
    Example:
        >>> distance = calculate_distance(59.9139, 10.7522, 59.9145, 10.7530)
        >>> print(f"Distance: {distance:.2f} meters")
    """
    try:
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in meters
        earth_radius = 6371000
        
        distance = earth_radius * c
        return distance
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error calculating distance: {e}")
        return 0.0


def point_in_polygon(
    latitude: float, 
    longitude: float, 
    polygon_coords: List[List[float]]
) -> bool:
    """
    Check if a point is inside a polygon.
    
    Uses the Shapely library to perform point-in-polygon test.
    
    Args:
        latitude: Point latitude in decimal degrees
        longitude: Point longitude in decimal degrees
        polygon_coords: List of [longitude, latitude] coordinate pairs defining polygon
        
    Returns:
        bool: True if point is inside polygon, False otherwise
        
    Example:
        >>> coords = [[10.7522, 59.9139], [10.7530, 59.9145], [10.7540, 59.9135], [10.7522, 59.9139]]
        >>> inside = point_in_polygon(59.9140, 10.7525, coords)
    """
    try:
        # Create point geometry
        point = Point(longitude, latitude)
        
        # Create polygon geometry from coordinates
        # Note: Shapely expects (x, y) which is (longitude, latitude)
        polygon_points = [(coord[0], coord[1]) for coord in polygon_coords]
        polygon = Polygon(polygon_points)
        
        return polygon.contains(point)
        
    except Exception as e:
        logger.error(f"Error checking point in polygon: {e}")
        return False


def calculate_polygon_area(polygon_coords: List[List[float]]) -> float:
    """
    Calculate the area of a polygon in square meters.
    
    Uses UTM projection for accurate area calculation.
    
    Args:
        polygon_coords: List of [longitude, latitude] coordinate pairs
        
    Returns:
        float: Area in square meters
    """
    try:
        # Create polygon geometry
        polygon_points = [(coord[0], coord[1]) for coord in polygon_coords]
        polygon = Polygon(polygon_points)
        
        # Get the centroid to determine appropriate UTM zone
        centroid = polygon.centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        
        # Create UTM projection
        utm_crs = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
        wgs84_crs = "+proj=longlat +datum=WGS84 +no_defs"
        
        project = pyproj.Transformer.from_crs(wgs84_crs, utm_crs, always_xy=True)
        
        # Transform polygon to UTM coordinates
        utm_polygon = transform(project.transform, polygon)
        
        return utm_polygon.area
        
    except Exception as e:
        logger.error(f"Error calculating polygon area: {e}")
        return 0.0


def get_polygon_centroid(polygon_coords: List[List[float]]) -> Tuple[float, float]:
    """
    Get the centroid (center point) of a polygon.
    
    Args:
        polygon_coords: List of [longitude, latitude] coordinate pairs
        
    Returns:
        Tuple[float, float]: (longitude, latitude) of centroid
    """
    try:
        polygon_points = [(coord[0], coord[1]) for coord in polygon_coords]
        polygon = Polygon(polygon_points)
        centroid = polygon.centroid
        
        return (centroid.x, centroid.y)
        
    except Exception as e:
        logger.error(f"Error calculating polygon centroid: {e}")
        return (0.0, 0.0)


def distance_to_polygon_boundary(
    latitude: float, 
    longitude: float, 
    polygon_coords: List[List[float]]
) -> float:
    """
    Calculate the shortest distance from a point to a polygon boundary.
    
    Args:
        latitude: Point latitude in decimal degrees
        longitude: Point longitude in decimal degrees
        polygon_coords: List of [longitude, latitude] coordinate pairs
        
    Returns:
        float: Distance to boundary in meters (negative if inside polygon)
    """
    try:
        point = Point(longitude, latitude)
        polygon_points = [(coord[0], coord[1]) for coord in polygon_coords]
        polygon = Polygon(polygon_points)
        
        # Calculate distance to boundary
        distance_degrees = point.distance(polygon.boundary)
        
        # Convert degrees to meters (approximate)
        # 1 degree of latitude ≈ 111,320 meters
        # 1 degree of longitude varies by latitude
        lat_rad = math.radians(latitude)
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * math.cos(lat_rad)
        
        # Use average for approximation
        avg_meters_per_degree = (meters_per_degree_lat + meters_per_degree_lon) / 2
        distance_meters = distance_degrees * avg_meters_per_degree
        
        # Return negative distance if point is inside polygon
        if polygon.contains(point):
            return -distance_meters
        else:
            return distance_meters
            
    except Exception as e:
        logger.error(f"Error calculating distance to boundary: {e}")
        return 0.0


def create_buffer_zone(
    polygon_coords: List[List[float]], 
    buffer_meters: float
) -> List[List[float]]:
    """
    Create a buffer zone around a polygon.
    
    Args:
        polygon_coords: Original polygon coordinates
        buffer_meters: Buffer distance in meters
        
    Returns:
        List[List[float]]: Buffered polygon coordinates
    """
    try:
        polygon_points = [(coord[0], coord[1]) for coord in polygon_coords]
        polygon = Polygon(polygon_points)
        
        # Convert buffer from meters to degrees (approximate)
        # This is a rough approximation - for precise work, use UTM projection
        buffer_degrees = buffer_meters / 111320
        
        buffered_polygon = polygon.buffer(buffer_degrees)
        
        # Extract coordinates from buffered polygon
        if hasattr(buffered_polygon, 'exterior'):
            coords = list(buffered_polygon.exterior.coords)
            return [[coord[0], coord[1]] for coord in coords]
        else:
            return polygon_coords
            
    except Exception as e:
        logger.error(f"Error creating buffer zone: {e}")
        return polygon_coords


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate GPS coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        bool: True if coordinates are valid, False otherwise
    """
    try:
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False
            
        if not (-90 <= latitude <= 90):
            return False
            
        if not (-180 <= longitude <= 180):
            return False
            
        return True
        
    except Exception:
        return False


def get_bounding_box(coordinates: List[List[float]]) -> Dict[str, float]:
    """
    Get the bounding box of a set of coordinates.
    
    Args:
        coordinates: List of [longitude, latitude] coordinate pairs
        
    Returns:
        Dict with min_lat, max_lat, min_lon, max_lon
    """
    try:
        if not coordinates:
            return {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0}
        
        lats = [coord[1] for coord in coordinates]
        lons = [coord[0] for coord in coordinates]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons)
        }
        
    except Exception as e:
        logger.error(f"Error calculating bounding box: {e}")
        return {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0}


def calculate_bearing(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calculate the bearing (direction) from point 1 to point 2.
    
    Args:
        lat1, lon1: Starting point coordinates
        lat2, lon2: Ending point coordinates
        
    Returns:
        float: Bearing in degrees (0-360, where 0 is North)
    """
    try:
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalize to 0-360 degrees
        bearing_deg = (bearing_deg + 360) % 360
        
        return bearing_deg
        
    except Exception as e:
        logger.error(f"Error calculating bearing: {e}")
        return 0.0


def get_nearest_fence(
    latitude: float, 
    longitude: float, 
    fences: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Find the nearest virtual fence to a given point.
    
    Args:
        latitude: Point latitude
        longitude: Point longitude
        fences: List of fence dictionaries with boundary coordinates
        
    Returns:
        Dict with nearest fence information or None if no fences
    """
    try:
        if not fences:
            return None
        
        point = Point(longitude, latitude)
        nearest_fence = None
        min_distance = float('inf')
        
        for fence in fences:
            if 'boundary_coordinates' not in fence:
                continue
                
            try:
                polygon_points = [(coord[0], coord[1]) for coord in fence['boundary_coordinates']]
                polygon = Polygon(polygon_points)
                
                distance = point.distance(polygon.boundary)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_fence = fence.copy()
                    nearest_fence['distance_meters'] = distance * 111320  # Approximate conversion
                    
            except Exception as e:
                logger.warning(f"Error processing fence {fence.get('id', 'unknown')}: {e}")
                continue
        
        return nearest_fence
        
    except Exception as e:
        logger.error(f"Error finding nearest fence: {e}")
        return None


def simplify_polygon(
    polygon_coords: List[List[float]], 
    tolerance_meters: float = 1.0
) -> List[List[float]]:
    """
    Simplify a polygon by removing unnecessary points.
    
    Args:
        polygon_coords: Original polygon coordinates
        tolerance_meters: Simplification tolerance in meters
        
    Returns:
        List[List[float]]: Simplified polygon coordinates
    """
    try:
        polygon_points = [(coord[0], coord[1]) for coord in polygon_coords]
        polygon = Polygon(polygon_points)
        
        # Convert tolerance from meters to degrees (approximate)
        tolerance_degrees = tolerance_meters / 111320
        
        simplified_polygon = polygon.simplify(tolerance_degrees, preserve_topology=True)
        
        if hasattr(simplified_polygon, 'exterior'):
            coords = list(simplified_polygon.exterior.coords)
            return [[coord[0], coord[1]] for coord in coords]
        else:
            return polygon_coords
            
    except Exception as e:
        logger.error(f"Error simplifying polygon: {e}")
        return polygon_coords
