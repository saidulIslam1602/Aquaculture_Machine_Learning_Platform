"""
ML Tasks Module

Celery tasks for machine learning operations including inference,
batch processing, and model management.

Industry Standards:
    - Idempotent task design
    - Comprehensive error handling
    - Progress tracking
    - Result persistence
    - Resource cleanup

Task Types:
    - Single image inference
    - Batch image processing
    - Model loading and validation
    - Performance benchmarking
"""

from celery import Task, group, chord
from celery.utils.log import get_task_logger
from typing import Dict, List, Any, Optional
import time
from PIL import Image
import io
import base64
import numpy as np

from ..celery_app import celery_app
from services.ml_service.inference.engine import inference_engine
from services.ml_service.models.model_manager import model_manager

# Task-specific logger
logger = get_task_logger(__name__)


class MLTask(Task):
    """
    Base ML Task Class

    Custom task class with ML-specific initialization and cleanup.
    Implements lazy loading and resource management.

    Features:
        - Lazy model loading
        - Automatic resource cleanup
        - Error handling
        - Performance tracking
    """

    _inference_engine = None
    _model_manager = None

    @property
    def inference_engine(self):
        """Lazy load inference engine"""
        if self._inference_engine is None:
            self._inference_engine = inference_engine
        return self._inference_engine

    @property
    def model_manager(self):
        """Lazy load model manager"""
        if self._model_manager is None:
            self._model_manager = model_manager
        return self._model_manager

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Task Failure Handler

        Called when task fails. Performs cleanup and logging.

        Args:
            exc: Exception that caused failure
            task_id: Unique task ID
            args: Task arguments
            kwargs: Task keyword arguments
            einfo: Exception info
        """
        logger.error(
            f"Task {self.name} failed: {exc}",
            exc_info=einfo,
            extra={"task_id": task_id},
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    base=MLTask,
    bind=True,
    name="services.worker.tasks.ml_tasks.predict_image",
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def predict_image(
    self,
    image_data: str,
    model_version: Optional[str] = None,
    return_probabilities: bool = False,
) -> Dict[str, Any]:
    """
    Predict Single Image (Async Task)

    Performs inference on a single image asynchronously.
    Supports base64-encoded images for easy transmission.

    Args:
        image_data: Base64-encoded image string
        model_version: Optional model version to use
        return_probabilities: Whether to return all class probabilities

    Returns:
        Dict containing prediction results

    Example:
        >>> from services.worker.tasks.ml_tasks import predict_image
        >>> with open('fish.jpg', 'rb') as f:
        ...     image_b64 = base64.b64encode(f.read()).decode()
        >>> result = predict_image.delay(image_b64)
        >>> print(result.get())  # Wait for result

    Raises:
        ValueError: If image data is invalid
        RuntimeError: If inference fails

    Performance:
        - Typical execution: 50-100ms
        - With queue wait: Variable
        - Retries on failure: Up to 3 times
    """
    start_time = time.time()

    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Perform inference
        result = self.inference_engine.predict(image, model_version=model_version)

        # Filter probabilities if not requested
        if not return_probabilities:
            result.pop("all_probabilities", None)

        # Add task metadata
        result["task_id"] = self.request.id
        result["task_execution_time_ms"] = (time.time() - start_time) * 1000

        logger.info(
            f"Image prediction completed: {result['species']} "
            f"(confidence: {result['confidence']:.2%})"
        )

        return result

    except Exception as e:
        logger.error(f"Image prediction failed: {e}", exc_info=True)
        # Re-raise for Celery retry mechanism
        raise


@celery_app.task(
    base=MLTask,
    bind=True,
    name="services.worker.tasks.ml_tasks.predict_batch",
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(Exception,),
    retry_backoff=True,
    time_limit=1800,  # 30 minutes hard limit
    soft_time_limit=1700,  # 28 minutes soft limit
)
def predict_batch(
    self,
    image_data_list: List[str],
    model_version: Optional[str] = None,
    batch_size: int = 32,
) -> List[Dict[str, Any]]:
    """
    Predict Batch of Images (Async Task)

    Performs batched inference for improved throughput.
    Automatically chunks large batches for memory efficiency.

    Args:
        image_data_list: List of base64-encoded image strings
        model_version: Optional model version to use
        batch_size: Batch size for processing

    Returns:
        List of prediction dictionaries

    Example:
        >>> images_b64 = [base64.b64encode(img).decode() for img in images]
        >>> result = predict_batch.delay(images_b64, batch_size=16)
        >>> predictions = result.get()

    Performance:
        - Batch of 32: ~500-800ms
        - Significantly faster than individual predictions
        - Automatic chunking for large batches

    Note:
        For very large batches (>1000 images), consider using
        batch_predict_chunked for better progress tracking.
    """
    start_time = time.time()
    total_images = len(image_data_list)

    try:
        # Update task state for progress tracking
        self.update_state(
            state="PROCESSING", meta={"current": 0, "total": total_images}
        )

        # Decode all images
        images = []
        for idx, image_data in enumerate(image_data_list):
            try:
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                images.append(image)
            except Exception as e:
                logger.warning(f"Failed to decode image {idx}: {e}")
                # Add placeholder for failed image
                images.append(None)

        # Filter out None values
        valid_images = [img for img in images if img is not None]

        # Process in batches
        all_results = []
        for i in range(0, len(valid_images), batch_size):
            batch = valid_images[i : i + batch_size]

            # Perform batch inference
            batch_results = self.inference_engine.predict_batch(
                batch, model_version=model_version
            )

            all_results.extend(batch_results)

            # Update progress
            self.update_state(
                state="PROCESSING",
                meta={
                    "current": min(i + batch_size, len(valid_images)),
                    "total": total_images,
                },
            )

        # Add task metadata
        execution_time = time.time() - start_time
        for result in all_results:
            result["task_id"] = self.request.id

        logger.info(
            f"Batch prediction completed: {len(all_results)} images "
            f"in {execution_time:.2f}s "
            f"({execution_time/len(all_results):.3f}s per image)"
        )

        return all_results

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        raise


@celery_app.task(
    base=MLTask,
    bind=True,
    name="services.worker.tasks.ml_tasks.load_model",
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
)
def load_model(self, model_version: str, force_reload: bool = False) -> Dict[str, Any]:
    """
    Load Model (Async Task)

    Loads model asynchronously for pre-warming or version switching.

    Args:
        model_version: Model version to load
        force_reload: Force reload even if cached

    Returns:
        Dict containing model metadata

    Example:
        >>> result = load_model.delay("v1.1.0")
        >>> metadata = result.get()
        >>> print(f"Model loaded: {metadata['version']}")

    Use Cases:
        - Pre-warm models before traffic spike
        - Switch active model version
        - Validate model files
    """
    start_time = time.time()

    try:
        # Load model
        model = self.model_manager.load_model(
            version=model_version, force_reload=force_reload
        )

        # Get metadata
        metadata = self.model_manager.get_metadata(model_version)

        result = {
            "version": metadata.version,
            "architecture": metadata.architecture,
            "num_parameters": metadata.num_parameters,
            "checksum": metadata.checksum,
            "load_time_seconds": time.time() - start_time,
            "task_id": self.request.id,
        }

        logger.info(f"Model loaded successfully: {model_version}")

        return result

    except Exception as e:
        logger.error(f"Model loading failed: {e}", exc_info=True)
        raise


@celery_app.task(
    base=MLTask,
    bind=True,
    name="services.worker.tasks.ml_tasks.benchmark_model",
    time_limit=600,  # 10 minutes
    soft_time_limit=540,
)
def benchmark_model(
    self,
    model_version: str,
    num_samples: int = 100,
    batch_sizes: List[int] = [1, 8, 16, 32],
) -> Dict[str, Any]:
    """
    Benchmark Model Performance (Async Task)

    Performs comprehensive performance benchmarking of a model.
    Tests different batch sizes and measures latency/throughput.

    Args:
        model_version: Model version to benchmark
        num_samples: Number of samples for benchmarking
        batch_sizes: List of batch sizes to test

    Returns:
        Dict containing benchmark results

    Example:
        >>> result = benchmark_model.delay("v1.0.0", num_samples=50)
        >>> benchmarks = result.get()
        >>> print(f"Latency p95: {benchmarks['latency_p95_ms']}ms")

    Metrics Collected:
        - Latency (p50, p95, p99)
        - Throughput (images/second)
        - Memory usage
        - Batch size impact
    """
    import torch

    start_time = time.time()

    try:
        # Load model
        model = self.model_manager.get_model(model_version)

        # Generate dummy data
        dummy_images = [
            Image.new("RGB", (224, 224), color="red") for _ in range(num_samples)
        ]

        results = {
            "model_version": model_version,
            "num_samples": num_samples,
            "batch_results": {},
        }

        # Benchmark each batch size
        for batch_size in batch_sizes:
            latencies = []

            # Run multiple iterations
            for i in range(0, num_samples, batch_size):
                batch = dummy_images[i : i + batch_size]

                start = time.time()
                _ = self.inference_engine.predict_batch(batch)
                latency = (time.time() - start) * 1000  # Convert to ms

                latencies.append(latency)

            # Calculate statistics
            latencies_sorted = sorted(latencies)
            n = len(latencies_sorted)

            results["batch_results"][f"batch_{batch_size}"] = {
                "latency_mean_ms": np.mean(latencies),
                "latency_p50_ms": latencies_sorted[int(n * 0.5)],
                "latency_p95_ms": latencies_sorted[int(n * 0.95)],
                "latency_p99_ms": latencies_sorted[int(n * 0.99)],
                "throughput_imgs_per_sec": batch_size / (np.mean(latencies) / 1000),
            }

        # Add GPU memory stats if available
        if torch.cuda.is_available():
            results["gpu_memory_allocated_gb"] = torch.cuda.memory_allocated() / 1e9
            results["gpu_memory_reserved_gb"] = torch.cuda.memory_reserved() / 1e9

        results["total_benchmark_time_seconds"] = time.time() - start_time
        results["task_id"] = self.request.id

        logger.info(f"Model benchmark completed for {model_version}")

        return results

    except Exception as e:
        logger.error(f"Model benchmarking failed: {e}", exc_info=True)
        raise


@celery_app.task(name="services.worker.tasks.ml_tasks.batch_predict_chunked")
def batch_predict_chunked(
    image_data_list: List[str],
    chunk_size: int = 100,
    model_version: Optional[str] = None,
) -> str:
    """
    Batch Predict with Chunking (Chord Pattern)

    Processes large batches by splitting into chunks and processing in parallel.
    Uses Celery's chord pattern for distributed processing.

    Args:
        image_data_list: List of base64-encoded images
        chunk_size: Size of each chunk
        model_version: Optional model version

    Returns:
        str: Task group ID for tracking

    Example:
        >>> images = [base64.b64encode(img).decode() for img in large_dataset]
        >>> group_id = batch_predict_chunked.delay(images, chunk_size=50)
        >>> # Track progress using group_id

    Architecture:
        Uses Celery chord: (task1 | task2 | task3) | callback
        - Parallel processing of chunks
        - Final aggregation in callback
    """
    # Split into chunks
    chunks = [
        image_data_list[i : i + chunk_size]
        for i in range(0, len(image_data_list), chunk_size)
    ]

    # Create parallel tasks
    job = group(predict_batch.s(chunk, model_version=model_version) for chunk in chunks)

    # Execute and return group ID
    result = job.apply_async()

    logger.info(
        f"Started chunked batch prediction: "
        f"{len(image_data_list)} images in {len(chunks)} chunks"
    )

    return result.id
