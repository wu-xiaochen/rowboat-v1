"""
API v1路由汇总
API v1 router aggregation
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, info, api_keys

# 创建v1路由器
router = APIRouter(prefix="/api/v1")

# 注册各个端点
router.include_router(health.router)
router.include_router(info.router)
router.include_router(api_keys.router)

