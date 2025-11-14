"""
数据源数据访问层
Data Sources Repository for database operations
严格复刻原项目实现：使用MongoDB ObjectId作为_id，集合名为"sources"
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.core.database import get_mongodb_db
from app.core.cache import get_cache_service
from app.models.schemas import DataSource, DataSourceStatus


class DataSourcesRepository:
    """
    数据源数据访问类
    Repository for DataSource CRUD operations
    严格复刻原项目：mongodb.data-sources.repository.ts
    """
    
    def __init__(self):
        """初始化Repository"""
        self.collection_name = "sources"  # 原项目使用"sources"，不是"dataSources"
        self.cache_service = get_cache_service()
        self.cache_ttl = 300  # 缓存5分钟
    
    async def create(self, data: Dict[str, Any]) -> DataSource:
        """
        创建数据源
        Create a new data source
        严格复刻原项目：使用ObjectId作为_id，然后转换为字符串id
        
        Args:
            data: 数据源数据字典（包含projectId, name, description, data, status）
            
        Returns:
            创建的数据源对象
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 生成ObjectId
        _id = ObjectId()
        
        # 构建文档（排除id字段，因为使用_id）
        now = datetime.now().isoformat()
        doc = {
            **data,
            "active": True,
            "attempts": 0,
            "version": 1,
            "createdAt": now,
            "error": None,
            "billingError": None,
            "lastAttemptAt": None,
            "lastUpdatedAt": None,
        }
        
        # 插入数据库（使用_id）
        await collection.insert_one({**doc, "_id": _id})
        
        # 返回时添加id字段（_id转换为字符串）
        return DataSource(**{**doc, "id": str(_id)})
    
    async def fetch(self, source_id: str) -> Optional[DataSource]:
        """
        根据ID获取数据源（原项目方法名：fetch）
        Fetch data source by ID
        严格复刻原项目：使用_id查询，然后转换为字符串id
        
        Args:
            source_id: 数据源ID（ObjectId字符串）
            
        Returns:
            数据源对象，如果不存在则返回None
        """
        # 尝试从缓存获取
        cache_key = self.cache_service.get_data_source_key(source_id)
        cached_source = await self.cache_service.get(cache_key)
        if cached_source:
            try:
                return DataSource(**cached_source)
            except Exception:
                # 缓存数据格式错误，继续从数据库查询
                pass
        
        # 从数据库查询（使用_id）
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        try:
            doc = await collection.find_one({"_id": ObjectId(source_id)})
        except Exception:
            # ObjectId格式错误
            return None
        
        if doc is None:
            return None
        
        # 移除_id，添加id字段（_id转换为字符串）
        _id = doc.pop("_id")
        doc["id"] = str(_id)
        
        # 转换为Pydantic模型
        data_source = DataSource(**doc)
        
        # 存入缓存
        data_source_dict = data_source.model_dump(by_alias=True)
        await self.cache_service.set(cache_key, data_source_dict, self.cache_ttl)
        
        return data_source
    
    async def get_by_id(self, source_id: str) -> Optional[DataSource]:
        """
        根据ID获取数据源（别名方法，调用fetch）
        Get data source by ID (alias for fetch)
        """
        return await self.fetch(source_id)
    
    async def list(
        self,
        project_id: str,
        filters: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        列出数据源
        List data sources
        严格复刻原项目：默认排除deleted，使用_id作为游标，限制最多50条
        
        Args:
            project_id: 项目ID
            filters: 过滤条件（active, deleted）
            cursor: 分页游标（ObjectId字符串）
            limit: 返回的最大记录数（默认50，最多50）
            
        Returns:
            包含items和nextCursor的字典
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 构建查询条件（默认排除deleted）
        query: Dict[str, Any] = {
            "projectId": project_id,
            "status": {"$ne": "deleted"}  # 默认排除deleted
        }
        
        # 如果明确要求deleted，则只查询deleted
        if filters and filters.get("deleted") is True:
            query["status"] = "deleted"
        
        # 添加active过滤
        if filters and "active" in filters and isinstance(filters["active"], bool):
            query["active"] = filters["active"]
        
        # 如果有游标，添加游标条件（使用_id）
        if cursor:
            try:
                query["_id"] = {"$lt": ObjectId(cursor)}
            except Exception:
                # ObjectId格式错误，忽略游标
                pass
        
        # 限制最多50条
        _limit = min(limit, 50)
        
        # 查询数据库（多取1条以判断是否有下一页）
        cursor_obj = collection.find(query).sort("_id", -1).limit(_limit + 1)
        
        # 转换为Pydantic模型列表
        results = []
        async for doc in cursor_obj:
            results.append(doc)
        
        # 判断是否有下一页
        has_next_page = len(results) > _limit
        items_docs = results[:_limit]
        
        # 转换为Pydantic模型
        items = []
        for doc in items_docs:
            _id = doc.pop("_id")
            doc["id"] = str(_id)
            try:
                items.append(DataSource(**doc))
            except Exception:
                # 跳过格式错误的数据
                continue
        
        # 返回nextCursor（最后一个结果的_id）
        next_cursor = None
        if has_next_page and items:
            # 使用最后一个结果的_id作为nextCursor
            next_cursor = str(results[_limit - 1]["_id"])
        
        return {
            "items": items,
            "nextCursor": next_cursor
        }
    
    async def update(
        self,
        source_id: str,
        data: Dict[str, Any],
        bump_version: bool = False
    ) -> Optional[DataSource]:
        """
        更新数据源
        Update a data source
        严格复刻原项目：使用findOneAndUpdate，支持bumpVersion
        
        Args:
            source_id: 数据源ID（ObjectId字符串）
            data: 要更新的字段字典
            bump_version: 是否增加版本号
            
        Returns:
            更新后的数据源对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        now = datetime.now().isoformat()
        
        # 构建更新操作
        update_op: Dict[str, Any] = {
            "$set": {
                **data,
                "lastUpdatedAt": now,
            }
        }
        
        # 如果bumpVersion，增加version
        if bump_version:
            update_op["$inc"] = {"version": 1}
        
        # 使用findOneAndUpdate（原项目使用此方法）
        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(source_id)},
                update_op,
                return_document=True  # 返回更新后的文档
            )
        except Exception:
            # ObjectId格式错误
            return None
        
        if result is None:
            return None
        
        # 移除_id，添加id字段
        _id = result.pop("_id")
        result["id"] = str(_id)
        
        # 清除缓存
        cache_key = self.cache_service.get_data_source_key(source_id)
        await self.cache_service.delete(cache_key)
        
        # 转换为Pydantic模型
        return DataSource(**result)
    
    async def delete(self, source_id: str) -> bool:
        """
        删除数据源（硬删除：真正的deleteOne）
        Delete a data source (hard delete: actual deleteOne)
        注意：Use Case中会先调用update设置status为deleted，这里实现硬删除方法
        
        Args:
            source_id: 数据源ID（ObjectId字符串）
            
        Returns:
            是否删除成功
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 硬删除（原项目Repository的delete方法是硬删除）
        try:
            result = await collection.delete_one({"_id": ObjectId(source_id)})
        except Exception:
            # ObjectId格式错误
            return False
        
        if result.deleted_count > 0:
            # 清除缓存
            cache_key = self.cache_service.get_data_source_key(source_id)
            await self.cache_service.delete(cache_key)
        
        return result.deleted_count > 0
    
    async def exists(self, source_id: str) -> bool:
        """
        检查数据源是否存在
        Check if data source exists
        
        Args:
            source_id: 数据源ID（ObjectId字符串）
            
        Returns:
            是否存在
        """
        try:
            db = await get_mongodb_db()
            collection = db[self.collection_name]
            count = await collection.count_documents({"_id": ObjectId(source_id)}, limit=1)
            return count > 0
        except Exception:
            return False

