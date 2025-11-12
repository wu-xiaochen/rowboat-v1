"""
API Key数据访问层
API Keys Repository for database operations
"""

from typing import List, Optional
from datetime import datetime

from app.core.database import get_mongodb_db
from app.models.api_key import APIKey


class APIKeysRepository:
    """
    API Key数据访问类
    Repository for API Key CRUD operations
    """
    
    def __init__(self):
        """初始化Repository"""
        self.collection_name = "api_keys"
    
    async def create(self, api_key: APIKey) -> APIKey:
        """
        创建API Key
        Create a new API key
        
        Args:
            api_key: API Key对象
            
        Returns:
            创建的API Key对象
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 转换为字典，准备插入数据库
        api_key_dict = api_key.model_dump(by_alias=True, exclude={"id"})
        
        # 插入数据库
        await collection.insert_one(api_key_dict)
        
        return api_key
    
    async def get_by_id(self, key_id: str) -> Optional[APIKey]:
        """
        根据ID获取API Key
        Get API key by ID
        
        Args:
            key_id: API Key ID
            
        Returns:
            API Key对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        doc = await collection.find_one({"id": key_id})
        
        if doc is None:
            return None
        
        if "_id" in doc:
            del doc["_id"]
        
        return APIKey(**doc)
    
    async def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        """
        根据Key哈希获取API Key
        Get API key by key hash
        
        Args:
            key_hash: API Key哈希值
            
        Returns:
            API Key对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        doc = await collection.find_one({"key": key_hash, "isActive": True})
        
        if doc is None:
            return None
        
        if "_id" in doc:
            del doc["_id"]
        
        return APIKey(**doc)
    
    async def get_by_project_id(self, project_id: str) -> List[APIKey]:
        """
        根据项目ID获取所有API Key
        Get all API keys for a project
        
        Args:
            project_id: 项目ID
            
        Returns:
            API Key列表
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        cursor = collection.find({"projectId": project_id}).sort("createdAt", -1)
        
        api_keys = []
        async for doc in cursor:
            if "_id" in doc:
                del doc["_id"]
            api_keys.append(APIKey(**doc))
        
        return api_keys
    
    async def update_last_used(self, key_id: str) -> bool:
        """
        更新API Key的最后使用时间
        Update the last used timestamp of an API key
        
        Args:
            key_id: API Key ID
            
        Returns:
            是否更新成功
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        result = await collection.update_one(
            {"id": key_id},
            {"$set": {"lastUsedAt": datetime.now()}}
        )
        
        return result.matched_count > 0
    
    async def deactivate(self, key_id: str) -> bool:
        """
        停用API Key
        Deactivate an API key
        
        Args:
            key_id: API Key ID
            
        Returns:
            是否停用成功
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        result = await collection.update_one(
            {"id": key_id},
            {"$set": {"isActive": False}}
        )
        
        return result.matched_count > 0
    
    async def delete(self, key_id: str) -> bool:
        """
        删除API Key
        Delete an API key
        
        Args:
            key_id: API Key ID
            
        Returns:
            是否删除成功
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        result = await collection.delete_one({"id": key_id})
        
        return result.deleted_count > 0

