"""
Animal Health Analysis Utilities

This module provides algorithms for analyzing animal health data from IoT sensors,
detecting anomalies, and generating health alerts for both aquaculture and livestock.

Industry Standards:
    - Statistical anomaly detection methods
    - Machine learning-ready feature extraction
    - Configurable thresholds for different species
    - Comprehensive health scoring algorithms
    - Real-time processing capabilities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status classifications"""
    HEALTHY = "healthy"
    MONITORING = "monitoring"
    CONCERN = "concern"
    ALERT = "alert"
    CRITICAL = "critical"


class AnimalType(Enum):
    """Supported animal types for health analysis"""
    CATTLE = "cattle"
    SHEEP = "sheep"
    GOAT = "goat"
    PIG = "pig"
    FISH = "fish"
    CHICKEN = "chicken"


@dataclass
class HealthThresholds:
    """Health parameter thresholds for different animal types"""
    heart_rate_min: int
    heart_rate_max: int
    temperature_min: float
    temperature_max: float
    activity_min: float
    activity_max: float
    rumination_min: int  # minutes per day
    rumination_max: int


# Species-specific health thresholds
HEALTH_THRESHOLDS = {
    AnimalType.CATTLE: HealthThresholds(
        heart_rate_min=48, heart_rate_max=84,
        temperature_min=37.5, temperature_max=39.5,
        activity_min=0.2, activity_max=1.0,
        rumination_min=300, rumination_max=600
    ),
    AnimalType.SHEEP: HealthThresholds(
        heart_rate_min=70, heart_rate_max=120,
        temperature_min=38.5, temperature_max=40.0,
        activity_min=0.3, activity_max=1.0,
        rumination_min=240, rumination_max=480
    ),
    AnimalType.GOAT: HealthThresholds(
        heart_rate_min=70, heart_rate_max=120,
        temperature_min=38.5, temperature_max=40.5,
        activity_min=0.3, activity_max=1.0,
        rumination_min=240, rumination_max=480
    ),
    AnimalType.PIG: HealthThresholds(
        heart_rate_min=60, heart_rate_max=100,
        temperature_min=38.0, temperature_max=39.5,
        activity_min=0.2, activity_max=1.0,
        rumination_min=0, rumination_max=0  # Pigs don't ruminate
    ),
    AnimalType.FISH: HealthThresholds(
        heart_rate_min=30, heart_rate_max=120,
        temperature_min=10.0, temperature_max=30.0,
        activity_min=0.1, activity_max=1.0,
        rumination_min=0, rumination_max=0
    )
}


class HealthAnalyzer:
    """
    Comprehensive health analysis engine for agricultural animals.
    
    Provides real-time health monitoring, anomaly detection, and
    predictive health analytics for various animal species.
    """
    
    def __init__(self, animal_type: AnimalType):
        self.animal_type = animal_type
        self.thresholds = HEALTH_THRESHOLDS.get(animal_type)
        if not self.thresholds:
            logger.warning(f"No thresholds defined for {animal_type}, using cattle defaults")
            self.thresholds = HEALTH_THRESHOLDS[AnimalType.CATTLE]
    
    def analyze_real_time_metrics(
        self, 
        metrics: Dict[str, Any], 
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Analyze real-time sensor metrics for health indicators.
        
        Args:
            metrics: Dictionary of sensor readings
            timestamp: Timestamp of the readings
            
        Returns:
            Dict with health analysis results
        """
        try:
            analysis_result = {
                "timestamp": timestamp.isoformat(),
                "health_score": 1.0,
                "status": HealthStatus.HEALTHY.value,
                "alerts": [],
                "anomalies": [],
                "recommendations": []
            }
            
            # Analyze heart rate
            if "heart_rate" in metrics:
                hr_analysis = self._analyze_heart_rate(metrics["heart_rate"])
                analysis_result["heart_rate_analysis"] = hr_analysis
                if hr_analysis["anomaly"]:
                    analysis_result["anomalies"].append(hr_analysis)
                    analysis_result["health_score"] *= hr_analysis["severity_factor"]
            
            # Analyze body temperature
            if "temperature" in metrics or "body_temperature" in metrics:
                temp = metrics.get("temperature") or metrics.get("body_temperature")
                temp_analysis = self._analyze_temperature(temp)
                analysis_result["temperature_analysis"] = temp_analysis
                if temp_analysis["anomaly"]:
                    analysis_result["anomalies"].append(temp_analysis)
                    analysis_result["health_score"] *= temp_analysis["severity_factor"]
            
            # Analyze activity level
            if "activity_level" in metrics:
                activity_analysis = self._analyze_activity(metrics["activity_level"])
                analysis_result["activity_analysis"] = activity_analysis
                if activity_analysis["anomaly"]:
                    analysis_result["anomalies"].append(activity_analysis)
                    analysis_result["health_score"] *= activity_analysis["severity_factor"]
            
            # Analyze rumination (for ruminants)
            if "rumination_time" in metrics and self.thresholds.rumination_max > 0:
                rumination_analysis = self._analyze_rumination(metrics["rumination_time"])
                analysis_result["rumination_analysis"] = rumination_analysis
                if rumination_analysis["anomaly"]:
                    analysis_result["anomalies"].append(rumination_analysis)
                    analysis_result["health_score"] *= rumination_analysis["severity_factor"]
            
            # Determine overall health status
            analysis_result["status"] = self._determine_health_status(analysis_result["health_score"])
            
            # Generate alerts if necessary
            if analysis_result["health_score"] < 0.8:
                analysis_result["alerts"] = self._generate_health_alerts(analysis_result)
            
            # Generate recommendations
            analysis_result["recommendations"] = self._generate_recommendations(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing real-time metrics: {e}")
            return {
                "timestamp": timestamp.isoformat(),
                "health_score": 0.5,
                "status": HealthStatus.MONITORING.value,
                "error": str(e)
            }
    
    def _analyze_heart_rate(self, heart_rate: float) -> Dict[str, Any]:
        """Analyze heart rate for anomalies"""
        try:
            anomaly = False
            severity = "normal"
            severity_factor = 1.0
            message = "Heart rate within normal range"
            
            if heart_rate < self.thresholds.heart_rate_min:
                anomaly = True
                severity = "low" if heart_rate > self.thresholds.heart_rate_min * 0.8 else "critical"
                severity_factor = 0.7 if severity == "low" else 0.3
                message = f"Heart rate below normal range: {heart_rate} BPM"
                
            elif heart_rate > self.thresholds.heart_rate_max:
                anomaly = True
                severity = "high" if heart_rate < self.thresholds.heart_rate_max * 1.2 else "critical"
                severity_factor = 0.7 if severity == "high" else 0.3
                message = f"Heart rate above normal range: {heart_rate} BPM"
            
            return {
                "parameter": "heart_rate",
                "value": heart_rate,
                "normal_range": f"{self.thresholds.heart_rate_min}-{self.thresholds.heart_rate_max} BPM",
                "anomaly": anomaly,
                "severity": severity,
                "severity_factor": severity_factor,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error analyzing heart rate: {e}")
            return {"parameter": "heart_rate", "error": str(e)}
    
    def _analyze_temperature(self, temperature: float) -> Dict[str, Any]:
        """Analyze body temperature for anomalies"""
        try:
            anomaly = False
            severity = "normal"
            severity_factor = 1.0
            message = "Body temperature within normal range"
            
            if temperature < self.thresholds.temperature_min:
                anomaly = True
                severity = "low" if temperature > self.thresholds.temperature_min - 1.0 else "critical"
                severity_factor = 0.6 if severity == "low" else 0.2
                message = f"Body temperature below normal: {temperature}°C"
                
            elif temperature > self.thresholds.temperature_max:
                anomaly = True
                severity = "high" if temperature < self.thresholds.temperature_max + 1.0 else "critical"
                severity_factor = 0.6 if severity == "high" else 0.2
                message = f"Body temperature above normal: {temperature}°C"
            
            return {
                "parameter": "temperature",
                "value": temperature,
                "normal_range": f"{self.thresholds.temperature_min}-{self.thresholds.temperature_max}°C",
                "anomaly": anomaly,
                "severity": severity,
                "severity_factor": severity_factor,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temperature: {e}")
            return {"parameter": "temperature", "error": str(e)}
    
    def _analyze_activity(self, activity_level: float) -> Dict[str, Any]:
        """Analyze activity level for anomalies"""
        try:
            anomaly = False
            severity = "normal"
            severity_factor = 1.0
            message = "Activity level within normal range"
            
            if activity_level < self.thresholds.activity_min:
                anomaly = True
                severity = "low"
                severity_factor = 0.8
                message = f"Activity level below normal: {activity_level}"
                
            elif activity_level > self.thresholds.activity_max:
                anomaly = True
                severity = "high"
                severity_factor = 0.9
                message = f"Activity level above normal: {activity_level}"
            
            return {
                "parameter": "activity_level",
                "value": activity_level,
                "normal_range": f"{self.thresholds.activity_min}-{self.thresholds.activity_max}",
                "anomaly": anomaly,
                "severity": severity,
                "severity_factor": severity_factor,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error analyzing activity: {e}")
            return {"parameter": "activity_level", "error": str(e)}
    
    def _analyze_rumination(self, rumination_time: int) -> Dict[str, Any]:
        """Analyze rumination time for ruminants"""
        try:
            anomaly = False
            severity = "normal"
            severity_factor = 1.0
            message = "Rumination time within normal range"
            
            if rumination_time < self.thresholds.rumination_min:
                anomaly = True
                severity = "low"
                severity_factor = 0.7
                message = f"Rumination time below normal: {rumination_time} minutes"
                
            elif rumination_time > self.thresholds.rumination_max:
                anomaly = True
                severity = "high"
                severity_factor = 0.9
                message = f"Rumination time above normal: {rumination_time} minutes"
            
            return {
                "parameter": "rumination_time",
                "value": rumination_time,
                "normal_range": f"{self.thresholds.rumination_min}-{self.thresholds.rumination_max} minutes",
                "anomaly": anomaly,
                "severity": severity,
                "severity_factor": severity_factor,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error analyzing rumination: {e}")
            return {"parameter": "rumination_time", "error": str(e)}
    
    def _determine_health_status(self, health_score: float) -> str:
        """Determine overall health status based on score"""
        if health_score >= 0.9:
            return HealthStatus.HEALTHY.value
        elif health_score >= 0.7:
            return HealthStatus.MONITORING.value
        elif health_score >= 0.5:
            return HealthStatus.CONCERN.value
        elif health_score >= 0.3:
            return HealthStatus.ALERT.value
        else:
            return HealthStatus.CRITICAL.value
    
    def _generate_health_alerts(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate health alerts based on analysis results"""
        alerts = []
        
        for anomaly in analysis_result.get("anomalies", []):
            if anomaly.get("severity") in ["high", "critical", "low"]:
                alert = {
                    "type": "health_anomaly",
                    "parameter": anomaly.get("parameter"),
                    "severity": anomaly.get("severity"),
                    "message": anomaly.get("message"),
                    "timestamp": analysis_result["timestamp"],
                    "requires_attention": anomaly.get("severity") in ["critical"]
                }
                alerts.append(alert)
        
        return alerts
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on analysis"""
        recommendations = []
        
        for anomaly in analysis_result.get("anomalies", []):
            parameter = anomaly.get("parameter")
            severity = anomaly.get("severity")
            
            if parameter == "heart_rate":
                if severity == "high":
                    recommendations.append("Monitor for stress factors, check for fever or pain")
                elif severity == "low":
                    recommendations.append("Check for sedation effects or cardiovascular issues")
                    
            elif parameter == "temperature":
                if severity == "high":
                    recommendations.append("Check for infection, provide cooling, contact veterinarian")
                elif severity == "low":
                    recommendations.append("Check for hypothermia, provide warming")
                    
            elif parameter == "activity_level":
                if severity == "low":
                    recommendations.append("Monitor for lameness, illness, or environmental factors")
                elif severity == "high":
                    recommendations.append("Check for stress, pain, or abnormal behavior")
                    
            elif parameter == "rumination_time":
                if severity == "low":
                    recommendations.append("Check feed quality, monitor for digestive issues")
        
        return recommendations


def analyze_animal_health(
    animal_type: str,
    metrics: Dict[str, Any],
    timestamp: datetime
) -> Dict[str, Any]:
    """
    Convenience function for analyzing animal health.
    
    Args:
        animal_type: Type of animal (cattle, sheep, etc.)
        metrics: Sensor metrics dictionary
        timestamp: Timestamp of measurements
        
    Returns:
        Dict with health analysis results
    """
    try:
        # Convert string to enum
        animal_enum = AnimalType(animal_type.lower())
        analyzer = HealthAnalyzer(animal_enum)
        return analyzer.analyze_real_time_metrics(metrics, timestamp)
        
    except ValueError:
        logger.warning(f"Unknown animal type: {animal_type}, using cattle defaults")
        analyzer = HealthAnalyzer(AnimalType.CATTLE)
        return analyzer.analyze_real_time_metrics(metrics, timestamp)
    except Exception as e:
        logger.error(f"Error in health analysis: {e}")
        return {
            "timestamp": timestamp.isoformat(),
            "health_score": 0.5,
            "status": HealthStatus.MONITORING.value,
            "error": str(e)
        }


def calculate_health_trend(
    historical_scores: List[Tuple[datetime, float]],
    window_days: int = 7
) -> Dict[str, Any]:
    """
    Calculate health trend over time.
    
    Args:
        historical_scores: List of (timestamp, health_score) tuples
        window_days: Number of days to analyze for trend
        
    Returns:
        Dict with trend analysis
    """
    try:
        if len(historical_scores) < 2:
            return {"trend": "insufficient_data", "slope": 0, "confidence": 0}
        
        # Convert to pandas for easier analysis
        df = pd.DataFrame(historical_scores, columns=['timestamp', 'health_score'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Filter to recent window
        cutoff_date = df['timestamp'].max() - timedelta(days=window_days)
        recent_data = df[df['timestamp'] >= cutoff_date]
        
        if len(recent_data) < 2:
            return {"trend": "insufficient_data", "slope": 0, "confidence": 0}
        
        # Calculate trend using linear regression
        x = np.arange(len(recent_data))
        y = recent_data['health_score'].values
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Determine trend direction
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "improving"
        else:
            trend = "declining"
        
        # Calculate confidence based on R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            "trend": trend,
            "slope": float(slope),
            "confidence": float(r_squared),
            "data_points": len(recent_data),
            "window_days": window_days,
            "current_score": float(recent_data['health_score'].iloc[-1]),
            "average_score": float(recent_data['health_score'].mean())
        }
        
    except Exception as e:
        logger.error(f"Error calculating health trend: {e}")
        return {"trend": "error", "slope": 0, "confidence": 0, "error": str(e)}


def detect_behavioral_anomalies(
    activity_data: List[Dict[str, Any]],
    baseline_days: int = 14
) -> List[Dict[str, Any]]:
    """
    Detect behavioral anomalies using statistical methods.
    
    Args:
        activity_data: List of activity measurements with timestamps
        baseline_days: Number of days to use for baseline calculation
        
    Returns:
        List of detected anomalies
    """
    try:
        if len(activity_data) < baseline_days:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(activity_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate baseline statistics
        baseline_cutoff = df['timestamp'].max() - timedelta(days=baseline_days)
        baseline_data = df[df['timestamp'] <= baseline_cutoff]
        
        if len(baseline_data) < 5:  # Need minimum data for statistics
            return []
        
        # Calculate baseline mean and standard deviation
        baseline_mean = baseline_data['activity_level'].mean()
        baseline_std = baseline_data['activity_level'].std()
        
        # Detect anomalies using 2-sigma rule
        anomalies = []
        threshold = 2 * baseline_std
        
        recent_data = df[df['timestamp'] > baseline_cutoff]
        
        for _, row in recent_data.iterrows():
            deviation = abs(row['activity_level'] - baseline_mean)
            
            if deviation > threshold:
                anomaly_type = "high_activity" if row['activity_level'] > baseline_mean else "low_activity"
                severity = "critical" if deviation > 3 * baseline_std else "moderate"
                
                anomalies.append({
                    "timestamp": row['timestamp'].isoformat(),
                    "type": anomaly_type,
                    "severity": severity,
                    "value": row['activity_level'],
                    "baseline_mean": baseline_mean,
                    "deviation": deviation,
                    "threshold": threshold
                })
        
        return anomalies
        
    except Exception as e:
        logger.error(f"Error detecting behavioral anomalies: {e}")
        return []
