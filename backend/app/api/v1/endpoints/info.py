"""
API信息端点
API information endpoints
"""

from fastapi import APIRouter

from app.api import ResponseModel
from app.core.config import get_settings

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("")
async def get_api_info():
    """
    获取API信息
    Get API information
    
    Returns:
        API版本、配置等信息
    """
    settings = get_settings()
    
    return ResponseModel.success(
        data={
            "name": settings.app_name,
            "version": "1.0.0",
            "environment": settings.environment,
            "api_version": "v1",
            "features": {
                "rag": settings.use_rag,
                "composio_tools": settings.use_composio_tools,
            },
            "llm_provider": {
                "base_url": settings.llm_base_url,
                "model_id": settings.llm_model_id,
            },
            "embedding_provider": {
                "model": settings.embedding_model,
            }
        },
        message="API信息获取成功"
    )

