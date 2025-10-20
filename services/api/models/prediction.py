"""Prediction database model"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Prediction(Base):
    """Prediction model"""

    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"))
    image_path = Column(String(500))
    predicted_species_id = Column(Integer, ForeignKey("fish_species.id"))
    confidence = Column(Numeric(5, 4))
    inference_time_ms = Column(Integer)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    model = relationship("Model", back_populates="predictions")
    species = relationship("FishSpecies", back_populates="predictions")
    user = relationship("User")

    def __repr__(self):
        return f"<Prediction(id='{self.id}', confidence={self.confidence})>"


class FishSpecies(Base):
    """Fish species model"""

    __tablename__ = "fish_species"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    scientific_name = Column(String(200))
    description = Column(String)
    optimal_temperature_min = Column(Numeric(5, 2))
    optimal_temperature_max = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    predictions = relationship("Prediction", back_populates="species")

    def __repr__(self):
        return f"<FishSpecies(name='{self.name}')>"


class Model(Base):
    """ML Model model"""

    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    architecture = Column(String(100))
    file_path = Column(String(500))
    accuracy = Column(Numeric(5, 4))
    precision_score = Column(Numeric(5, 4))
    recall_score = Column(Numeric(5, 4))
    f1_score = Column(Numeric(5, 4))
    is_active = Column(Boolean, default=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    predictions = relationship("Prediction", back_populates="model")

    def __repr__(self):
        return f"<Model(name='{self.name}', version='{self.version}')>"
