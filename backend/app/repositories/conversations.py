"""
对话数据访问层
Conversations Repository for database operations
"""

from typing import List, Optional
from datetime import datetime

from app.core.database import get_mongodb_db
from app.models.schemas import Conversation, Turn


class ConversationsRepository:
    """
    对话数据访问类
    Repository for Conversation CRUD operations
    """
    
    def __init__(self):
        """初始化Repository"""
        self.collection_name = "conversations"
    
    async def create(self, conversation: Conversation) -> Conversation:
        """
        创建对话
        Create a new conversation
        
        Args:
            conversation: 对话对象
            
        Returns:
            创建的对话对象
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 转换为字典，准备插入数据库
        conversation_dict = conversation.model_dump(by_alias=True, exclude={"id"})
        
        # 添加id字段到字典中（MongoDB不需要，但我们保留用于查询）
        conversation_dict["id"] = conversation.id
        
        # 插入数据库
        await collection.insert_one(conversation_dict)
        
        # 返回创建的对话
        return conversation
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        根据ID获取对话
        Get conversation by ID
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 查询数据库
        doc = await collection.find_one({"id": conversation_id})
        
        if doc is None:
            return None
        
        # 移除MongoDB的_id字段
        if "_id" in doc:
            del doc["_id"]
        
        # 转换为Pydantic模型
        return Conversation(**doc)
    
    async def get_by_project_id(
        self,
        project_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """
        根据项目ID获取对话列表
        Get conversations by project ID
        
        Args:
            project_id: 项目ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            对话列表
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 查询数据库
        cursor = collection.find(
            {"projectId": project_id}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        # 转换为Pydantic模型列表
        conversations = []
        async for doc in cursor:
            if "_id" in doc:
                del doc["_id"]
            conversations.append(Conversation(**doc))
        
        return conversations
    
    async def update(
        self,
        conversation_id: str,
        conversation: Conversation
    ) -> Optional[Conversation]:
        """
        更新对话
        Update a conversation
        
        Args:
            conversation_id: 对话ID
            conversation: 更新的对话对象
            
        Returns:
            更新后的对话对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 更新updatedAt字段
        conversation_dict = conversation.model_dump(by_alias=True, exclude={"id"})
        conversation_dict["updatedAt"] = datetime.now()
        
        # 更新数据库
        result = await collection.update_one(
            {"id": conversation_id},
            {"$set": conversation_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        # 返回更新后的对话
        return await self.get_by_id(conversation_id)
    
    async def add_turn(self, conversation_id: str, turn: Turn) -> Optional[Conversation]:
        """
        向对话添加轮次
        Add a turn to conversation
        
        Args:
            conversation_id: 对话ID
            turn: 轮次对象
            
        Returns:
            更新后的对话对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 转换轮次为字典
        turn_dict = turn.model_dump(by_alias=True)
        
        # 更新数据库（添加到turns数组）
        result = await collection.update_one(
            {"id": conversation_id},
            {
                "$push": {"turns": turn_dict},
                "$set": {"updatedAt": datetime.now()}
            }
        )
        
        if result.matched_count == 0:
            return None
        
        # 返回更新后的对话
        return await self.get_by_id(conversation_id)
    
    async def delete(self, conversation_id: str) -> bool:
        """
        删除对话
        Delete a conversation
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否删除成功
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 删除数据库记录
        result = await collection.delete_one({"id": conversation_id})
        
        return result.deleted_count > 0
    
    async def exists(self, conversation_id: str) -> bool:
        """
        检查对话是否存在
        Check if conversation exists
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否存在
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        count = await collection.count_documents({"id": conversation_id}, limit=1)
        return count > 0
    
    async def count_by_project_id(self, project_id: str) -> int:
        """
        统计项目的对话数量
        Count conversations by project ID
        
        Args:
            project_id: 项目ID
            
        Returns:
            对话数量
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        return await collection.count_documents({"projectId": project_id})

