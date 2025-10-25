"""
ML Prediction Routes - Core ML functionality
"""

import logging
import uuid
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_active_user
from ..core.config import settings
from ..models.user import User
from ..models.prediction import Prediction, FishSpecies, Model
from ..schemas.prediction import PredictionResponse
from ..services.ml_service import MLService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["Machine Learning"])

# Initialize ML service
ml_service = MLService()


@router.post("/classify", response_model=PredictionResponse, status_code=201)
async def classify_fish(
    file: UploadFile = File(..., description="Fish image (JPG, PNG, WEBP - Max 10MB)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PredictionResponse:
    """
    🐟 Classify Fish Species from Image
    
    Upload an image and get AI-powered fish species prediction with confidence score.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPG, PNG, WEBP)"
        )
    
    # Validate file size 
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be less than {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Get active model
        active_model = db.query(Model).filter(Model.is_active == True).first()
        if not active_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No active ML model available. Please contact administrator."
            )
        
        # Perform ML inference
        start_time = datetime.utcnow()
        prediction_result = await ml_service.predict_species(image_data)
        end_time = datetime.utcnow()
        
        inference_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Find or create fish species
        species = db.query(FishSpecies).filter(
            FishSpecies.name == prediction_result["species"]
        ).first()
        
        if not species and prediction_result["species"] != "Unknown":
            # Create new species if not found
            species = FishSpecies(
                name=prediction_result["species"],
                scientific_name=prediction_result.get("scientific_name"),
                description=prediction_result.get("description")
            )
            db.add(species)
            db.flush()
        elif not species:
            # Handle "Unknown" species case
            species = FishSpecies(
                name="Unknown",
                scientific_name="Classification uncertain",
                description="Species could not be classified with sufficient confidence"
            )
        
        # Save prediction to database
        db_prediction = Prediction(
            id=uuid.uuid4(),
            model_id=active_model.id,
            image_path=f"uploads/{current_user.id}/{uuid.uuid4()}_{file.filename}",
            predicted_species_id=species.id,
            confidence=prediction_result["confidence"],
            inference_time_ms=inference_time,
            metadata={
                "filename": file.filename,
                "file_size": file.size,
                "content_type": file.content_type,
                "model_version": active_model.version,
                "processing_status": prediction_result.get("status", "success")
            },
            created_by=current_user.id
        )
        
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        logger.info(f"Fish classification completed for user {current_user.id}: {species.name} ({prediction_result['confidence']:.4f})")
        
        return PredictionResponse(
            id=str(db_prediction.id),
            species_name=species.name,
            scientific_name=species.scientific_name,
            confidence=float(db_prediction.confidence),
            inference_time_ms=db_prediction.inference_time_ms,
            model_version=active_model.version,
            created_at=db_prediction.created_at,
            optimal_temp_range={
                "min": float(species.optimal_temperature_min) if species.optimal_temperature_min else None,
                "max": float(species.optimal_temperature_max) if species.optimal_temperature_max else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction service temporarily unavailable. Please try again later."
        )


@router.get("/history", response_model=List[PredictionResponse])
async def get_prediction_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[PredictionResponse]:
    """
    📊 Get User's Prediction History
    
    Retrieve paginated list of user's previous fish classifications.
    """
    predictions = (
        db.query(Prediction)
        .filter(Prediction.created_by == current_user.id)
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return [
        PredictionResponse(
            id=str(pred.id),
            species_name=pred.species.name,
            scientific_name=pred.species.scientific_name,
            confidence=float(pred.confidence),
            inference_time_ms=pred.inference_time_ms,
            model_version=pred.model.version,
            created_at=pred.created_at,
            optimal_temp_range={
                "min": float(pred.species.optimal_temperature_min) if pred.species.optimal_temperature_min else None,
                "max": float(pred.species.optimal_temperature_max) if pred.species.optimal_temperature_max else None
            }
        )
        for pred in predictions
    ]


@router.get("/species", response_model=List[dict])
async def get_fish_species(
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    🐠 Get All Fish Species
    
    Retrieve list of all fish species that can be classified by the ML model.
    """
    species = db.query(FishSpecies).all()
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "scientific_name": s.scientific_name,
            "description": s.description,
            "optimal_temperature_range": {
                "min": float(s.optimal_temperature_min) if s.optimal_temperature_min else None,
                "max": float(s.optimal_temperature_max) if s.optimal_temperature_max else None
            }
        }
        for s in species
    ]


@router.get("/stats", response_model=dict)
async def get_prediction_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    📈 Get User's Prediction Statistics
    
    Returns user-specific prediction analytics and insights.
    """
    user_predictions = db.query(Prediction).filter(
        Prediction.created_by == current_user.id
    ).all()
    
    if not user_predictions:
        return {
            "total_predictions": 0,
            "average_confidence": 0,
            "most_common_species": None,
            "predictions_this_month": 0
        }
    
    # Calculate statistics
    total_predictions = len(user_predictions)
    avg_confidence = sum(float(p.confidence) for p in user_predictions) / total_predictions
    
    # Find most common species
    species_counts = {}
    for pred in user_predictions:
        species_name = pred.species.name
        species_counts[species_name] = species_counts.get(species_name, 0) + 1
    
    most_common_species = max(species_counts, key=species_counts.get) if species_counts else None
    
    # Count predictions this month
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    predictions_this_month = sum(
        1 for p in user_predictions if p.created_at >= current_month
    )
    
    return {
        "total_predictions": total_predictions,
        "average_confidence": round(avg_confidence, 4),
        "most_common_species": most_common_species,
        "predictions_this_month": predictions_this_month,
        "species_variety": len(species_counts),
        "species_breakdown": species_counts
    }