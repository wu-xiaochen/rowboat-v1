"""
FastAPI应用入口
Main entry point for the FastAPI application
"""

import uvicorn
from app.core.config import settings


def main():
    """
    启动FastAPI应用
    Start the FastAPI application
    """
    # 验证配置
    try:
        settings.validate_config()
        print(f"✓ 配置验证成功")
        print(f"✓ 应用名称: {settings.app_name}")
        print(f"✓ 运行环境: {settings.environment}")
        print(f"✓ 启动端口: {settings.api_port}")
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
        print(f"✗ 请检查 .env 文件或环境变量")
        return
    
    # 启动应用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()

