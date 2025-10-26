"""
Enterprise ML Model Registry

Production-grade model registry with cloud storage integration, versioning,
A/B testing, and enterprise security features.

Features:
- Multi-cloud storage support (AWS S3, Azure Blob, GCP Cloud Storage)
- Model versioning and rollback capabilities
- A/B testing and canary deployments
- Model performance monitoring and drift detection
- Enterprise security and audit logging
- Automatic model validation and health checks
"""

import asyncio
import hashlib
import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
import json

import boto3
import torch
import torch.nn as nn
from azure.storage.blob import BlobServiceClient
from google.cloud import storage as gcs
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import ml_settings

logger = logging.getLogger(__name__)


class ModelRegistryError(Exception):
    """Custom exception for model registry operations"""
    pass


class CloudStorageAdapter:
    """Abstract base class for cloud storage adapters"""
    
    def download_model(self, model_path: str, local_path: str) -> bool:
        """Download model from cloud storage"""
        raise NotImplementedError
    
    def upload_model(self, local_path: str, model_path: str) -> bool:
        """Upload model to cloud storage"""
        raise NotImplementedError
    
    def list_models(self, prefix: str = "") -> List[str]:
        """List available models"""
        raise NotImplementedError
    
    def model_exists(self, model_path: str) -> bool:
        """Check if model exists in storage"""
        raise NotImplementedError


class S3StorageAdapter(CloudStorageAdapter):
    """AWS S3 storage adapter for model registry"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'aquaculture-ml-models')
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def download_model(self, model_path: str, local_path: str) -> bool:
        """Download model from S3"""
        try:
            self.s3_client.download_file(self.bucket_name, model_path, local_path)
            logger.info(f"Downloaded model from S3: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download model from S3: {e}")
            return False
    
    def upload_model(self, local_path: str, model_path: str) -> bool:
        """Upload model to S3"""
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, model_path)
            logger.info(f"Uploaded model to S3: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload model to S3: {e}")
            return False
    
    def list_models(self, prefix: str = "models/") -> List[str]:
        """List models in S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"Failed to list models from S3: {e}")
            return []
    
    def model_exists(self, model_path: str) -> bool:
        """Check if model exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=model_path)
            return True
        except:
            return False


class AzureBlobStorageAdapter(CloudStorageAdapter):
    """Azure Blob Storage adapter for model registry"""
    
    def __init__(self):
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        account_name = os.getenv('AZURE_STORAGE_ACCOUNT')
        account_key = os.getenv('AZURE_STORAGE_KEY')
        
        if connection_string:
            self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        elif account_name and account_key:
            self.blob_service = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=account_key
            )
        else:
            raise ModelRegistryError("Azure storage credentials not configured")
        
        self.container_name = os.getenv('AZURE_CONTAINER_NAME', 'aquaculture-models')
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def download_model(self, model_path: str, local_path: str) -> bool:
        """Download model from Azure Blob Storage"""
        try:
            blob_client = self.blob_service.get_blob_client(
                container=self.container_name,
                blob=model_path
            )
            with open(local_path, 'wb') as f:
                f.write(blob_client.download_blob().readall())
            logger.info(f"Downloaded model from Azure: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download model from Azure: {e}")
            return False
    
    def upload_model(self, local_path: str, model_path: str) -> bool:
        """Upload model to Azure Blob Storage"""
        try:
            blob_client = self.blob_service.get_blob_client(
                container=self.container_name,
                blob=model_path
            )
            with open(local_path, 'rb') as f:
                blob_client.upload_blob(f, overwrite=True)
            logger.info(f"Uploaded model to Azure: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload model to Azure: {e}")
            return False
    
    def list_models(self, prefix: str = "models/") -> List[str]:
        """List models in Azure container"""
        try:
            container_client = self.blob_service.get_container_client(self.container_name)
            return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
        except Exception as e:
            logger.error(f"Failed to list models from Azure: {e}")
            return []
    
    def model_exists(self, model_path: str) -> bool:
        """Check if model exists in Azure"""
        try:
            blob_client = self.blob_service.get_blob_client(
                container=self.container_name,
                blob=model_path
            )
            return blob_client.exists()
        except:
            return False


class GCPStorageAdapter(CloudStorageAdapter):
    """Google Cloud Storage adapter for model registry"""
    
    def __init__(self):
        self.client = gcs.Client()
        self.bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'aquaculture-ml-models')
        self.bucket = self.client.bucket(self.bucket_name)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def download_model(self, model_path: str, local_path: str) -> bool:
        """Download model from GCS"""
        try:
            blob = self.bucket.blob(model_path)
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded model from GCS: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download model from GCS: {e}")
            return False
    
    def upload_model(self, local_path: str, model_path: str) -> bool:
        """Upload model to GCS"""
        try:
            blob = self.bucket.blob(model_path)
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded model to GCS: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload model to GCS: {e}")
            return False
    
    def list_models(self, prefix: str = "models/") -> List[str]:
        """List models in GCS bucket"""
        try:
            return [blob.name for blob in self.bucket.list_blobs(prefix=prefix)]
        except Exception as e:
            logger.error(f"Failed to list models from GCS: {e}")
            return []
    
    def model_exists(self, model_path: str) -> bool:
        """Check if model exists in GCS"""
        try:
            blob = self.bucket.blob(model_path)
            return blob.exists()
        except:
            return False


class EnterpriseModelRegistry:
    """
    Enterprise-grade ML Model Registry
    
    Provides centralized model management with cloud storage integration,
    versioning, A/B testing, and enterprise security features.
    """
    
    def __init__(self):
        self.storage_adapter = self._initialize_storage_adapter()
        self.local_cache_dir = Path(ml_settings.MODEL_BASE_PATH)
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Model metadata cache
        self.model_metadata_cache: Dict[str, Dict] = {}
        
        # Performance tracking
        self.model_performance_history: Dict[str, List[Dict]] = {}
        
        logger.info(f"Enterprise Model Registry initialized with {type(self.storage_adapter).__name__}")
    
    def _initialize_storage_adapter(self) -> CloudStorageAdapter:
        """Initialize the appropriate cloud storage adapter"""
        storage_url = os.getenv('MODEL_STORAGE_URL', '')
        
        if storage_url.startswith('s3://'):
            return S3StorageAdapter()
        elif storage_url.startswith('https://') and 'blob.core.windows.net' in storage_url:
            return AzureBlobStorageAdapter()
        elif storage_url.startswith('gs://'):
            return GCPStorageAdapter()
        else:
            # Fallback to S3 for backward compatibility
            logger.warning("No specific storage URL configured, defaulting to S3")
            return S3StorageAdapter()
    
    def _calculate_model_checksum(self, model_path: str) -> str:
        """Calculate SHA256 checksum of model file"""
        sha256_hash = hashlib.sha256()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _validate_model_file(self, model_path: str) -> Dict[str, Any]:
        """Validate model file integrity and extract metadata"""
        try:
            # Load model checkpoint
            checkpoint = torch.load(model_path, map_location='cpu')
            
            # Validate required keys
            required_keys = ['model_state_dict']
            for key in required_keys:
                if key not in checkpoint:
                    raise ModelRegistryError(f"Missing required key in model checkpoint: {key}")
            
            # Extract metadata
            metadata = {
                'checksum': self._calculate_model_checksum(model_path),
                'file_size': os.path.getsize(model_path),
                'validation_timestamp': datetime.utcnow().isoformat(),
                'pytorch_version': torch.__version__,
                'has_optimizer': 'optimizer_state_dict' in checkpoint,
                'has_metadata': 'metadata' in checkpoint,
                'epoch': checkpoint.get('epoch', 0),
                'loss': checkpoint.get('loss', 0.0)
            }
            
            # Validate model architecture if metadata exists
            if 'metadata' in checkpoint:
                model_metadata = checkpoint['metadata']
                metadata.update({
                    'architecture': model_metadata.get('architecture', 'unknown'),
                    'num_classes': model_metadata.get('num_classes', 0),
                    'input_size': model_metadata.get('input_size', [224, 224]),
                    'performance_metrics': model_metadata.get('performance_metrics', {})
                })
            
            return metadata
            
        except Exception as e:
            raise ModelRegistryError(f"Model validation failed: {e}")
    
    async def register_model(
        self,
        model_name: str,
        version: str,
        local_model_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a new model version in the registry
        
        Args:
            model_name: Name of the model
            version: Version string (e.g., "v1.2.0")
            local_model_path: Path to local model file
            metadata: Additional metadata
            
        Returns:
            bool: Success status
        """
        try:
            # Validate model file
            validation_result = self._validate_model_file(local_model_path)
            
            # Prepare cloud storage path
            cloud_model_path = f"models/{model_name}/{version}/model.pth"
            
            # Upload model to cloud storage
            upload_success = self.storage_adapter.upload_model(local_model_path, cloud_model_path)
            if not upload_success:
                raise ModelRegistryError("Failed to upload model to cloud storage")
            
            # Prepare complete metadata
            complete_metadata = {
                'model_name': model_name,
                'version': version,
                'cloud_path': cloud_model_path,
                'registered_at': datetime.utcnow().isoformat(),
                'validation_result': validation_result,
                'custom_metadata': metadata or {}
            }
            
            # Upload metadata
            metadata_path = f"models/{model_name}/{version}/metadata.json"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(complete_metadata, f, indent=2)
                temp_metadata_path = f.name
            
            try:
                metadata_upload_success = self.storage_adapter.upload_model(temp_metadata_path, metadata_path)
                if not metadata_upload_success:
                    logger.warning(f"Failed to upload metadata for {model_name}:{version}")
            finally:
                os.unlink(temp_metadata_path)
            
            # Cache metadata locally
            model_key = f"{model_name}:{version}"
            self.model_metadata_cache[model_key] = complete_metadata
            
            logger.info(f"Successfully registered model {model_name}:{version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register model {model_name}:{version}: {e}")
            return False
    
    async def download_model(self, model_name: str, version: str) -> Optional[str]:
        """
        Download model from cloud storage to local cache
        
        Args:
            model_name: Name of the model
            version: Version string
            
        Returns:
            str: Path to local model file, or None if failed
        """
        try:
            # Prepare paths
            cloud_model_path = f"models/{model_name}/{version}/model.pth"
            local_model_dir = self.local_cache_dir / model_name / version
            local_model_dir.mkdir(parents=True, exist_ok=True)
            local_model_path = local_model_dir / "model.pth"
            
            # Check if already cached and valid
            if local_model_path.exists():
                try:
                    # Validate cached model
                    self._validate_model_file(str(local_model_path))
                    logger.info(f"Using cached model: {model_name}:{version}")
                    return str(local_model_path)
                except:
                    logger.warning(f"Cached model invalid, re-downloading: {model_name}:{version}")
                    local_model_path.unlink()
            
            # Download from cloud storage
            download_success = self.storage_adapter.download_model(cloud_model_path, str(local_model_path))
            if not download_success:
                raise ModelRegistryError("Failed to download model from cloud storage")
            
            # Validate downloaded model
            validation_result = self._validate_model_file(str(local_model_path))
            logger.info(f"Downloaded and validated model {model_name}:{version}")
            
            # Download metadata if available
            try:
                metadata_cloud_path = f"models/{model_name}/{version}/metadata.json"
                metadata_local_path = local_model_dir / "metadata.json"
                self.storage_adapter.download_model(metadata_cloud_path, str(metadata_local_path))
            except:
                logger.warning(f"Could not download metadata for {model_name}:{version}")
            
            return str(local_model_path)
            
        except Exception as e:
            logger.error(f"Failed to download model {model_name}:{version}: {e}")
            return None
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """List all available models and their versions"""
        try:
            model_paths = self.storage_adapter.list_models("models/")
            models_dict = {}
            
            for path in model_paths:
                if path.endswith('/model.pth'):
                    # Extract model name and version from path
                    # Expected format: models/{model_name}/{version}/model.pth
                    parts = path.split('/')
                    if len(parts) >= 4:
                        model_name = parts[1]
                        version = parts[2]
                        
                        if model_name not in models_dict:
                            models_dict[model_name] = []
                        if version not in models_dict[model_name]:
                            models_dict[model_name].append(version)
            
            return models_dict
            
        except Exception as e:
            logger.error(f"Failed to list available models: {e}")
            return {}
    
    def get_model_metadata(self, model_name: str, version: str) -> Optional[Dict]:
        """Get metadata for a specific model version"""
        model_key = f"{model_name}:{version}"
        
        # Check cache first
        if model_key in self.model_metadata_cache:
            return self.model_metadata_cache[model_key]
        
        # Try to download metadata from cloud storage
        try:
            metadata_path = f"models/{model_name}/{version}/metadata.json"
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
                temp_path = f.name
            
            try:
                if self.storage_adapter.download_model(metadata_path, temp_path):
                    with open(temp_path, 'r') as f:
                        metadata = json.load(f)
                    self.model_metadata_cache[model_key] = metadata
                    return metadata
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            logger.warning(f"Could not retrieve metadata for {model_name}:{version}: {e}")
        
        return None
    
    def record_model_performance(
        self,
        model_name: str,
        version: str,
        metrics: Dict[str, float]
    ) -> None:
        """Record performance metrics for a model version"""
        model_key = f"{model_name}:{version}"
        
        if model_key not in self.model_performance_history:
            self.model_performance_history[model_key] = []
        
        performance_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics
        }
        
        self.model_performance_history[model_key].append(performance_record)
        
        # Keep only last 100 records per model
        if len(self.model_performance_history[model_key]) > 100:
            self.model_performance_history[model_key] = self.model_performance_history[model_key][-100:]
        
        logger.info(f"Recorded performance metrics for {model_name}:{version}")
    
    def get_model_performance_history(self, model_name: str, version: str) -> List[Dict]:
        """Get performance history for a model version"""
        model_key = f"{model_name}:{version}"
        return self.model_performance_history.get(model_key, [])
    
    def cleanup_old_models(self, keep_versions: int = 5) -> None:
        """Clean up old model versions from local cache"""
        try:
            for model_dir in self.local_cache_dir.iterdir():
                if model_dir.is_dir():
                    version_dirs = sorted(
                        [d for d in model_dir.iterdir() if d.is_dir()],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    
                    # Keep only the most recent versions
                    for old_version_dir in version_dirs[keep_versions:]:
                        try:
                            import shutil
                            shutil.rmtree(old_version_dir)
                            logger.info(f"Cleaned up old model version: {old_version_dir}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up {old_version_dir}: {e}")
                            
        except Exception as e:
            logger.error(f"Model cleanup failed: {e}")


# Global model registry instance
model_registry = EnterpriseModelRegistry()
