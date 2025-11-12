"""
配置管理模块
Configuration management module using pydantic-settings
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    Application settings loaded from environment variables
    """
    
    # 应用配置
    app_name: str = Field(default="质信智购", description="应用名称")
    api_port: int = Field(default=8001, description="API服务端口")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    
    # LLM Provider配置（OpenAI兼容）
    llm_api_key: str = Field(..., description="LLM API密钥")
    llm_base_url: str = Field(..., description="LLM API基础URL")
    llm_model_id: str = Field(..., description="LLM模型ID")
    
    # Embedding配置
    embedding_model: str = Field(..., description="Embedding模型名称")
    embedding_provider_base_url: str = Field(..., description="Embedding提供商基础URL")
    embedding_provider_api_key: str = Field(..., description="Embedding API密钥")
    
    # Composio配置
    composio_api_key: str = Field(..., description="Composio API密钥")
    
    # 数据库配置
    mongodb_connection_string: str = Field(..., description="MongoDB连接字符串")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis连接URL")
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant连接URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API密钥")
    
    # 功能开关
    use_rag: bool = Field(default=True, description="是否启用RAG功能")
    use_composio_tools: bool = Field(default=True, description="是否启用Composio工具")
    
    # CORS配置
    cors_origins: str | List[str] = Field(
        default=["http://localhost:3001", "http://localhost:3000"],
        description="允许的CORS源"
    )
    
    # JWT配置
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", description="JWT密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_expire_minutes: int = Field(default=60, description="JWT过期时间（分钟）")
    
    # 提示词配置
    prompts_dir: str = Field(
        default="config/prompts",
        description="提示词文件目录"
    )
    copilot_model: str = Field(
        default="gpt-4.1",
        description="Copilot模型名称"
    )
    agent_model: str = Field(
        default="gpt-4.1",
        description="智能体默认模型名称"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS origins，确保返回列表"""
        if isinstance(v, str):
            # 按逗号分割
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    def validate_config(self) -> None:
        """
        验证配置完整性
        Validate that all required configurations are present
        """
        required_fields = [
            "llm_api_key",
            "llm_base_url",
            "llm_model_id",
            "embedding_model",
            "embedding_provider_base_url",
            "embedding_provider_api_key",
            "composio_api_key",
            "mongodb_connection_string",
        ]
        
        missing_fields = []
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and value.startswith("your-")):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"配置验证失败：以下必需字段缺失或未配置: {', '.join(missing_fields)}"
            )


# 全局配置实例（延迟初始化）
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    Get settings instance (singleton pattern)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# 为了向后兼容，提供一个便捷的访问方式
# 注意：在测试环境中不要在模块级别访问 settings
try:
    settings = get_settings()
except Exception:
    # 在测试环境或配置未就绪时，不创建实例
    settings = None  # type: ignore

