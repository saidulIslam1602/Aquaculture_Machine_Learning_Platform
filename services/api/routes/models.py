"""
ML Models Management Routes
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.prediction import Model
from ..services.ml_service import MLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Model Management"])
ml_service = MLService()


@router.get("/active", response_model=dict)
async def get_active_model(
    db: Session = Depends(get_db)
) -> dict:
    """
    🤖 Get Active ML Model Information
    
    Returns information about the currently active model being used for predictions.
    """
    active_model = db.query(Model).filter(Model.is_active == True).first()
    
    if not active_model:
        raise HTTPException(
            status_code=404,
            detail="No active model found"
        )
    
    model_info = ml_service.get_model_info()
    
    return {
        "id": str(active_model.id),
        "name": active_model.name,
        "version": active_model.version,
        "architecture": active_model.architecture,
        "accuracy": float(active_model.accuracy) if active_model.accuracy else None,
        "precision": float(active_model.precision_score) if active_model.precision_score else None,
        "recall": float(active_model.recall_score) if active_model.recall_score else None,
        "f1_score": float(active_model.f1_score) if active_model.f1_score else None,
        "created_at": active_model.created_at,
        "supported_species": model_info["supported_species"],
        "total_species": model_info["total_species"],
        "confidence_threshold": model_info["confidence_threshold"],
        "inference_device": model_info["inference_device"]
    }


@router.get("/all", response_model=List[dict])
async def get_all_models(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    📊 Get All ML Models
    
    Returns list of all available ML models with their performance metrics.
    """
    models = db.query(Model).order_by(Model.created_at.desc()).all()
    
    return [
        {
            "id": str(model.id),
            "name": model.name,
            "version": model.version,
            "architecture": model.architecture,
            "accuracy": float(model.accuracy) if model.accuracy else None,
            "precision": float(model.precision_score) if model.precision_score else None,
            "recall": float(model.recall_score) if model.recall_score else None,
            "f1_score": float(model.f1_score) if model.f1_score else None,
            "is_active": model.is_active,
            "created_at": model.created_at,
            "total_predictions": len(model.predictions) if model.predictions else 0
        }
        for model in models
    ]


@router.get("/stats", response_model=dict)
async def get_model_stats(
    db: Session = Depends(get_db)
) -> dict:
    """
    📈 Get Model Performance Statistics
    
    Returns aggregated statistics about model performance and usage.
    """
    active_model = db.query(Model).filter(Model.is_active == True).first()
    
    if not active_model:
        return {"error": "No active model"}
    
    # Calculate stats from predictions
    total_predictions = len(active_model.predictions) if active_model.predictions else 0
    
    if total_predictions > 0:
        confidences = [float(p.confidence) for p in active_model.predictions if p.confidence]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        inference_times = [p.inference_time_ms for p in active_model.predictions if p.inference_time_ms]
        avg_inference_time = sum(inference_times) / len(inference_times) if inference_times else 0
        
        # Calculate confidence distribution
        high_confidence = sum(1 for c in confidences if c >= 0.9)
        medium_confidence = sum(1 for c in confidences if 0.7 <= c < 0.9)
        low_confidence = sum(1 for c in confidences if c < 0.7)
        
    else:
        avg_confidence = 0
        avg_inference_time = 0
        high_confidence = medium_confidence = low_confidence = 0
    
    return {
        "model_name": active_model.name,
        "model_version": active_model.version,
        "total_predictions": total_predictions,
        "average_confidence": round(avg_confidence, 4),
        "average_inference_time_ms": round(avg_inference_time, 2),
        "accuracy": float(active_model.accuracy) if active_model.accuracy else None,
        "precision": float(active_model.precision_score) if active_model.precision_score else None,
        "recall": float(active_model.recall_score) if active_model.recall_score else None,
        "f1_score": float(active_model.f1_score) if active_model.f1_score else None,
        "confidence_distribution": {
            "high_confidence": high_confidence,  # >= 90%
            "medium_confidence": medium_confidence,  # 70-89%
            "low_confidence": low_confidence  # < 70%
        }
    }


@router.get("/health", response_model=dict)
async def check_model_health() -> dict:
    """
    🏥 Check ML Model Health
    
    Returns health status of the ML service and model availability.
    """
    model_health = ml_service.is_healthy()
    model_info = ml_service.get_model_info()
    
    return {
        "status": "healthy" if model_health else "unhealthy",
        "model_loaded": model_info["model_loaded"],
        "model_name": model_info["model_name"],
        "model_version": model_info["model_version"],
        "supported_species": len(model_info["supported_species"]),
        "inference_device": model_info["inference_device"],
        "ready_for_predictions": model_health
    }