"""
健康检查端点
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime

from app.api import ResponseModel
from app.core.config import get_settings
from app.core.database import (
    check_mongodb_connection,
    check_redis_connection,
    check_qdrant_connection,
)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    健康检查端点
    Health check endpoint
    
    Returns:
        应用健康状态
    """
    settings = get_settings()
    
    # 检查所有数据库连接
    mongodb_ok = await check_mongodb_connection()
    redis_ok = await check_redis_connection()
    qdrant_ok = check_qdrant_connection() if settings.use_rag else True
    
    all_ok = mongodb_ok and redis_ok and qdrant_ok
    
    return ResponseModel.success(
        data={
            "status": "healthy" if all_ok else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "mongodb": "connected" if mongodb_ok else "disconnected",
                "redis": "connected" if redis_ok else "disconnected",
                "qdrant": "connected" if qdrant_ok else "disconnected" if settings.use_rag else "disabled",
            },
            "features": {
                "rag": settings.use_rag,
                "composio_tools": settings.use_composio_tools,
            }
        },
        message="服务运行正常" if all_ok else "部分服务不可用"
    )


@router.get("/ping")
async def ping():
    """
    简单的ping端点
    Simple ping endpoint
    
    Returns:
        pong响应
    """
    return ResponseModel.success(
        data={"ping": "pong", "timestamp": datetime.now().isoformat()},
        message="服务可用"
    )

