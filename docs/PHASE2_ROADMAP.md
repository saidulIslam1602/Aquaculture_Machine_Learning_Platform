# 🚀 **Phase 2: ML Services & Advanced Operations (Days 29-56)**

## 📋 **Phase 2 Overview**

Building upon the solid foundation from Phase 1, Phase 2 transforms your platform into a **production-grade ML system** with advanced operational capabilities. You'll implement real ML inference, sophisticated monitoring, and enterprise-level automation.

### **What You'll Build in Phase 2:**
- 🤖 **Complete ML Service** with PyTorch model serving
- ⚡ **Worker Service** with Celery and Kafka integration  
- 📊 **Advanced Monitoring** with custom metrics and alerting
- 🔄 **CI/CD Pipeline** with automated testing and deployment
- 🎯 **Performance Optimization** for production workloads
- 🛡️ **Security Hardening** with enterprise practices

---

## 🎯 **Phase 2: ML Services & Workers (Days 29-42)**

### **Day 29: ML Service Foundation**

#### **Step 29.1: Complete ML Service Architecture**

**Learning Objective**: Understand production ML serving patterns and PyTorch deployment strategies.

**File Creation Order:**

1. **`services/ml-service/core/config.py`** - ML-specific configuration
```python
"""
ML Service Configuration

Handles ML-specific settings including model paths, inference parameters,
and performance optimization settings.
"""

from functools import lru_cache
from typing import List, Tuple

from pydantic_settings import BaseSettings


class MLSettings(BaseSettings):
    """
    ML Service Configuration
    
    Centralized configuration for ML inference service.
    Optimized for production deployment with GPU support.
    """
    
    # Service Configuration
    ML_SERVICE_HOST: str = "0.0.0.0"
    ML_SERVICE_PORT: int = 8001
    ML_SERVICE_NAME: str = "aquaculture-ml-service"
    
    # Model Configuration
    MODEL_BASE_PATH: str = "/app/models"
    ACTIVE_MODEL_VERSION: str = "v1.0.0"
    MODEL_ARCHITECTURE: str = "resnet50"  # resnet50, efficientnet_b0, vit_base
    NUM_CLASSES: int = 10  # Number of fish species
    
    # Inference Configuration
    INFERENCE_DEVICE: str = "cpu"  # cpu, cuda, mps
    BATCH_SIZE: int = 32
    MAX_BATCH_SIZE: int = 64
    INFERENCE_TIMEOUT: int = 30  # seconds
    
    # Image Processing
    IMAGE_SIZE: Tuple[int, int] = (224, 224)
    NORMALIZE_MEAN: List[float] = [0.485, 0.456, 0.406]  # ImageNet standards
    NORMALIZE_STD: List[float] = [0.229, 0.224, 0.225]
    
    # Performance Optimization
    ENABLE_MIXED_PRECISION: bool = False  # FP16 for faster inference
    ENABLE_MODEL_COMPILATION: bool = False  # PyTorch 2.0 compilation
    MODEL_WARMUP_SAMPLES: int = 5  # Warmup iterations
    
    # Caching
    PREDICTION_CACHE_TTL: int = 300  # 5 minutes
    MODEL_CACHE_SIZE: int = 3  # Number of models to keep in memory
    
    # Monitoring
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 8002
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_ml_settings() -> MLSettings:
    """Get cached ML settings instance"""
    return MLSettings()


# Global ML settings instance
ml_settings = get_ml_settings()
```

**WHY This ML Configuration?**
- **Device Abstraction**: Supports CPU, CUDA, and Apple Silicon
- **Performance Tuning**: Mixed precision and model compilation options
- **Batch Processing**: Configurable batch sizes for throughput optimization
- **Caching Strategy**: Model and prediction caching for performance

2. **`services/ml-service/models/model_manager.py`** - Enhanced model management
```python
"""
Production Model Manager

Handles model loading, versioning, caching, and lifecycle management
with enterprise-grade features for production deployment.
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image

from ..core.config import ml_settings

logger = logging.getLogger(__name__)


class ModelMetadata:
    """Enhanced model metadata with performance tracking"""
    
    def __init__(
        self,
        version: str,
        architecture: str,
        file_path: str,
        checksum: str,
        num_parameters: int,
        performance_metrics: Optional[Dict[str, float]] = None,
    ):
        self.version = version
        self.architecture = architecture
        self.file_path = file_path
        self.checksum = checksum
        self.num_parameters = num_parameters
        self.performance_metrics = performance_metrics or {}
        self.loaded_at = datetime.utcnow()
        
        # Performance tracking
        self.inference_count = 0
        self.total_inference_time = 0.0
        self.error_count = 0
        self.last_used = datetime.utcnow()
    
    def record_inference(self, duration: float, success: bool = True):
        """Record inference performance metrics"""
        self.inference_count += 1
        self.total_inference_time += duration
        self.last_used = datetime.utcnow()
        
        if not success:
            self.error_count += 1
    
    @property
    def average_inference_time(self) -> float:
        """Calculate average inference time in milliseconds"""
        if self.inference_count == 0:
            return 0.0
        return (self.total_inference_time / self.inference_count) * 1000
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.inference_count == 0:
            return 0.0
        return (self.error_count / self.inference_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for API responses"""
        return {
            "version": self.version,
            "architecture": self.architecture,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "num_parameters": self.num_parameters,
            "performance_metrics": self.performance_metrics,
            "loaded_at": self.loaded_at.isoformat(),
            "inference_count": self.inference_count,
            "avg_inference_time_ms": self.average_inference_time,
            "error_rate_percent": self.error_rate,
            "last_used": self.last_used.isoformat(),
        }


class ModelManager:
    """
    Production Model Manager with Advanced Features
    
    Features:
    - Thread-safe model loading and caching
    - Performance monitoring and metrics
    - Automatic model warm-up
    - Memory management and cleanup
    - Health monitoring
    - A/B testing support
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model manager"""
        if not hasattr(self, "initialized"):
            self.models: Dict[str, nn.Module] = {}
            self.metadata: Dict[str, ModelMetadata] = {}
            self.transforms: Dict[str, transforms.Compose] = {}
            self.device = self._setup_device()
            self.class_names: List[str] = []
            self.initialized = True
            logger.info(f"ModelManager initialized on device: {self.device}")
    
    def _setup_device(self) -> torch.device:
        """Setup optimal inference device"""
        if ml_settings.INFERENCE_DEVICE == "cuda" and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        elif ml_settings.INFERENCE_DEVICE == "mps" and torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("Using Apple Silicon MPS device")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU device")
        
        return device
    
    def _create_transforms(self) -> transforms.Compose:
        """Create image preprocessing transforms"""
        return transforms.Compose([
            transforms.Resize(ml_settings.IMAGE_SIZE),
            transforms.CenterCrop(ml_settings.IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=ml_settings.NORMALIZE_MEAN,
                std=ml_settings.NORMALIZE_STD
            ),
        ])
    
    def _create_model_architecture(self, architecture: str, num_classes: int) -> nn.Module:
        """Create model architecture based on configuration"""
        import torchvision.models as models
        
        if architecture == "resnet50":
            model = models.resnet50(pretrained=False)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
        elif architecture == "resnet101":
            model = models.resnet101(pretrained=False)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
        elif architecture == "efficientnet_b0":
            model = models.efficientnet_b0(pretrained=False)
            model.classifier[1] = nn.Linear(
                model.classifier[1].in_features, num_classes
            )
        elif architecture == "vit_base_patch16_224":
            model = models.vit_b_16(pretrained=False)
            model.heads.head = nn.Linear(model.heads.head.in_features, num_classes)
        else:
            raise ValueError(f"Unsupported architecture: {architecture}")
        
        return model
    
    async def load_model(self, version: str, force_reload: bool = False) -> nn.Module:
        """Load model with async support for non-blocking operations"""
        # Check cache first
        if version in self.models and not force_reload:
            logger.info(f"Using cached model version: {version}")
            return self.models[version]
        
        # Use thread pool for CPU-intensive model loading
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(None, self._load_model_sync, version, force_reload)
        return model
    
    def _load_model_sync(self, version: str, force_reload: bool = False) -> nn.Module:
        """Synchronous model loading implementation"""
        with self._lock:
            # Double-check after acquiring lock
            if version in self.models and not force_reload:
                return self.models[version]
            
            model_path = Path(ml_settings.MODEL_BASE_PATH) / version / "model.pth"
            class_names_path = Path(ml_settings.MODEL_BASE_PATH) / version / "class_names.txt"
            
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")
            
            logger.info(f"Loading model from: {model_path}")
            
            try:
                # Load checkpoint
                checkpoint = torch.load(model_path, map_location=self.device)
                
                # Extract components
                if isinstance(checkpoint, dict):
                    state_dict = checkpoint.get("model_state_dict", checkpoint)
                    performance_metrics = checkpoint.get("metrics", {})
                    class_names = checkpoint.get("class_names", [])
                else:
                    state_dict = checkpoint
                    performance_metrics = {}
                    class_names = []
                
                # Load class names from file if available
                if class_names_path.exists():
                    with open(class_names_path, 'r') as f:
                        class_names = [line.strip() for line in f.readlines()]
                
                # Create model
                model = self._create_model_architecture(
                    ml_settings.MODEL_ARCHITECTURE, 
                    len(class_names) or ml_settings.NUM_CLASSES
                )
                
                # Load weights
                model.load_state_dict(state_dict)
                model.to(self.device)
                model.eval()
                
                # Apply optimizations
                if ml_settings.ENABLE_MIXED_PRECISION:
                    model = model.half()
                    logger.info("Enabled mixed precision (FP16)")
                
                if ml_settings.ENABLE_MODEL_COMPILATION and hasattr(torch, "compile"):
                    model = torch.compile(model)
                    logger.info("Enabled PyTorch 2.0 compilation")
                
                # Create metadata
                checksum = self._calculate_checksum(model_path)
                num_params = sum(p.numel() for p in model.parameters())
                
                metadata = ModelMetadata(
                    version=version,
                    architecture=ml_settings.MODEL_ARCHITECTURE,
                    file_path=str(model_path),
                    checksum=checksum,
                    num_parameters=num_params,
                    performance_metrics=performance_metrics,
                )
                
                # Cache everything
                self.models[version] = model
                self.metadata[version] = metadata
                self.transforms[version] = self._create_transforms()
                if class_names:
                    self.class_names = class_names
                
                # Warm up model
                self._warmup_model(model)
                
                logger.info(f"Model loaded successfully: {version}")
                logger.info(f"Parameters: {num_params:,}")
                logger.info(f"Classes: {len(self.class_names)}")
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model {version}: {e}")
                raise RuntimeError(f"Model loading failed: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of model file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _warmup_model(self, model: nn.Module) -> None:
        """Warm up model with dummy inference"""
        logger.info("Warming up model...")
        model.eval()
        
        with torch.no_grad():
            dummy_input = torch.randn(
                1, 3, *ml_settings.IMAGE_SIZE, device=self.device
            )
            
            if ml_settings.ENABLE_MIXED_PRECISION:
                dummy_input = dummy_input.half()
            
            # Multiple warmup iterations
            start_time = time.time()
            for _ in range(ml_settings.MODEL_WARMUP_SAMPLES):
                _ = model(dummy_input)
            
            warmup_time = time.time() - start_time
            logger.info(f"Model warmup complete: {warmup_time:.2f}s")
    
    async def predict(
        self, 
        image: Image.Image, 
        version: Optional[str] = None,
        return_probabilities: bool = False
    ) -> Dict[str, Any]:
        """
        Perform inference on single image
        
        Args:
            image: PIL Image object
            version: Model version (defaults to active)
            return_probabilities: Return all class probabilities
            
        Returns:
            Dict containing prediction results
        """
        if version is None:
            version = ml_settings.ACTIVE_MODEL_VERSION
        
        # Ensure model is loaded
        model = await self.load_model(version)
        transform = self.transforms[version]
        metadata = self.metadata[version]
        
        start_time = time.time()
        
        try:
            # Preprocess image
            input_tensor = transform(image).unsqueeze(0).to(self.device)
            
            if ml_settings.ENABLE_MIXED_PRECISION:
                input_tensor = input_tensor.half()
            
            # Inference
            with torch.no_grad():
                outputs = model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted_class = torch.max(probabilities, 1)
            
            # Convert to CPU and extract values
            confidence = confidence.item()
            predicted_class = predicted_class.item()
            
            # Get class name
            species_name = (
                self.class_names[predicted_class] 
                if predicted_class < len(self.class_names) 
                else f"class_{predicted_class}"
            )
            
            # Prepare result
            result = {
                "species": species_name,
                "species_id": predicted_class,
                "confidence": confidence,
                "model_version": version,
                "inference_time_ms": (time.time() - start_time) * 1000,
            }
            
            # Add all probabilities if requested
            if return_probabilities:
                all_probs = probabilities.cpu().numpy()[0]
                result["all_probabilities"] = {
                    (self.class_names[i] if i < len(self.class_names) else f"class_{i}"): float(prob)
                    for i, prob in enumerate(all_probs)
                }
            
            # Record performance
            metadata.record_inference(time.time() - start_time, success=True)
            
            return result
            
        except Exception as e:
            # Record error
            metadata.record_inference(time.time() - start_time, success=False)
            logger.error(f"Inference failed: {e}")
            raise
    
    async def predict_batch(
        self, 
        images: List[Image.Image], 
        version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform batch inference on multiple images
        
        Args:
            images: List of PIL Image objects
            version: Model version (defaults to active)
            
        Returns:
            List of prediction results
        """
        if version is None:
            version = ml_settings.ACTIVE_MODEL_VERSION
        
        # Ensure model is loaded
        model = await self.load_model(version)
        transform = self.transforms[version]
        metadata = self.metadata[version]
        
        start_time = time.time()
        
        try:
            # Preprocess all images
            batch_tensor = torch.stack([
                transform(image) for image in images
            ]).to(self.device)
            
            if ml_settings.ENABLE_MIXED_PRECISION:
                batch_tensor = batch_tensor.half()
            
            # Batch inference
            with torch.no_grad():
                outputs = model(batch_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidences, predicted_classes = torch.max(probabilities, 1)
            
            # Convert to CPU
            confidences = confidences.cpu().numpy()
            predicted_classes = predicted_classes.cpu().numpy()
            
            # Prepare results
            results = []
            for i, (confidence, predicted_class) in enumerate(zip(confidences, predicted_classes)):
                species_name = (
                    self.class_names[predicted_class] 
                    if predicted_class < len(self.class_names) 
                    else f"class_{predicted_class}"
                )
                
                results.append({
                    "species": species_name,
                    "species_id": int(predicted_class),
                    "confidence": float(confidence),
                    "model_version": version,
                    "batch_index": i,
                })
            
            # Record batch performance
            batch_time = time.time() - start_time
            avg_time_per_image = batch_time / len(images)
            
            for _ in images:
                metadata.record_inference(avg_time_per_image, success=True)
            
            return results
            
        except Exception as e:
            # Record errors for all images
            batch_time = time.time() - start_time
            avg_time_per_image = batch_time / len(images)
            
            for _ in images:
                metadata.record_inference(avg_time_per_image, success=False)
            
            logger.error(f"Batch inference failed: {e}")
            raise
    
    def get_model_info(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive model information"""
        if version is None:
            version = ml_settings.ACTIVE_MODEL_VERSION
        
        if version not in self.metadata:
            raise ValueError(f"Model version {version} not loaded")
        
        metadata = self.metadata[version]
        
        return {
            **metadata.to_dict(),
            "class_names": self.class_names,
            "device": str(self.device),
            "image_size": ml_settings.IMAGE_SIZE,
            "batch_size": ml_settings.BATCH_SIZE,
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        status = {
            "healthy": True,
            "device": str(self.device),
            "loaded_models": list(self.models.keys()),
            "active_version": ml_settings.ACTIVE_MODEL_VERSION,
            "total_models": len(self.models),
            "class_count": len(self.class_names),
        }
        
        # Add device-specific info
        if torch.cuda.is_available():
            status["cuda_available"] = True
            status["cuda_memory_allocated_gb"] = torch.cuda.memory_allocated() / 1e9
            status["cuda_memory_reserved_gb"] = torch.cuda.memory_reserved() / 1e9
        
        # Add performance summary
        if self.metadata:
            total_inferences = sum(m.inference_count for m in self.metadata.values())
            avg_inference_time = sum(
                m.average_inference_time * m.inference_count 
                for m in self.metadata.values()
            ) / max(total_inferences, 1)
            
            status["performance"] = {
                "total_inferences": total_inferences,
                "avg_inference_time_ms": avg_inference_time,
            }
        
        return status


# Global model manager instance
model_manager = ModelManager()
```

**WHY This Advanced Model Manager?**
- **Production Features**: Performance tracking, error handling, health monitoring
- **Async Support**: Non-blocking model loading and inference
- **Batch Processing**: Optimized for high throughput scenarios
- **Memory Management**: Efficient caching and cleanup
- **Device Optimization**: Supports CPU, CUDA, and Apple Silicon

#### **Step 29.2: ML Service API Endpoints**

3. **`services/ml-service/main.py`** - ML service FastAPI application
```python
"""
ML Service Main Application

Production-grade ML inference service with comprehensive monitoring,
error handling, and performance optimization.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

from .core.config import ml_settings
from .models.model_manager import model_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info(f"Starting {ml_settings.ML_SERVICE_NAME}")
    
    # Pre-load active model
    try:
        await model_manager.load_model(ml_settings.ACTIVE_MODEL_VERSION)
        logger.info("Active model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load active model: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ML service")


# Create FastAPI application
app = FastAPI(
    title="Aquaculture ML Service",
    description="Production ML inference service for fish classification",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": ml_settings.ML_SERVICE_NAME,
        "version": "1.0.0",
        "device": str(model_manager.device),
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with model status"""
    try:
        health_status = model_manager.get_health_status()
        return {
            "status": "healthy",
            "service": ml_settings.ML_SERVICE_NAME,
            "timestamp": time.time(),
            **health_status,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/predict")
async def predict_single(file: UploadFile = File(...)):
    """
    Single image prediction endpoint
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        
    Returns:
        Prediction result with species and confidence
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read and process image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Validate image size
        if image.size[0] < 32 or image.size[1] < 32:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image too small (minimum 32x32 pixels)"
            )
        
        # Perform inference
        result = await model_manager.predict(image, return_probabilities=False)
        
        return {
            "success": True,
            "prediction": result,
            "timestamp": time.time(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed"
        )


@app.post("/predict/batch")
async def predict_batch(files: List[UploadFile] = File(...)):
    """
    Batch image prediction endpoint
    
    Args:
        files: List of image files
        
    Returns:
        List of prediction results
    """
    try:
        # Validate batch size
        if len(files) > ml_settings.MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size too large (max {ml_settings.MAX_BATCH_SIZE})"
            )
        
        # Process all images
        images = []
        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is not an image"
                )
            
            image_bytes = await file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            images.append(image)
        
        # Perform batch inference
        results = await model_manager.predict_batch(images)
        
        return {
            "success": True,
            "predictions": results,
            "batch_size": len(results),
            "timestamp": time.time(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch prediction failed"
        )


@app.get("/models")
async def list_models():
    """List available models"""
    try:
        # In a real implementation, scan model directory
        return {
            "models": [ml_settings.ACTIVE_MODEL_VERSION],
            "active_model": ml_settings.ACTIVE_MODEL_VERSION,
        }
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models"
        )


@app.get("/models/{version}")
async def get_model_info(version: str):
    """Get detailed model information"""
    try:
        info = model_manager.get_model_info(version)
        return {
            "success": True,
            "model_info": info,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model information"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=ml_settings.ML_SERVICE_HOST,
        port=ml_settings.ML_SERVICE_PORT,
        reload=False,  # Disable in production
    )
```

**WHY This ML Service Design?**
- **Async Operations**: Non-blocking file processing and inference
- **Batch Support**: Optimized for high-throughput scenarios
- **Error Handling**: Comprehensive validation and error responses
- **Health Monitoring**: Detailed health checks for orchestration

---

### **Day 30: Worker Service Implementation**

#### **Step 30.1: Celery Worker Setup**

**Learning Objective**: Understand distributed task processing and message queue integration.

**File Creation Order:**

1. **`services/worker/celery_app.py`** - Celery application configuration
```python
"""
Celery Application Configuration

Production-grade Celery setup with Redis broker, monitoring,
and comprehensive task management.
"""

import logging
import os
from celery import Celery
from celery.signals import setup_logging

# Configure logging
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    })


# Create Celery application
celery_app = Celery(
    "aquaculture_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "services.worker.tasks.ml_tasks",
        "services.worker.tasks.data_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "services.worker.tasks.ml_tasks.*": {"queue": "ml_queue"},
        "services.worker.tasks.data_tasks.*": {"queue": "data_queue"},
    },
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task results
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup_old_predictions": {
            "task": "services.worker.tasks.data_tasks.cleanup_old_predictions",
            "schedule": 3600.0,  # Every hour
        },
        "model_health_check": {
            "task": "services.worker.tasks.ml_tasks.model_health_check",
            "schedule": 300.0,   # Every 5 minutes
        },
    },
)

logger = logging.getLogger(__name__)
logger.info("Celery application configured")
```

2. **`services/worker/tasks/ml_tasks.py`** - ML-specific tasks
```python
"""
ML Tasks for Celery Workers

Handles ML inference, model management, and related background tasks.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from celery import current_task
from PIL import Image
import io
import base64

from ..celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ml_tasks.predict_image")
def predict_image(
    self, 
    image_base64: str, 
    model_version: Optional[str] = None,
    return_probabilities: bool = False
) -> Dict[str, Any]:
    """
    Asynchronous image prediction task
    
    Args:
        image_base64: Base64 encoded image data
        model_version: Model version to use
        return_probabilities: Return all class probabilities
        
    Returns:
        Prediction result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={"status": "Loading image and model"}
        )
        
        # Decode image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Import model manager (lazy import to avoid startup issues)
        from services.ml_service.models.model_manager import model_manager
        
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={"status": "Running inference"}
        )
        
        # Run async prediction in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                model_manager.predict(
                    image, 
                    version=model_version,
                    return_probabilities=return_probabilities
                )
            )
        finally:
            loop.close()
        
        # Add task metadata
        result.update({
            "task_id": self.request.id,
            "processed_at": time.time(),
            "worker_id": self.request.hostname,
        })
        
        logger.info(f"Prediction completed: {result['species']} ({result['confidence']:.2%})")
        
        return {
            "status": "SUCCESS",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Prediction task failed: {e}")
        
        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": type(e).__name__,
            }
        )
        
        raise


@celery_app.task(bind=True, name="ml_tasks.predict_batch")
def predict_batch(
    self, 
    images_base64: List[str], 
    model_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Asynchronous batch prediction task
    
    Args:
        images_base64: List of base64 encoded images
        model_version: Model version to use
        
    Returns:
        Batch prediction results
    """
    try:
        batch_size = len(images_base64)
        
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "status": f"Processing batch of {batch_size} images",
                "progress": 0,
                "total": batch_size,
            }
        )
        
        # Decode all images
        images = []
        for i, image_b64 in enumerate(images_base64):
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            images.append(image)
            
            # Update progress
            self.update_state(
                state="PROCESSING",
                meta={
                    "status": f"Loaded image {i+1}/{batch_size}",
                    "progress": i + 1,
                    "total": batch_size,
                }
            )
        
        # Import model manager
        from services.ml_service.models.model_manager import model_manager
        
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "status": "Running batch inference",
                "progress": batch_size,
                "total": batch_size,
            }
        )
        
        # Run async batch prediction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                model_manager.predict_batch(images, version=model_version)
            )
        finally:
            loop.close()
        
        # Add task metadata to each result
        for result in results:
            result.update({
                "task_id": self.request.id,
                "processed_at": time.time(),
                "worker_id": self.request.hostname,
            })
        
        logger.info(f"Batch prediction completed: {len(results)} images processed")
        
        return {
            "status": "SUCCESS",
            "results": results,
            "batch_size": len(results),
        }
        
    except Exception as e:
        logger.error(f"Batch prediction task failed: {e}")
        
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": type(e).__name__,
                "batch_size": len(images_base64),
            }
        )
        
        raise


@celery_app.task(name="ml_tasks.model_health_check")
def model_health_check() -> Dict[str, Any]:
    """
    Periodic model health check task
    
    Returns:
        Model health status
    """
    try:
        from services.ml_service.models.model_manager import model_manager
        
        health_status = model_manager.get_health_status()
        
        # Log health metrics
        logger.info(f"Model health check: {health_status}")
        
        # You could send metrics to monitoring system here
        # send_metrics_to_prometheus(health_status)
        
        return {
            "status": "SUCCESS",
            "health": health_status,
            "timestamp": time.time(),
        }
        
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return {
            "status": "FAILURE",
            "error": str(e),
            "timestamp": time.time(),
        }


@celery_app.task(name="ml_tasks.preload_model")
def preload_model(model_version: str) -> Dict[str, Any]:
    """
    Preload model for faster inference
    
    Args:
        model_version: Version of model to preload
        
    Returns:
        Preload result
    """
    try:
        from services.ml_service.models.model_manager import model_manager
        
        # Run async model loading
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(model_manager.load_model(model_version))
        finally:
            loop.close()
        
        logger.info(f"Model {model_version} preloaded successfully")
        
        return {
            "status": "SUCCESS",
            "model_version": model_version,
            "timestamp": time.time(),
        }
        
    except Exception as e:
        logger.error(f"Model preload failed: {e}")
        return {
            "status": "FAILURE",
            "error": str(e),
            "model_version": model_version,
            "timestamp": time.time(),
        }
```

**WHY This Celery Design?**
- **Task Routing**: Different queues for different task types
- **Progress Tracking**: Real-time task progress updates
- **Error Handling**: Comprehensive error capture and reporting
- **Health Monitoring**: Periodic health checks and metrics

#### **Step 30.2: Kafka Consumer Integration**

3. **`services/worker/consumers/kafka_consumer.py`** - Kafka message processing
```python
"""
Kafka Consumer for Real-time Data Processing

Handles real-time data streams from IoT sensors, cameras,
and other data sources in the aquaculture system.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from ..celery_app import celery_app

logger = logging.getLogger(__name__)


class AquacultureKafkaConsumer:
    """
    Production Kafka Consumer for Aquaculture Data
    
    Handles multiple data streams:
    - Sensor data (temperature, pH, oxygen)
    - Camera feeds (fish detection events)
    - System events (alerts, notifications)
    - User actions (predictions, configurations)
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "aquaculture-workers",
        topics: Optional[List[str]] = None,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics or [
            "sensor-data",
            "camera-events", 
            "system-events",
            "prediction-requests",
        ]
        
        self.consumer = None
        self.producer = None
        self.running = False
    
    def connect(self):
        """Initialize Kafka consumer and producer"""
        try:
            # Configure consumer
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            
            # Configure producer for responses
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                retries=3,
                acks='all',
            )
            
            logger.info(f"Connected to Kafka: {self.bootstrap_servers}")
            logger.info(f"Subscribed to topics: {self.topics}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        if not self.consumer:
            self.connect()
        
        self.running = True
        logger.info("Starting Kafka message consumption...")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    self.process_message(message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue processing other messages
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming and cleanup resources"""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
        
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
    
    def process_message(self, message):
        """
        Process incoming Kafka message based on topic
        
        Args:
            message: Kafka message object
        """
        topic = message.topic
        data = message.value
        timestamp = datetime.fromtimestamp(message.timestamp / 1000)
        
        logger.info(f"Processing message from {topic}: {data}")
        
        try:
            if topic == "sensor-data":
                self.handle_sensor_data(data, timestamp)
            elif topic == "camera-events":
                self.handle_camera_event(data, timestamp)
            elif topic == "system-events":
                self.handle_system_event(data, timestamp)
            elif topic == "prediction-requests":
                self.handle_prediction_request(data, timestamp)
            else:
                logger.warning(f"Unknown topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error handling {topic} message: {e}")
            # Send to dead letter queue or error topic
            self.send_error_message(topic, data, str(e))
    
    def handle_sensor_data(self, data: Dict[str, Any], timestamp: datetime):
        """
        Handle IoT sensor data
        
        Expected data format:
        {
            "sensor_id": "temp_001",
            "sensor_type": "temperature",
            "value": 23.5,
            "unit": "celsius",
            "tank_id": "tank_001",
            "location": {"x": 10, "y": 20}
        }
        """
        sensor_id = data.get("sensor_id")
        sensor_type = data.get("sensor_type")
        value = data.get("value")
        tank_id = data.get("tank_id")
        
        # Validate data
        if not all([sensor_id, sensor_type, value is not None, tank_id]):
            raise ValueError("Missing required sensor data fields")
        
        # Check for anomalies
        anomaly_detected = self.detect_sensor_anomaly(sensor_type, value)
        
        if anomaly_detected:
            # Trigger alert task
            celery_app.send_task(
                "data_tasks.process_sensor_alert",
                args=[data, timestamp.isoformat()],
                queue="data_queue"
            )
        
        # Store sensor data (trigger background task)
        celery_app.send_task(
            "data_tasks.store_sensor_data",
            args=[data, timestamp.isoformat()],
            queue="data_queue"
        )
        
        logger.info(f"Processed sensor data: {sensor_id} = {value}")
    
    def handle_camera_event(self, data: Dict[str, Any], timestamp: datetime):
        """
        Handle camera detection events
        
        Expected data format:
        {
            "camera_id": "cam_001",
            "event_type": "fish_detected",
            "image_url": "s3://bucket/image.jpg",
            "bounding_boxes": [...],
            "confidence": 0.95,
            "tank_id": "tank_001"
        }
        """
        camera_id = data.get("camera_id")
        event_type = data.get("event_type")
        image_url = data.get("image_url")
        
        if event_type == "fish_detected" and image_url:
            # Trigger ML prediction task
            celery_app.send_task(
                "ml_tasks.process_camera_detection",
                args=[data, timestamp.isoformat()],
                queue="ml_queue"
            )
        
        logger.info(f"Processed camera event: {camera_id} - {event_type}")
    
    def handle_system_event(self, data: Dict[str, Any], timestamp: datetime):
        """
        Handle system events (alerts, notifications, etc.)
        
        Expected data format:
        {
            "event_type": "alert",
            "severity": "high",
            "message": "High mortality rate detected",
            "source": "monitoring_system",
            "metadata": {...}
        }
        """
        event_type = data.get("event_type")
        severity = data.get("severity")
        
        if event_type == "alert" and severity in ["high", "critical"]:
            # Trigger immediate notification
            celery_app.send_task(
                "data_tasks.send_alert_notification",
                args=[data, timestamp.isoformat()],
                queue="data_queue",
                priority=9  # High priority
            )
        
        logger.info(f"Processed system event: {event_type} - {severity}")
    
    def handle_prediction_request(self, data: Dict[str, Any], timestamp: datetime):
        """
        Handle async prediction requests from API
        
        Expected data format:
        {
            "request_id": "req_123",
            "user_id": "user_456",
            "image_base64": "...",
            "model_version": "v1.0.0",
            "callback_url": "https://api/callback"
        }
        """
        request_id = data.get("request_id")
        image_base64 = data.get("image_base64")
        callback_url = data.get("callback_url")
        
        if request_id and image_base64:
            # Trigger ML prediction task
            task = celery_app.send_task(
                "ml_tasks.predict_image",
                args=[image_base64, data.get("model_version")],
                queue="ml_queue"
            )
            
            # Store task mapping for callback
            celery_app.send_task(
                "data_tasks.store_prediction_task",
                args=[request_id, task.id, callback_url],
                queue="data_queue"
            )
        
        logger.info(f"Processed prediction request: {request_id}")
    
    def detect_sensor_anomaly(self, sensor_type: str, value: float) -> bool:
        """
        Simple anomaly detection for sensor values
        
        Args:
            sensor_type: Type of sensor
            value: Sensor reading
            
        Returns:
            True if anomaly detected
        """
        # Define normal ranges for different sensors
        normal_ranges = {
            "temperature": (18.0, 28.0),  # Celsius
            "ph": (6.5, 8.5),
            "oxygen": (5.0, 15.0),        # mg/L
            "salinity": (0.0, 35.0),      # ppt
        }
        
        if sensor_type in normal_ranges:
            min_val, max_val = normal_ranges[sensor_type]
            return not (min_val <= value <= max_val)
        
        return False
    
    def send_error_message(self, topic: str, data: Dict[str, Any], error: str):
        """Send failed message to error topic"""
        if self.producer:
            error_message = {
                "original_topic": topic,
                "original_data": data,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            try:
                self.producer.send("error-messages", value=error_message)
                self.producer.flush()
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")


# Global consumer instance
kafka_consumer = AquacultureKafkaConsumer()


@celery_app.task(name="kafka_tasks.start_consumer")
def start_kafka_consumer():
    """Celery task to start Kafka consumer"""
    try:
        kafka_consumer.start_consuming()
    except Exception as e:
        logger.error(f"Kafka consumer task failed: {e}")
        raise


# CLI command to start consumer
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        kafka_consumer.start_consuming()
    else:
        print("Usage: python kafka_consumer.py start")
```

**WHY This Kafka Design?**
- **Multi-topic Support**: Handles different data streams
- **Error Handling**: Dead letter queue for failed messages
- **Anomaly Detection**: Real-time sensor monitoring
- **Task Integration**: Seamless Celery task triggering

---

### **Day 31: Advanced Monitoring & Alerting**

#### **Step 31.1: Custom Metrics and Business KPIs**

**Learning Objective**: Implement comprehensive monitoring with custom metrics for business intelligence.

**File Creation Order:**

1. **`services/api/utils/metrics.py`** - Enhanced metrics collection
```python
"""
Advanced Metrics Collection

Implements comprehensive metrics collection for business KPIs,
performance monitoring, and operational insights.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client.core import REGISTRY

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Advanced Performance Metrics Collector
    
    Tracks detailed performance metrics, business KPIs,
    and operational statistics for monitoring and alerting.
    """
    
    def __init__(self):
        # API Performance Metrics
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status']
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.api_active_requests = Gauge(
            'api_active_requests',
            'Currently active API requests'
        )
        
        # ML Performance Metrics
        self.ml_predictions_total = Counter(
            'ml_predictions_total',
            'Total ML predictions',
            ['model_type', 'model_version', 'status']
        )
        
        self.ml_prediction_duration = Histogram(
            'ml_prediction_duration_seconds',
            'ML prediction duration',
            ['model_type', 'model_version'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.ml_model_accuracy = Gauge(
            'ml_model_accuracy',
            'ML model accuracy score',
            ['model_type', 'model_version']
        )
        
        self.ml_model_drift_score = Gauge(
            'ml_model_drift_score',
            'ML model drift detection score',
            ['model_type', 'model_version']
        )
        
        # Business KPI Metrics
        self.business_fish_mortality_rate = Gauge(
            'business_fish_mortality_rate',
            'Fish mortality rate',
            ['tank_id', 'species']
        )
        
        self.business_feed_conversion_ratio = Gauge(
            'business_feed_conversion_ratio',
            'Feed conversion ratio',
            ['tank_id', 'species']
        )
        
        self.business_water_quality_score = Gauge(
            'business_water_quality_score',
            'Water quality score (0-1)',
            ['tank_id', 'parameter']
        )
        
        self.business_daily_production_kg = Gauge(
            'business_daily_production_kg',
            'Daily production in kilograms',
            ['tank_id', 'species']
        )
        
        self.business_system_uptime_percentage = Gauge(
            'business_system_uptime_percentage',
            'System uptime percentage'
        )
        
        # Infrastructure Metrics
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Active database connections'
        )
        
        self.database_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query duration',
            ['query_type'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'status']
        )
        
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate percentage'
        )
        
        # Security Metrics
        self.security_login_attempts_total = Counter(
            'security_login_attempts_total',
            'Total login attempts',
            ['status', 'user_type']
        )
        
        self.security_suspicious_activity_total = Counter(
            'security_suspicious_activity_total',
            'Suspicious security activities',
            ['activity_type', 'severity']
        )
        
        # Worker Metrics
        self.worker_tasks_total = Counter(
            'worker_tasks_total',
            'Total worker tasks',
            ['task_type', 'status', 'queue']
        )
        
        self.worker_task_duration = Histogram(
            'worker_task_duration_seconds',
            'Worker task duration',
            ['task_type', 'queue'],
            buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
        )
        
        self.worker_queue_size = Gauge(
            'worker_queue_size',
            'Worker queue size',
            ['queue']
        )
        
        # Data Quality Metrics
        self.data_quality_score = Gauge(
            'data_quality_score',
            'Data quality score (0-1)',
            ['data_source', 'stage']
        )
        
        self.feature_missing_rate = Gauge(
            'feature_missing_rate',
            'Feature missing rate',
            ['feature_name', 'data_source']
        )
        
        # In-memory performance tracking
        self._request_times = deque(maxlen=1000)
        self._error_counts = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_api_request(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int, 
        duration: float
    ):
        """Record API request metrics"""
        # Prometheus metrics
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # In-memory tracking
        with self._lock:
            self._request_times.append({
                'timestamp': time.time(),
                'duration': duration,
                'status': status_code,
            })
    
    def record_ml_prediction(
        self,
        model_type: str,
        model_version: str,
        duration: float,
        success: bool = True,
        accuracy: Optional[float] = None
    ):
        """Record ML prediction metrics"""
        status = "success" if success else "failure"
        
        self.ml_predictions_total.labels(
            model_type=model_type,
            model_version=model_version,
            status=status
        ).inc()
        
        if success:
            self.ml_prediction_duration.labels(
                model_type=model_type,
                model_version=model_version
            ).observe(duration)
        
        if accuracy is not None:
            self.ml_model_accuracy.labels(
                model_type=model_type,
                model_version=model_version
            ).set(accuracy)
    
    def record_business_metric(
        self,
        metric_name: str,
        value: float,
        labels: Dict[str, str]
    ):
        """Record business KPI metrics"""
        if metric_name == "mortality_rate":
            self.business_fish_mortality_rate.labels(**labels).set(value)
        elif metric_name == "feed_conversion_ratio":
            self.business_feed_conversion_ratio.labels(**labels).set(value)
        elif metric_name == "water_quality_score":
            self.business_water_quality_score.labels(**labels).set(value)
        elif metric_name == "daily_production_kg":
            self.business_daily_production_kg.labels(**labels).set(value)
        elif metric_name == "system_uptime_percentage":
            self.business_system_uptime_percentage.set(value)
    
    def record_database_query(self, query_type: str, duration: float):
        """Record database query metrics"""
        self.database_query_duration.labels(query_type=query_type).observe(duration)
    
    def record_cache_operation(self, operation: str, success: bool):
        """Record cache operation metrics"""
        status = "hit" if success and operation == "get" else "miss" if operation == "get" else "success" if success else "failure"
        self.cache_operations_total.labels(operation=operation, status=status).inc()
    
    def record_security_event(self, event_type: str, severity: str = "low"):
        """Record security events"""
        if event_type == "login_attempt":
            self.security_login_attempts_total.labels(status="success", user_type="regular").inc()
        elif event_type == "login_failure":
            self.security_login_attempts_total.labels(status="failure", user_type="regular").inc()
        else:
            self.security_suspicious_activity_total.labels(
                activity_type=event_type,
                severity=severity
            ).inc()
    
    def record_worker_task(
        self,
        task_type: str,
        queue: str,
        duration: float,
        success: bool = True
    ):
        """Record worker task metrics"""
        status = "success" if success else "failure"
        
        self.worker_tasks_total.labels(
            task_type=task_type,
            status=status,
            queue=queue
        ).inc()
        
        if success:
            self.worker_task_duration.labels(
                task_type=task_type,
                queue=queue
            ).observe(duration)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get real-time performance summary"""
        with self._lock:
            recent_requests = [
                req for req in self._request_times 
                if time.time() - req['timestamp'] < 300  # Last 5 minutes
            ]
        
        if not recent_requests:
            return {
                "latency_mean_ms": 0,
                "latency_p50_ms": 0,
                "latency_p95_ms": 0,
                "latency_p99_ms": 0,
                "throughput_rps": 0,
                "error_rate": 0,
                "total_requests": 0,
                "uptime_seconds": 0,
            }
        
        # Calculate percentiles
        durations = sorted([req['duration'] * 1000 for req in recent_requests])
        n = len(durations)
        
        p50_idx = int(0.5 * n)
        p95_idx = int(0.95 * n)
        p99_idx = int(0.99 * n)
        
        # Calculate error rate
        error_count = sum(1 for req in recent_requests if req['status'] >= 400)
        error_rate = error_count / len(recent_requests) if recent_requests else 0
        
        # Calculate throughput (requests per second)
        time_span = max(req['timestamp'] for req in recent_requests) - min(req['timestamp'] for req in recent_requests)
        throughput = len(recent_requests) / max(time_span, 1)
        
        return {
            "latency_mean_ms": sum(durations) / n,
            "latency_p50_ms": durations[p50_idx] if p50_idx < n else 0,
            "latency_p95_ms": durations[p95_idx] if p95_idx < n else 0,
            "latency_p99_ms": durations[p99_idx] if p99_idx < n else 0,
            "throughput_rps": throughput,
            "error_rate": error_rate,
            "total_requests": len(recent_requests),
            "uptime_seconds": time.time() - min(req['timestamp'] for req in recent_requests),
        }


# Global metrics instance
performance_metrics = PerformanceMetrics()


def get_business_metrics_endpoint():
    """
    Custom metrics endpoint for Prometheus scraping
    
    Returns business-specific metrics in Prometheus format
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    # Update dynamic metrics
    performance_summary = performance_metrics.get_performance_summary()
    
    # Set current performance metrics
    if hasattr(performance_metrics, '_performance_gauge'):
        for key, value in performance_summary.items():
            performance_metrics._performance_gauge.labels(metric=key).set(value)
    
    return generate_latest(REGISTRY)
```

**WHY This Advanced Metrics Design?**
- **Comprehensive Coverage**: API, ML, business, infrastructure, security metrics
- **Real-time Calculation**: Live percentiles and performance summaries
- **Business Intelligence**: KPIs for operational decision making
- **Prometheus Integration**: Standard metrics format for monitoring

---

This is just the beginning of Phase 2! I'll continue with the remaining days covering:

- **Days 32-35**: CI/CD Pipeline, Testing, and Quality Assurance
- **Days 36-39**: Performance Optimization and Scaling
- **Days 40-42**: Security Hardening and Compliance

Would you like me to continue with the next section of Phase 2, or would you prefer to focus on a specific area first?

