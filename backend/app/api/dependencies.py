"""
API依赖注入
API dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Header, HTTPException, status

from app.repositories.api_keys import APIKeysRepository
from app.core.security import hash_api_key


async def verify_api_key(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    验证API Key
    Verify API key from Authorization header
    
    Args:
        authorization: Authorization header value (Bearer {key})
        
    Returns:
        验证通过的项目ID
        
    Raises:
        HTTPException: 如果验证失败
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少Authorization header"
        )
    
    # 检查格式：Bearer {key}
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header格式错误，应为: Bearer {key}"
        )
    
    api_key = parts[1]
    
    # 哈希API key
    key_hash = hash_api_key(api_key)
    
    # 查询数据库
    repo = APIKeysRepository()
    api_key_obj = await repo.get_by_key_hash(key_hash)
    
    if api_key_obj is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key已停用"
        )
    
    # 更新最后使用时间（异步，不等待）
    await repo.update_last_used(api_key_obj.id)
    
    return api_key_obj.project_id


async def get_optional_api_key(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    可选的API Key验证（用于某些公开端点）
    Optional API key verification for public endpoints
    
    Args:
        authorization: Authorization header value
        
    Returns:
        项目ID（如果提供了有效的key），否则返回None
    """
    if not authorization:
        return None
    
    try:
        return await verify_api_key(authorization)
    except HTTPException:
        return None

