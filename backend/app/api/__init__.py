"""
API模块
API module
"""

from typing import Any, Dict


class ResponseModel:
    """
    统一响应模型
    Unified response model for all API endpoints
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict:
        """
        成功响应
        Success response
        
        Args:
            data: 响应数据
            message: 成功消息
            
        Returns:
            统一格式的响应字典
        """
        return {
            "success": True,
            "data": data,
            "message": message,
        }
    
    @staticmethod
    def error(
        code: str = "ERROR",
        message: str = "操作失败",
        details: Any = None
    ) -> Dict:
        """
        错误响应
        Error response
        
        Args:
            code: 错误代码
            message: 错误消息
            details: 错误详情
            
        Returns:
            统一格式的错误响应字典
        """
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        }

