"""
Embedding服务实现
Embedding service implementation
"""

from typing import List, Optional
from openai import OpenAI

from app.core.config import get_settings


class EmbeddingService:
    """
    Embedding服务
    Embedding service for generating embeddings
    """
    
    def __init__(self):
        """初始化Embedding服务"""
        self.settings = get_settings()
        
        # 初始化OpenAI客户端（兼容API）
        self.client = OpenAI(
            api_key=self.settings.embedding_provider_api_key,
            base_url=self.settings.embedding_provider_base_url,
        )
        self.model = self.settings.embedding_model
    
    async def embed(self, text: str) -> tuple[List[float], int]:
        """
        生成单个文本的嵌入向量
        Generate embedding for a single text
        
        Args:
            text: 文本内容
            
        Returns:
            (embedding向量, token数量)
        """
        try:
            # 调用OpenAI兼容的API（注意：OpenAI客户端是同步的，需要在异步环境中使用）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.embeddings.create(
                    model=self.model,
                    input=text,
                )
            )
            
            # 提取嵌入向量和token数量
            embedding = response.data[0].embedding
            tokens = response.usage.total_tokens
            
            return embedding, tokens
            
        except Exception as e:
            raise Exception(f"生成嵌入向量失败: {e}")
    
    async def embed_many(self, texts: List[str]) -> tuple[List[List[float]], int]:
        """
        批量生成文本的嵌入向量
        Generate embeddings for multiple texts
        
        Args:
            texts: 文本列表
            
        Returns:
            (嵌入向量列表, token总数)
        """
        try:
            # 调用OpenAI兼容的API（注意：OpenAI客户端是同步的，需要在异步环境中使用）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                )
            )
            
            # 提取嵌入向量列表和token数量
            embeddings = [item.embedding for item in response.data]
            tokens = response.usage.total_tokens
            
            return embeddings, tokens
            
        except Exception as e:
            raise Exception(f"批量生成嵌入向量失败: {e}")


# 全局Embedding服务实例（单例模式）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    获取Embedding服务实例（单例）
    Get Embedding service instance (singleton)
    
    Returns:
        Embedding服务实例
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    
    return _embedding_service

