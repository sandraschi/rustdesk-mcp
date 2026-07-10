import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Standard basic authentication for MCP web bridges."""
    correct_username = os.getenv("RUSTDESK_WEB_USER", "admin")
    correct_password = os.getenv("RUSTDESK_WEB_PASS", "admin123")

    is_username_correct = secrets.compare_digest(credentials.username, correct_username)
    is_password_correct = secrets.compare_digest(credentials.password, correct_password)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
