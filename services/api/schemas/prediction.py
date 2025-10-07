"""Prediction Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PredictionBase(BaseModel):
    """Base prediction schema"""

    predicted_species_id: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    inference_time_ms: int


class PredictionCreate(PredictionBase):
    """Schema for creating a prediction"""

    model_id: UUID
    image_path: str
    metadata: Optional[Dict[str, Any]] = None


class PredictionResponse(PredictionBase):
    """Prediction response schema"""

    id: UUID
    model_id: UUID
    image_path: str
    species_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FishSpeciesResponse(BaseModel):
    """Fish species response schema"""

    id: int
    name: str
    scientific_name: Optional[str] = None
    description: Optional[str] = None
    optimal_temperature_min: Optional[float] = None
    optimal_temperature_max: Optional[float] = None

    class Config:
        from_attributes = True


class InferenceRequest(BaseModel):
    """Request schema for inference"""

    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    model_version: Optional[str] = None


class InferenceResponse(BaseModel):
    """Response schema for inference"""

    species_name: str
    species_id: int
    confidence: float
    inference_time_ms: int
    all_probabilities: Optional[Dict[str, float]] = None
