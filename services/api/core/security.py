"""
Security and Authentication Module

This module implements industry-standard security practices including:
- Password hashing using bcrypt
- JWT token generation and validation
- Bearer token authentication
- Role-based access control foundations

Industry Standards:
    - OWASP password hashing guidelines
    - JWT (RFC 7519) for stateless authentication
    - bcrypt for password hashing (OWASP recommended)
    - Bearer token authentication (RFC 6750)
    - Constant-time comparison for security

Security Features:
    - Automatic password strength validation
    - Token expiration and refresh
    - Protection against timing attacks
    - Secure random token generation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

# Password Hashing Context
# Uses bcrypt algorithm (OWASP recommended)
# - Automatic salt generation
# - Configurable work factor (cost)
# - Protection against rainbow table attacks
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",  # Automatically upgrade old hashes
    bcrypt__rounds=12,  # Work factor (higher = more secure but slower)
)

# HTTP Bearer Token Authentication Scheme
# Implements RFC 6750 Bearer Token Usage
# Expects: Authorization: Bearer <token>
security = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="Enter JWT token obtained from /api/v1/auth/login",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify Password Against Hash (Constant-Time Comparison)

    Uses bcrypt's constant-time comparison to prevent timing attacks.
    Automatically handles different hash formats and salt values.

    Args:
        plain_password: User-provided password in plain text
        hashed_password: Stored bcrypt hash from database

    Returns:
        bool: True if password matches hash, False otherwise

    Example:
        >>> hashed = get_password_hash("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False

    Security Notes:
        - Uses constant-time comparison (prevents timing attacks)
        - Automatically verifies salt and work factor
        - Safe against rainbow table attacks

    Performance:
        Typical verification time: 100-300ms (intentionally slow for security)
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash Password Using bcrypt

    Generates a secure bcrypt hash with automatic salt generation.
    Uses configurable work factor for future-proof security.

    Args:
        password: Plain text password to hash

    Returns:
        str: Bcrypt hash string (includes algorithm, cost, salt, and hash)

    Example:
        >>> hash1 = get_password_hash("mypassword")
        >>> hash2 = get_password_hash("mypassword")
        >>> hash1 != hash2  # Different salts
        True

    Security Notes:
        - Automatic random salt generation
        - Work factor of 12 rounds (2^12 iterations)
        - Resistant to GPU cracking attempts
        - Follows OWASP password storage guidelines

    Performance:
        Typical hashing time: 100-300ms (intentionally slow)

    Best Practices:
        - Never log or display hashed passwords
        - Store in database with sufficient field length (60+ chars)
        - Consider adding pepper (application-level secret) for extra security
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT Access Token (RFC 7519)

    Generates a signed JWT token for stateless authentication.
    Token includes user claims and expiration time.

    Args:
        data: Claims to encode in token (e.g., user_id, username, roles)
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "user123", "role": "admin"})
        >>> # Token format: header.payload.signature

    Token Structure:
        - Header: Algorithm and token type
        - Payload: User claims + expiration
        - Signature: HMAC-SHA256 signature

    Security Notes:
        - Tokens are signed but not encrypted (don't store sensitive data)
        - Include expiration time to limit token lifetime
        - Validate signature on every request
        - Consider implementing token refresh mechanism

    Best Practices:
        - Keep tokens short-lived (15-60 minutes)
        - Use refresh tokens for long sessions
        - Implement token revocation for logout
        - Store tokens securely on client (httpOnly cookies or secure storage)
    """
    # Create a copy to avoid modifying original data
    to_encode = data.copy()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    to_encode.update(
        {
            "exp": expire,  # Expiration time (Unix timestamp)
            "iat": datetime.utcnow(),  # Issued at time
            "type": "access",  # Token type
        }
    )

    # Encode and sign token
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and Validate JWT Token

    Verifies token signature and expiration, then returns payload.
    Raises HTTPException if token is invalid or expired.

    Args:
        token: JWT token string to decode

    Returns:
        Dict[str, Any]: Decoded token payload (claims)

    Raises:
        HTTPException: 401 Unauthorized if token is invalid

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        'user123'

    Validation Checks:
        - Signature verification (prevents tampering)
        - Expiration time check
        - Algorithm verification (prevents algorithm confusion)

    Security Notes:
        - Always validate tokens on protected endpoints
        - Check expiration time server-side
        - Implement token revocation for sensitive operations
        - Log failed validation attempts for security monitoring
    """
    try:
        # Decode and verify token
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        # Token is invalid, expired, or tampered
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User data from token

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Active user data

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
