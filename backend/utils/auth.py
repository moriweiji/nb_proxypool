# coding=utf-8
"""
API 认证工具
"""

from fastapi import Header, HTTPException, status
from backend.core.settings import settings


def verify_api_key(x_api_key: str = Header(..., description="API Key")):
    """
    验证 API Key
    
    Args:
        x_api_key: 请求头中的 API Key
    
    Raises:
        HTTPException: API Key 无效时抛出 401 错误
    """
    valid_keys = settings.api_keys_list
    
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return x_api_key

