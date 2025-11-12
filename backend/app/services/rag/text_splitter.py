"""
文本分割服务实现
Text splitter service implementation
"""

from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter


class TextSplitterService:
    """
    文本分割服务
    Text splitter service for splitting documents into chunks
    """
    
    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 20,
        separators: Optional[List[str]] = None,
    ):
        """
        初始化文本分割服务
        Initialize text splitter service
        
        Args:
            chunk_size: 块大小（默认1024）
            chunk_overlap: 块重叠大小（默认20）
            separators: 分隔符列表（默认：['\n\n', '\n', '. ', '.', '']）
        """
        if separators is None:
            separators = ['\n\n', '\n', '. ', '.', '']
        
        self.splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        分割文本
        Split text into chunks
        
        Args:
            text: 文本内容
            
        Returns:
            文本块列表
        """
        documents = self.splitter.create_documents([text])
        return [doc.page_content for doc in documents]
    
    def split_documents(self, texts: List[str]) -> List[str]:
        """
        批量分割文本
        Split multiple texts into chunks
        
        Args:
            texts: 文本列表
            
        Returns:
            文本块列表
        """
        all_chunks = []
        for text in texts:
            chunks = self.split_text(text)
            all_chunks.extend(chunks)
        return all_chunks


# 全局文本分割服务实例（单例模式）
_text_splitter_service: Optional[TextSplitterService] = None


def get_text_splitter_service() -> TextSplitterService:
    """
    获取文本分割服务实例（单例）
    Get text splitter service instance (singleton)
    
    Returns:
        文本分割服务实例
    """
    global _text_splitter_service
    
    if _text_splitter_service is None:
        _text_splitter_service = TextSplitterService()
    
    return _text_splitter_service

