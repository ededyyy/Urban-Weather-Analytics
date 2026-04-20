from __future__ import annotations

import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

_basic_auth = HTTPBasic()


def require_basic_auth(
    credentials: HTTPBasicCredentials = Depends(_basic_auth),
) -> str:
    """
    Simple HTTP Basic auth for API endpoints.

    Configure with environment variables:
    - API_AUTH_USERNAME (default: admin)
    - API_AUTH_PASSWORD (default: admin123)
    """
    expected_username = os.getenv("API_AUTH_USERNAME", "admin")
    expected_password = os.getenv("API_AUTH_PASSWORD", "admin123")

    valid_username = secrets.compare_digest(
        credentials.username, expected_username
    )
    valid_password = secrets.compare_digest(
        credentials.password, expected_password
    )
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid authentication credentials"},
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
