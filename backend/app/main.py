"""
FastAPI应用实例
FastAPI application instance (placeholder for now)
"""

from fastapi import FastAPI
from app.core.config import settings

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="质信智购 - AI智能体平台后端API",
    version="1.0.0",
)


@app.get("/")
async def root():
    """
    根端点
    Root endpoint
    """
    return {
        "message": f"欢迎使用{settings.app_name}",
        "version": "1.0.0",
        "status": "running"
    }

