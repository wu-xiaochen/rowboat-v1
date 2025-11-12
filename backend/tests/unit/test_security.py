"""
安全工具测试
Tests for security utilities
"""

import pytest
from app.core.security import (
    generate_api_key,
    generate_project_secret,
    hash_api_key,
    verify_api_key,
    get_key_prefix,
)


class TestAPIKeySecurity:
    """API Key安全测试"""
    
    def test_generate_api_key(self):
        """测试：生成API Key"""
        key = generate_api_key()
        
        assert key is not None
        assert len(key) == 64  # 32 bytes = 64 hex characters
        assert isinstance(key, str)
    
    def test_generate_api_key_with_custom_length(self):
        """测试：生成指定长度的API Key"""
        key = generate_api_key(length=16)
        
        assert len(key) == 32  # 16 bytes = 32 hex characters
    
    def test_generate_project_secret(self):
        """测试：生成项目Secret"""
        secret = generate_project_secret()
        
        assert secret is not None
        assert len(secret) == 64
        assert isinstance(secret, str)
    
    def test_hash_api_key(self):
        """测试：对API Key进行哈希"""
        key = "test_key_12345"
        hashed = hash_api_key(key)
        
        assert hashed is not None
        assert len(hashed) == 64  # SHA256 produces 64 hex characters
        assert hashed != key  # 哈希后不同
    
    def test_hash_api_key_deterministic(self):
        """测试：相同的key产生相同的哈希"""
        key = "test_key_12345"
        hashed1 = hash_api_key(key)
        hashed2 = hash_api_key(key)
        
        assert hashed1 == hashed2
    
    def test_hash_api_key_different_keys(self):
        """测试：不同的key产生不同的哈希"""
        key1 = "test_key_1"
        key2 = "test_key_2"
        hashed1 = hash_api_key(key1)
        hashed2 = hash_api_key(key2)
        
        assert hashed1 != hashed2
    
    def test_verify_api_key_success(self):
        """测试：验证API Key成功"""
        key = "test_key_12345"
        hashed = hash_api_key(key)
        
        assert verify_api_key(key, hashed) is True
    
    def test_verify_api_key_failure(self):
        """测试：验证API Key失败"""
        key = "test_key_12345"
        wrong_key = "wrong_key"
        hashed = hash_api_key(key)
        
        assert verify_api_key(wrong_key, hashed) is False
    
    def test_get_key_prefix(self):
        """测试：获取Key前缀"""
        key = "abcdef1234567890"
        prefix = get_key_prefix(key)
        
        assert prefix == "abcdef12"  # 默认8个字符
        assert len(prefix) == 8
    
    def test_get_key_prefix_custom_length(self):
        """测试：获取指定长度的Key前缀"""
        key = "abcdef1234567890"
        prefix = get_key_prefix(key, length=4)
        
        assert prefix == "abcd"
        assert len(prefix) == 4
    
    def test_get_key_prefix_short_key(self):
        """测试：key长度小于前缀长度"""
        key = "abc"
        prefix = get_key_prefix(key, length=8)
        
        assert prefix == "abc"  # 返回完整key

