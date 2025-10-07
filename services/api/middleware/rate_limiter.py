"""
Rate Limiting Middleware Module

Implements token bucket algorithm for API rate limiting.

Industry Standards:
    - Token bucket algorithm
    - Per-user rate limiting
    - Redis-based distributed limiting
    - Configurable limits
    - Rate limit headers (X-RateLimit-*)
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import time
import logging

from ..core.redis_client import get_redis
from ..core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Middleware

    Implements distributed rate limiting using Redis and token bucket algorithm.

    Features:
        - Per-user rate limiting
        - Configurable limits
        - Distributed (Redis-based)
        - Rate limit headers
        - Burst capacity support

    Algorithm:
        Token Bucket - allows burst traffic while maintaining average rate

    Headers:
        - X-RateLimit-Limit: Maximum requests per window
        - X-RateLimit-Remaining: Remaining requests
        - X-RateLimit-Reset: Time when limit resets

    Example:
        ```python
        app.add_middleware(RateLimitMiddleware)
        ```

    Configuration:
        Set in config.py:
        - RATE_LIMIT_PER_MINUTE: Requests per minute
        - RATE_LIMIT_BURST: Burst capacity
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process Request with Rate Limiting

        Checks rate limit before processing request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response

        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/live", "/ready"]:
            return await call_next(request)

        # Get user identifier (IP or user ID)
        user_id = self._get_user_identifier(request)

        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(user_id)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for user: {user_id}",
                extra={"user_id": user_id, "path": request.url.path, "method": request.method},
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(int(reset_time - time.time())),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_user_identifier(self, request: Request) -> str:
        """
        Get User Identifier

        Extracts user identifier for rate limiting.
        Uses authenticated user ID or falls back to IP address.

        Args:
            request: HTTP request

        Returns:
            str: User identifier
        """
        # Try to get authenticated user
        if hasattr(request.state, "user"):
            return f"user:{request.state.user.get('sub')}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def _check_rate_limit(self, user_id: str) -> tuple[bool, int, int]:
        """
        Check Rate Limit (Token Bucket Algorithm)

        Implements distributed rate limiting using Redis.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (allowed, remaining, reset_time)

        Algorithm:
            1. Get current token count from Redis
            2. Calculate tokens to add since last request
            3. Add tokens (up to burst capacity)
            4. Check if enough tokens available
            5. Consume token if allowed
        """
        try:
            redis = await get_redis()

            # Redis keys
            key = f"ratelimit:{user_id}"

            # Current time
            now = time.time()

            # Get current state
            pipe = redis.pipeline()
            pipe.get(f"{key}:tokens")
            pipe.get(f"{key}:last_update")
            tokens_str, last_update_str = await pipe.execute()

            # Parse values
            tokens = float(tokens_str) if tokens_str else settings.RATE_LIMIT_PER_MINUTE
            last_update = float(last_update_str) if last_update_str else now

            # Calculate tokens to add
            time_passed = now - last_update
            tokens_to_add = time_passed * (settings.RATE_LIMIT_PER_MINUTE / 60.0)

            # Update tokens (cap at burst limit)
            tokens = min(
                tokens + tokens_to_add, settings.RATE_LIMIT_PER_MINUTE + settings.RATE_LIMIT_BURST
            )

            # Check if request allowed
            if tokens >= 1:
                # Consume token
                tokens -= 1
                allowed = True
            else:
                allowed = False

            # Update Redis
            pipe = redis.pipeline()
            pipe.set(f"{key}:tokens", str(tokens), ex=3600)  # Expire in 1 hour
            pipe.set(f"{key}:last_update", str(now), ex=3600)
            await pipe.execute()

            # Calculate reset time
            reset_time = int(now + (1 - tokens) / (settings.RATE_LIMIT_PER_MINUTE / 60.0))

            return allowed, int(tokens), reset_time

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            # Fail open (allow request) on Redis errors
            return True, settings.RATE_LIMIT_PER_MINUTE, int(time.time() + 60)
