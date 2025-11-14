"""
任务数据访问层
Jobs Repository for database operations
严格复刻原项目实现：使用MongoDB ObjectId作为_id
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.core.database import get_mongodb_db
from app.models.schemas import Job, JobStatus


class JobsRepository:
    """
    任务数据访问类
    Repository for Job CRUD operations
    """
    
    def __init__(self):
        """初始化Repository"""
        self.collection_name = "jobs"
    
    async def fetch(self, job_id: str) -> Optional[Job]:
        """
        根据ID获取任务（原项目方法名：fetch）
        Fetch job by ID
        严格复刻原项目：使用_id查询，然后转换为字符串id
        
        Args:
            job_id: 任务ID（ObjectId字符串）
            
        Returns:
            任务对象，如果不存在则返回None
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 从数据库查询（使用_id）
        try:
            doc = await collection.find_one({"_id": ObjectId(job_id)})
        except Exception:
            # ObjectId格式错误
            return None
        
        if doc is None:
            return None
        
        # 移除_id，添加id字段（_id转换为字符串）
        _id = doc.pop("_id")
        doc["id"] = str(_id)
        
        # 转换为Pydantic模型
        return Job(**doc)
    
    async def list(
        self,
        project_id: str,
        filters: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        列出任务（原项目方法名：list）
        List jobs for project
        严格复刻原项目：使用_id作为游标，使用projection只返回部分字段
        
        Args:
            project_id: 项目ID
            filters: 过滤条件（status, recurringJobRuleId, composioTriggerDeploymentId, createdAfter, createdBefore）
            cursor: 分页游标（ObjectId字符串）
            limit: 返回的最大记录数（默认50，最多50）
            
        Returns:
            包含items和nextCursor的字典
            items是ListedJobItem（只包含id, projectId, status, reason, createdAt, updatedAt）
        """
        db = await get_mongodb_db()
        collection = db[self.collection_name]
        
        # 构建查询条件
        query: Dict[str, Any] = {"projectId": project_id}
        
        # 应用过滤条件（原项目JobFiltersSchema）
        if filters:
            if "status" in filters:
                query["status"] = filters["status"]
            
            if "recurringJobRuleId" in filters:
                query["reason.type"] = "recurring_job_rule"
                query["reason.ruleId"] = filters["recurringJobRuleId"]
            
            if "composioTriggerDeploymentId" in filters:
                query["reason.type"] = "composio_trigger"
                query["reason.triggerDeploymentId"] = filters["composioTriggerDeploymentId"]
            
            # 处理日期范围（需要合并条件）
            if "createdAfter" in filters or "createdBefore" in filters:
                date_query: Dict[str, Any] = {}
                if "createdAfter" in filters:
                    date_query["$gte"] = filters["createdAfter"]
                if "createdBefore" in filters:
                    date_query["$lte"] = filters["createdBefore"]
                query["createdAt"] = date_query
        
        # 如果有游标，添加游标条件（使用_id）
        if cursor:
            try:
                query["_id"] = {"$lt": ObjectId(cursor)}
            except Exception:
                # ObjectId格式错误，忽略游标
                pass
        
        # 限制最多50条（原项目Math.min(limit, 50)）
        _limit = min(limit, 50)
        
        # 查询数据库（多取1条以判断是否有下一页）
        # 使用projection只返回部分字段（原项目ListedJobItem）
        cursor_obj = collection.find(query).sort("_id", -1).limit(_limit + 1)
        
        # 转换为列表
        results = []
        async for doc in cursor_obj:
            results.append(doc)
        
        # 判断是否有下一页
        has_next_page = len(results) > _limit
        items_docs = results[:_limit]
        
        # 转换为ListedJobItem（只包含部分字段）
        items = []
        for doc in items_docs:
            _id = doc.pop("_id")
            # 只保留ListedJobItem的字段：id, projectId, status, reason, createdAt, updatedAt
            item = {
                "id": str(_id),
                "projectId": doc.get("projectId"),
                "status": doc.get("status"),
                "reason": doc.get("reason"),
                "createdAt": doc.get("createdAt"),
                "updatedAt": doc.get("updatedAt"),
            }
            items.append(item)
        
        # 返回nextCursor（最后一个结果的_id）
        next_cursor = None
        if has_next_page and items:
            # 使用最后一个结果的_id作为nextCursor
            next_cursor = str(results[_limit - 1]["_id"])
        
        return {
            "items": items,
            "nextCursor": next_cursor
        }

