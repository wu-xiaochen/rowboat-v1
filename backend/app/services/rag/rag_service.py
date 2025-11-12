"""
RAG服务实现
RAG service implementation for vector search and retrieval
"""

import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    PointStruct,
)

from app.core.config import get_settings
from app.core.database import get_qdrant_client
from app.services.rag.embedding_service import get_embedding_service
from app.models.schemas import RAGReturnType


class RAGResult(BaseModel):
    """RAG搜索结果"""
    title: str
    name: str
    content: str
    doc_id: str = Field(alias="docId")
    source_id: str = Field(alias="sourceId")
    
    class Config:
        populate_by_name = True


class RAGService:
    """
    RAG服务
    RAG service for vector search and retrieval
    """
    
    COLLECTION_NAME = "embeddings"
    
    def __init__(self):
        """初始化RAG服务"""
        self.settings = get_settings()
        self.qdrant_client = get_qdrant_client()
        self.embedding_service = get_embedding_service()
    
    async def search(
        self,
        project_id: str,
        query: str,
        source_ids: List[str],
        return_type: RAGReturnType = RAGReturnType.CHUNKS,
        k: int = 3,
    ) -> List[RAGResult]:
        """
        搜索相关文档
        Search for relevant documents
        
        Args:
            project_id: 项目ID
            query: 查询文本
            source_ids: 数据源ID列表
            return_type: 返回类型（chunks或content）
            k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 生成查询嵌入向量
        embedding, _ = await self.embedding_service.embed(query)
        
        # 构建过滤器
        filter_conditions = [
            FieldCondition(
                key="projectId",
                match=MatchValue(value=project_id)
            ),
            FieldCondition(
                key="sourceId",
                match=MatchAny(any=source_ids)
            ),
        ]
        filter_condition = Filter(must=filter_conditions)
        
        # 执行向量搜索
        try:
            search_results = self.qdrant_client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=embedding,
                query_filter=filter_condition,
                limit=k,
                with_payload=True,
            )
        except Exception as e:
            # 如果集合不存在，返回空列表
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                return []
            raise Exception(f"向量搜索失败: {e}")
        
        # 处理搜索结果
        # 注意：search方法返回的是ScoredPoint列表
        results = []
        for scored_point in search_results:
            payload = scored_point.payload
            if payload:
                result = RAGResult(
                    title=payload.get("title", ""),
                    name=payload.get("name", ""),
                    content=payload.get("content", ""),
                    doc_id=payload.get("docId", ""),
                    source_id=payload.get("sourceId", ""),
                )
                results.append(result)
        
        # 如果返回类型是chunks，直接返回
        if return_type == RAGReturnType.CHUNKS:
            return results
        
        # 如果返回类型是content，需要从MongoDB获取完整内容
        # 注意：这里暂时返回chunks，后续需要从MongoDB获取完整内容
        # TODO: 从MongoDB获取完整内容
        return results
    
    async def upsert_embeddings(
        self,
        project_id: str,
        source_id: str,
        doc_id: str,
        doc_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        """
        存储嵌入向量
        Store embeddings in Qdrant
        
        Args:
            project_id: 项目ID
            source_id: 数据源ID
            doc_id: 文档ID
            doc_name: 文档名称
            chunks: 文本块列表
            embeddings: 嵌入向量列表
        """
        # 准备点数据
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "projectId": project_id,
                    "sourceId": source_id,
                    "docId": doc_id,
                    "content": chunk,
                    "title": doc_name,
                    "name": doc_name,
                },
            )
            points.append(point)
        
        # 存储到Qdrant
        try:
            self.qdrant_client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points,
            )
        except Exception as e:
            raise Exception(f"存储嵌入向量失败: {e}")
    
    async def delete_embeddings(
        self,
        project_id: str,
        source_id: Optional[str] = None,
        doc_id: Optional[str] = None,
    ) -> None:
        """
        删除嵌入向量
        Delete embeddings from Qdrant
        
        Args:
            project_id: 项目ID
            source_id: 数据源ID（可选）
            doc_id: 文档ID（可选）
        """
        # 构建过滤器
        filter_conditions = [
            FieldCondition(
                key="projectId",
                match=MatchValue(value=project_id)
            ),
        ]
        
        if source_id:
            filter_conditions.append(
                FieldCondition(
                    key="sourceId",
                    match=MatchValue(value=source_id)
                )
            )
        
        if doc_id:
            filter_conditions.append(
                FieldCondition(
                    key="docId",
                    match=MatchValue(value=doc_id)
                )
            )
        
        filter_condition = Filter(must=filter_conditions)
        
        # 删除点
        try:
            # 注意：Qdrant的删除操作需要先查询点ID
            # 这里暂时不实现，后续需要完善
            # TODO: 实现删除操作
            pass
        except Exception as e:
            raise Exception(f"删除嵌入向量失败: {e}")


# 全局RAG服务实例（单例模式）
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    获取RAG服务实例（单例）
    Get RAG service instance (singleton)
    
    Returns:
        RAG服务实例
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService()
    
    return _rag_service

