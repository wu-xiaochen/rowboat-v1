"""
对话数据访问层
Conversations Repository for database operations
严格复刻原项目实现：使用MongoDB ObjectId作为_id
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

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
    
    async def create(self, data: Dict[str, Any]) -> Conversation:
        """
        创建对话
        Create a new conversation
        严格复刻原项目：使用ObjectId作为_id，然后转换为字符串id
        
        Args:
            data: 对话数据字典（包含projectId, workflow, reason, isLiveWorkflow）
            
        Returns:
            创建的对话对象
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 生成ObjectId
        _id = ObjectId()
        
        # 构建文档（排除id字段，因为使用_id）
        now = datetime.now()
        doc = {
            **data,
            "createdAt": now.isoformat(),
        }
        
        # 插入数据库（使用_id）
        await collection.insert_one({**doc, "_id": _id})
        
        # 返回时添加id字段（_id转换为字符串）
        conversation_data = {
            **data,
            "id": str(_id),
            "createdAt": now,
        }
        return Conversation(**conversation_data)
    
    async def fetch(self, conversation_id: str) -> Optional[Conversation]:
        """
        根据ID获取对话（原项目方法名：fetch）
        Fetch conversation by ID
        严格复刻原项目：使用_id查询，然后转换为字符串id
        
        Args:
            conversation_id: 对话ID（ObjectId字符串）
            
        Returns:
            对话对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 从数据库查询（使用_id）
        try:
            doc = await collection.find_one({"_id": ObjectId(conversation_id)})
        except Exception:
            # ObjectId格式错误
            return None
        
        if doc is None:
            return None
        
        # 移除_id，添加id字段（_id转换为字符串）
        _id = doc.pop("_id")
        doc["id"] = str(_id)
        
        # 转换为Pydantic模型
        return Conversation(**doc)
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        根据ID获取对话（别名方法，调用fetch）
        Get conversation by ID (alias for fetch)
        """
        return await self.fetch(conversation_id)
    
    async def list(
        self,
        project_id: str,
        cursor: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        列出对话（原项目方法名：list）
        List conversations for project
        严格复刻原项目：使用_id作为游标，使用projection只返回部分字段
        
        Args:
            project_id: 项目ID
            cursor: 分页游标（ObjectId字符串）
            limit: 返回的最大记录数（默认50）
            
        Returns:
            包含items和nextCursor的字典
            items是ListedConversationItem（只包含id, projectId, createdAt, updatedAt, reason）
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 构建查询条件
        query: Dict[str, Any] = {"projectId": project_id}
        
        # 如果有游标，添加游标条件（使用_id）
        if cursor:
            try:
                query["_id"] = {"$lt": ObjectId(cursor)}
            except Exception:
                # ObjectId格式错误，忽略游标
                pass
        
        # 查询数据库（多取1条以判断是否有下一页）
        # 使用projection只返回部分字段（原项目ListedConversationItem）
        cursor_obj = collection.find(query).sort("_id", -1).limit(limit + 1)
        
        # 转换为列表
        results = []
        async for doc in cursor_obj:
            results.append(doc)
        
        # 判断是否有下一页
        has_next_page = len(results) > limit
        items_docs = results[:limit]
        
        # 转换为ListedConversationItem（只包含部分字段）
        items = []
        for doc in items_docs:
            _id = doc.pop("_id")
            # 只保留ListedConversationItem的字段：id, projectId, createdAt, updatedAt, reason
            item = {
                "id": str(_id),
                "projectId": doc.get("projectId"),
                "createdAt": doc.get("createdAt"),
                "updatedAt": doc.get("updatedAt"),
                "reason": doc.get("reason"),
            }
            items.append(item)
        
        # 返回nextCursor（最后一个结果的_id）
        next_cursor = None
        if has_next_page and items:
            # 使用最后一个结果的_id作为nextCursor
            next_cursor = str(results[limit - 1]["_id"])
        
        return {
            "items": items,
            "nextCursor": next_cursor
        }
    
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
    
    async def add_turn(self, conversation_id: str, turn_data: Dict[str, Any]) -> Turn:
        """
        向对话添加轮次（原项目方法名：addTurn）
        Add a turn to conversation
        严格复刻原项目：使用_id查询，返回创建的Turn对象
        
        Args:
            conversation_id: 对话ID（ObjectId字符串）
            turn_data: 轮次数据字典（不包含id, createdAt, updatedAt）
            
        Returns:
            创建的Turn对象
        """
        import uuid
        
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 创建turn对象（原项目使用nanoid生成id）
        # 注意：Python中没有nanoid，我们使用uuid生成id
        turn_id = str(uuid.uuid4())
        now = datetime.now()
        
        turn = {
            **turn_data,
            "id": turn_id,
            "createdAt": now.isoformat(),
        }
        
        # 更新数据库（添加到turns数组，使用_id）
        try:
            await collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"turns": turn},
                    "$set": {"updatedAt": now.isoformat()}
                }
            )
        except Exception:
            # ObjectId格式错误
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
        
        # 返回创建的Turn对象
        return Turn(**turn)
    
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

