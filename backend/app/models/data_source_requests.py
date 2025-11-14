"""
数据源请求模型
Data Source request models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.schemas import DataSourceType, DataSourceStatus


class DataSourceCreateRequest(BaseModel):
    """数据源创建请求模型（严格复刻原项目CreateSchema）"""
    name: str = Field(..., description="数据源名称")
    description: str = Field(..., description="数据源描述")
    data: Dict[str, Any] = Field(..., description="数据源数据（包含type字段）")
    status: Optional[DataSourceStatus] = Field(None, description="数据源状态（可选，文件类型不能设置）")
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class DataSourceUpdateRequest(BaseModel):
    """数据源更新请求模型（严格复刻原项目UpdateSchema：只允许更新description）"""
    description: Optional[str] = Field(None, description="数据源描述（唯一可更新字段）")
    
    class Config:
        populate_by_name = True


class DataSourceToggleRequest(BaseModel):
    """数据源切换状态请求模型"""
    active: bool = Field(..., description="是否激活")
    
    class Config:
        populate_by_name = True

