"""
项目数据访问层
Projects Repository for database operations
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_mongodb_db
from app.core.cache import get_cache_service
from app.models.schemas import Project


class ProjectsRepository:
    """
    项目数据访问类
    Repository for Project CRUD operations
    """
    
    def __init__(self):
        """初始化Repository"""
        self.collection_name = "projects"
        self.cache_service = get_cache_service()
        self.cache_ttl = 300  # 缓存5分钟
    
    async def create(self, project: Project) -> Project:
        """
        创建项目（带缓存）
        Create a new project (with cache)
        
        Args:
            project: 项目对象
            
        Returns:
            创建的项目对象
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 转换为字典，准备插入数据库
        project_dict = project.model_dump(by_alias=True, exclude={"id"})
        
        # 插入数据库
        result = await collection.insert_one(project_dict)
        
        # 返回创建的项目（带生成的ID）
        created_project = project.model_copy()
        
        # 存入缓存
        cache_key = self.cache_service.get_project_key(created_project.id)
        project_dict_cached = created_project.model_dump(by_alias=True)
        await self.cache_service.set(cache_key, project_dict_cached, self.cache_ttl)
        
        return created_project
    
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """
        根据ID获取项目（带缓存优化）
        Get project by ID (with cache optimization)
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目对象，如果不存在则返回None
        """
        # 尝试从缓存获取
        cache_key = self.cache_service.get_project_key(project_id)
        cached_project = await self.cache_service.get(cache_key)
        if cached_project:
            try:
                return Project(**cached_project)
            except Exception:
                # 缓存数据格式错误，继续从数据库查询
                pass
        
        # 从数据库查询
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 查询数据库（使用投影减少数据传输，排除大型workflow字段）
        doc = await collection.find_one(
            {"id": project_id},
            # 注意：这里不排除workflow，因为需要完整数据
            # 如果workflow很大，可以考虑分页或延迟加载
        )
        
        if doc is None:
            return None
        
        # 移除MongoDB的_id字段
        if "_id" in doc:
            del doc["_id"]
        
        # 转换为Pydantic模型
        project = Project(**doc)
        
        # 存入缓存（转换为字典）
        project_dict = project.model_dump(by_alias=True)
        await self.cache_service.set(cache_key, project_dict, self.cache_ttl)
        
        return project
    
    async def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        根据用户ID获取项目列表
        Get projects by user ID
        
        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            项目列表
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 查询数据库
        cursor = collection.find(
            {"createdByUserId": user_id}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        # 转换为Pydantic模型列表
        projects = []
        async for doc in cursor:
            if "_id" in doc:
                del doc["_id"]
            projects.append(Project(**doc))
        
        return projects
    
    async def update(self, project_id: str, project: Project) -> Optional[Project]:
        """
        更新项目（带缓存失效）
        Update a project (with cache invalidation)
        
        Args:
            project_id: 项目ID
            project: 更新的项目对象
            
        Returns:
            更新后的项目对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 更新lastUpdatedAt字段
        project_dict = project.model_dump(by_alias=True, exclude={"id"})
        project_dict["lastUpdatedAt"] = datetime.now()
        
        # 更新数据库
        result = await collection.update_one(
            {"id": project_id},
            {"$set": project_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        # 清除缓存
        cache_key = self.cache_service.get_project_key(project_id)
        await self.cache_service.delete(cache_key)
        
        # 返回更新后的项目（会重新缓存）
        return await self.get_by_id(project_id)
    
    async def delete(self, project_id: str) -> bool:
        """
        删除项目（带缓存失效）
        Delete a project (with cache invalidation)
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否删除成功
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 删除数据库记录
        result = await collection.delete_one({"id": project_id})
        
        if result.deleted_count > 0:
            # 清除缓存
            cache_key = self.cache_service.get_project_key(project_id)
            await self.cache_service.delete(cache_key)
        
        return result.deleted_count > 0
    
    async def exists(self, project_id: str) -> bool:
        """
        检查项目是否存在
        Check if project exists
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否存在
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        count = await collection.count_documents({"id": project_id}, limit=1)
        return count > 0
    
    async def count_by_user_id(self, user_id: str) -> int:
        """
        统计用户的项目数量
        Count projects by user ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            项目数量
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        return await collection.count_documents({"createdByUserId": user_id})

