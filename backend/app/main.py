"""
FastAPI应用实例
FastAPI application instance
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict

from app.core.config import get_settings
from app.core.database import (
    initialize_databases,
    close_all_connections,
    create_mongodb_indexes,
)
from app.api import ResponseModel
from app.api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    Application lifespan management
    """
    # 启动时执行
    print("🚀 启动应用...")
    settings = get_settings()
    
    # 初始化数据库连接
    await initialize_databases()
    
    # 创建数据库索引
    try:
        await create_mongodb_indexes()
    except Exception as e:
        print(f"⚠️  创建索引失败: {e}")
    
    print(f"✓ {settings.app_name} 已启动")
    print(f"✓ API文档: http://localhost:{settings.api_port}/docs")
    
    yield
    
    # 关闭时执行
    print("⏹ 关闭应用...")
    await close_all_connections()
    print("✓ 应用已关闭")


# 创建FastAPI应用实例
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="质信智购 - AI智能体平台后端API\n\n"
                "基于FastAPI、LangChain、OpenAI Agent SDK构建的智能体管理平台",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册API路由
app.include_router(v1_router)


# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理请求验证错误
    Handle request validation errors
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseModel.error(
            code="VALIDATION_ERROR",
            message="请求参数验证失败",
            details=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    处理通用异常
    Handle general exceptions
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseModel.error(
            code="INTERNAL_ERROR",
            message="服务器内部错误",
            details=str(exc) if settings.debug else None,
        ),
    )


@app.get("/", tags=["Root"])
async def root():
    """
    根端点
    Root endpoint
    """
    return ResponseModel.success(
        data={
            "name": settings.app_name,
            "version": "1.0.0",
            "environment": settings.environment,
        },
        message=f"欢迎使用{settings.app_name}"
    )

