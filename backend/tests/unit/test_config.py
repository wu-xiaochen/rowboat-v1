"""
配置管理测试
Tests for configuration management
"""

import pytest
import os
from pydantic import ValidationError
from app.core.config import Settings


class TestSettings:
    """配置类测试"""
    
    def test_settings_with_valid_env_vars(self, monkeypatch):
        """测试：使用有效的环境变量创建配置"""
        # 设置环境变量
        test_env_vars = {
            "APP_NAME": "测试应用",
            "API_PORT": "8888",
            "DEBUG": "true",
            "ENVIRONMENT": "test",
            "LLM_API_KEY": "test-llm-key",
            "LLM_BASE_URL": "https://test-llm.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test-embedding.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-embedding-key",
            "COMPOSIO_API_KEY": "test-composio-key",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/testdb",
            "REDIS_URL": "redis://test:6379",
            "QDRANT_URL": "http://test:6333",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        # 创建配置实例
        settings = Settings()
        
        # 验证配置值
        assert settings.app_name == "测试应用"
        assert settings.api_port == 8888
        assert settings.debug is True
        assert settings.environment == "test"
        assert settings.llm_api_key == "test-llm-key"
        assert settings.llm_base_url == "https://test-llm.com"
        assert settings.llm_model_id == "test-model"
        assert settings.embedding_model == "test-embedding"
        assert settings.mongodb_connection_string == "mongodb://test:27017/testdb"
    
    def test_settings_default_values(self, monkeypatch):
        """测试：配置的默认值"""
        # 清除可能影响的环境变量
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        
        # 只设置必需的环境变量
        required_vars = {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/test",
        }
        
        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        # 验证默认值
        assert settings.app_name == "质信智购"
        assert settings.api_port == 8001
        assert settings.debug is False
        assert settings.environment == "development"
        assert settings.use_rag is True
        assert settings.use_composio_tools is True
    
    def test_cors_origins_parsing_from_json(self, monkeypatch):
        """测试：从JSON字符串解析CORS origins"""
        required_vars = {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/test",
            "CORS_ORIGINS": '["http://example.com", "https://example.org"]',
        }
        
        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        assert len(settings.cors_origins) == 2
        assert "http://example.com" in settings.cors_origins
        assert "https://example.org" in settings.cors_origins
    
    def test_cors_origins_parsing_from_comma_separated(self, monkeypatch):
        """测试：从逗号分隔字符串解析CORS origins"""
        required_vars = {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://test.com",
            "LLM_MODEL_ID": "test-model",
            "EMBEDDING_MODEL": "test-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://test.com",
            "EMBEDDING_PROVIDER_API_KEY": "test-key",
            "COMPOSIO_API_KEY": "test-key",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/test",
            "CORS_ORIGINS": "http://example.com, https://example.org",
        }
        
        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        assert len(settings.cors_origins) == 2
        assert "http://example.com" in settings.cors_origins
        assert "https://example.org" in settings.cors_origins
    
    def test_validate_config_success(self, monkeypatch):
        """测试：配置验证成功"""
        test_env_vars = {
            "LLM_API_KEY": "valid-key",
            "LLM_BASE_URL": "https://valid.com",
            "LLM_MODEL_ID": "valid-model",
            "EMBEDDING_MODEL": "valid-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://valid.com",
            "EMBEDDING_PROVIDER_API_KEY": "valid-key",
            "COMPOSIO_API_KEY": "valid-key",
            "MONGODB_CONNECTION_STRING": "mongodb://valid:27017/test",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        # 应该不抛出异常
        settings.validate_config()
    
    def test_validate_config_failure_missing_keys(self, monkeypatch):
        """测试：配置验证失败（缺少必需字段）"""
        # 设置所有必需字段为占位符值
        test_env_vars = {
            "LLM_API_KEY": "",  # 空值
            "LLM_BASE_URL": "",
            "LLM_MODEL_ID": "valid-model",
            "EMBEDDING_MODEL": "valid-model",
            "EMBEDDING_PROVIDER_BASE_URL": "https://valid.com",
            "EMBEDDING_PROVIDER_API_KEY": "valid-key",
            "COMPOSIO_API_KEY": "valid-key",
            "MONGODB_CONNECTION_STRING": "mongodb://test:27017/test",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        # 应该抛出 ValueError（因为有空值）
        with pytest.raises(ValueError) as exc_info:
            settings.validate_config()
        
        assert "配置验证失败" in str(exc_info.value)
    
    def test_validate_config_failure_placeholder_values(self, monkeypatch):
        """测试：配置验证失败（使用占位符值）"""
        test_env_vars = {
            "LLM_API_KEY": "your-llm-api-key-here",  # 占位符值
            "LLM_BASE_URL": "https://valid.com",
            "LLM_MODEL_ID": "valid-model",
            "EMBEDDING_MODEL": "valid-embedding",
            "EMBEDDING_PROVIDER_BASE_URL": "https://valid.com",
            "EMBEDDING_PROVIDER_API_KEY": "your-key-here",  # 占位符值
            "COMPOSIO_API_KEY": "valid-key",
            "MONGODB_CONNECTION_STRING": "mongodb://valid:27017/test",
        }
        
        for key, value in test_env_vars.items():
            monkeypatch.setenv(key, value)
        
        settings = Settings()
        
        # 应该抛出 ValueError（因为包含占位符值）
        with pytest.raises(ValueError) as exc_info:
            settings.validate_config()
        
        assert "llm_api_key" in str(exc_info.value)
        assert "embedding_provider_api_key" in str(exc_info.value)

