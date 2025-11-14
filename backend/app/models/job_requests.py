"""
任务请求模型
Job request models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.schemas import JobStatus


class JobFiltersRequest(BaseModel):
    """
    任务过滤条件
    Job filters request
    严格复刻原项目JobFiltersSchema
    """
    status: Optional[JobStatus] = None
    recurringJobRuleId: Optional[str] = Field(None, alias="recurringJobRuleId")
    composioTriggerDeploymentId: Optional[str] = Field(None, alias="composioTriggerDeploymentId")
    createdAfter: Optional[str] = Field(None, alias="createdAfter")
    createdBefore: Optional[str] = Field(None, alias="createdBefore")
    
    class Config:
        populate_by_name = True

