"""
ML Service Configuration Module

Manages configuration for model serving, inference, and monitoring.

Industry Standards:
    - Separation of ML-specific configuration
    - Model versioning support
    - A/B testing configuration
    - Performance monitoring settings
"""

from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
from functools import lru_cache
from pathlib import Path


class MLSettings(BaseSettings):
    """
    Machine Learning Service Configuration

    Centralized configuration for ML model serving and inference.
    Supports multiple model versions and A/B testing.

    Attributes:
        MODEL_BASE_PATH: Base directory for model storage
        ACTIVE_MODEL_VERSION: Currently active model version
        SUPPORTED_MODELS: List of supported model architectures

    Example:
        >>> settings = get_ml_settings()
        >>> print(settings.MODEL_BASE_PATH)
        '/app/models'
    """

    # Model Storage Configuration
    MODEL_BASE_PATH: str = "/app/models"
    MODEL_REGISTRY_URL: Optional[str] = None  # MLflow or custom registry

    # Active Model Configuration
    ACTIVE_MODEL_VERSION: str = "v1.0.0"
    MODEL_ARCHITECTURE: str = "resnet50"  # resnet50, efficientnet_b0, vit_base
    NUM_CLASSES: int = 31  # Number of fish species

    # Model Serving Configuration
    BATCH_SIZE: int = 32  # Inference batch size
    MAX_BATCH_WAIT_TIME: float = 0.1  # Max wait time for batching (seconds)
    INFERENCE_DEVICE: str = "cuda"  # cuda, cpu, mps
    ENABLE_MIXED_PRECISION: bool = True  # FP16 inference for speed

    # Model Versioning & A/B Testing
    ENABLE_AB_TESTING: bool = False
    AB_TEST_TRAFFIC_SPLIT: Dict[str, float] = {"v1.0.0": 0.9, "v1.1.0": 0.1}
    MODEL_WARMUP_SAMPLES: int = 10  # Samples for model warm-up

    # Input Processing
    IMAGE_SIZE: List[int] = [224, 224]  # Height, Width
    NORMALIZE_MEAN: List[float] = [0.485, 0.456, 0.406]  # ImageNet mean
    NORMALIZE_STD: List[float] = [0.229, 0.224, 0.225]  # ImageNet std
    MAX_IMAGE_SIZE_MB: int = 10  # Maximum upload size

    # Performance Configuration
    NUM_WORKERS: int = 4  # Number of inference workers
    ENABLE_ONNX: bool = False  # Use ONNX Runtime for inference
    ENABLE_TENSORRT: bool = False  # Use TensorRT optimization
    ENABLE_MODEL_COMPILATION: bool = False  # PyTorch 2.0 compile

    # Caching Configuration
    ENABLE_PREDICTION_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 10000  # Max cached predictions

    # Monitoring Configuration
    ENABLE_PERFORMANCE_TRACKING: bool = True
    ENABLE_DRIFT_DETECTION: bool = True
    DRIFT_DETECTION_WINDOW: int = 1000  # Samples for drift detection
    ALERT_THRESHOLD_LATENCY_MS: int = 500  # Alert if latency > 500ms
    ALERT_THRESHOLD_ACCURACY_DROP: float = 0.05  # Alert if accuracy drops 5%

    # Model Metadata
    MODEL_NAME: str = "fish_classifier"
    MODEL_DESCRIPTION: str = "Production fish species classification model"
    SUPPORTED_SPECIES: List[str] = [
        "Bangus",
        "Tilapia",
        "Catfish",
        "Salmon",
        "Grass_Carp",
        "Big_Head_Carp",
        "Silver_Carp",
        "Indian_Carp",
        "Pangasius",
        "Gourami",
        "Snakehead",
        "Climbing_Perch",
        "Janitor_Fish",
        "Knifefish",
        "Freshwater_Eel",
        "Glass_Perchlet",
        "Goby",
        "Tenpounder",
        "Black_Spotted_Barb",
        "Fourfinger_Threadfin",
        "Green_Spotted_Puffer",
        "Indo_Pacific_Tarpon",
        "Jaguar_Gapote",
        "Long_Snouted_Pipefish",
        "Mosquito_Fish",
        "Mudfish",
        "Mullet",
        "Perch",
        "Scat_Fish",
        "Silver_Barb",
        "Silver_Perch",
    ]

    # Confidence Thresholds
    MIN_CONFIDENCE_THRESHOLD: float = 0.5  # Minimum confidence for prediction
    HIGH_CONFIDENCE_THRESHOLD: float = 0.9  # High confidence threshold

    # Logging Configuration
    LOG_PREDICTIONS: bool = True
    LOG_INFERENCE_TIME: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        """Pydantic configuration"""

        env_file = ".env"
        env_prefix = "ML_"  # Environment variables prefixed with ML_
        case_sensitive = True


@lru_cache()
def get_ml_settings() -> MLSettings:
    """
    Get ML Service Settings (Singleton Pattern)

    Returns cached MLSettings instance for performance.

    Returns:
        MLSettings: Validated ML service configuration

    Example:
        >>> from services.ml_service.core.config import get_ml_settings
        >>> settings = get_ml_settings()
        >>> print(settings.MODEL_ARCHITECTURE)
        'resnet50'

    Note:
        Settings are cached and thread-safe.
    """
    return MLSettings()


# Global ML settings instance
ml_settings = get_ml_settings()
