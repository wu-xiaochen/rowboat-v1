"""
缓存服务
Cache service for performance optimization using Redis
"""

from typing import Optional, Any
import json
from datetime import timedelta

from app.core.database import get_redis_client
from app.core.config import get_settings


class CacheService:
    """
    缓存服务类
    Cache service for storing and retrieving cached data
    """
    
    def __init__(self):
        """初始化缓存服务"""
        self.default_ttl = 300  # 默认过期时间：5分钟
        self.settings = get_settings()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        Get cached value
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        try:
            client = await get_redis_client()
            value = await client.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            # 缓存失败不应影响主流程
            print(f"缓存获取失败: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        Set cached value
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认使用default_ttl
            
        Returns:
            是否设置成功
        """
        try:
            client = await get_redis_client()
            ttl = ttl or self.default_ttl
            
            # 尝试序列化为JSON
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, default=str)
            else:
                value_str = str(value)
            
            await client.setex(key, ttl, value_str)
            return True
        except Exception as e:
            # 缓存失败不应影响主流程
            print(f"缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存值
        Delete cached value
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            client = await get_redis_client()
            await client.delete(key)
            return True
        except Exception as e:
            print(f"缓存删除失败: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        按模式删除缓存
        Delete cached values by pattern
        
        Args:
            pattern: 匹配模式（如 "project:*"）
            
        Returns:
            删除的数量
        """
        try:
            client = await get_redis_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            print(f"批量删除缓存失败: {e}")
            return 0
    
    def get_project_key(self, project_id: str) -> str:
        """获取项目缓存键"""
        return f"project:{project_id}"
    
    def get_api_key_key(self, key_hash: str) -> str:
        """获取API Key缓存键"""
        return f"api_key:{key_hash}"
    
    def get_conversation_key(self, conversation_id: str) -> str:
        """获取对话缓存键"""
        return f"conversation:{conversation_id}"


# 全局缓存服务实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    获取缓存服务实例（单例模式）
    Get cache service instance (singleton pattern)
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

