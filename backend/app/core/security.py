"""
安全相关工具
Security utilities for authentication and authorization
"""

import secrets
import hashlib
from typing import Optional


def generate_api_key(length: int = 32) -> str:
    """
    生成API Key
    Generate a secure random API key
    
    Args:
        length: key的长度（字符数）
        
    Returns:
        生成的API key
    """
    # 生成随机字节并转换为hex字符串
    return secrets.token_hex(length)


def generate_project_secret(length: int = 32) -> str:
    """
    生成项目Secret
    Generate a project secret
    
    Args:
        length: secret的长度（字符数）
        
    Returns:
        生成的secret
    """
    return secrets.token_hex(length)


def hash_api_key(api_key: str) -> str:
    """
    对API Key进行哈希
    Hash an API key for secure storage
    
    Args:
        api_key: 原始API key
        
    Returns:
        哈希后的key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    验证API Key
    Verify an API key against its hash
    
    Args:
        plain_key: 原始API key
        hashed_key: 哈希后的key
        
    Returns:
        是否匹配
    """
    return hash_api_key(plain_key) == hashed_key


def get_key_prefix(api_key: str, length: int = 8) -> str:
    """
    获取API Key的前缀（用于显示）
    Get the prefix of an API key for display purposes
    
    Args:
        api_key: API key
        length: 前缀长度
        
    Returns:
        key前缀
    """
    return api_key[:length] if len(api_key) >= length else api_key

