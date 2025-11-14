"""
对话管理功能集成测试
Integration tests for Conversations management endpoints
严格复刻原项目逻辑的测试
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime
from bson import ObjectId

from app.main import app
from app.models.schemas import Conversation, Workflow


@pytest.mark.asyncio
async def test_list_conversations_success():
    """测试获取对话列表成功"""
    # Mock Repository
    mock_conversations = [
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": None,
            "reason": {"type": "chat"},
        },
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": None,
            "reason": {"type": "api"},
        },
    ]
    
    mock_list_result = {
        "items": mock_conversations,
        "nextCursor": None,
    }
    
    with patch("app.api.v1.endpoints.conversations.ConversationsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/conversations"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "nextCursor" in data["data"]
        assert len(data["data"]["items"]) == 2
        assert data["data"]["items"][0]["reason"]["type"] == "chat"
        
        # 验证Repository被调用
        mock_repo_instance.list.assert_called_once()
        call_args = mock_repo_instance.list.call_args
        assert call_args[0][0] == "test_project_id"  # 第一个位置参数是project_id


@pytest.mark.asyncio
async def test_list_conversations_with_cursor():
    """测试带游标的对话列表"""
    # Mock Repository
    mock_conversations = [
        {
            "id": str(ObjectId()),
            "projectId": "test_project_id",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": None,
            "reason": {"type": "chat"},
        }
    ]
    
    mock_list_result = {
        "items": mock_conversations,
        "nextCursor": str(ObjectId()),
    }
    
    with patch("app.api.v1.endpoints.conversations.ConversationsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        cursor = str(ObjectId())
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/conversations",
                params={"cursor": cursor, "limit": 50}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["nextCursor"] is not None
        
        # 验证Repository被调用时传递了cursor
        mock_repo_instance.list.assert_called_once()
        call_args = mock_repo_instance.list.call_args
        assert call_args[0][0] == "test_project_id"
        assert call_args[1]["cursor"] == cursor


@pytest.mark.asyncio
async def test_get_conversation_success():
    """测试获取对话详情成功"""
    # Mock Repository
    mock_conversation_id = str(ObjectId())
    mock_conversation = Conversation(
        id=mock_conversation_id,
        projectId="test_project_id",
        workflow=Workflow(
            agents=[],
            prompts=[],
            tools=[],
            pipelines=[],
            start_agent_name=None,
        ),
        reason={"type": "chat"},
        isLiveWorkflow=True,
        createdAt=datetime.now(),
        updatedAt=None,
        turns=None,
    )
    
    with patch("app.api.v1.endpoints.conversations.ConversationsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=mock_conversation)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                f"/api/v1/test_project_id/conversations/{mock_conversation_id}"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == mock_conversation_id
        assert data["data"]["projectId"] == "test_project_id"
        assert data["data"]["reason"]["type"] == "chat"
        
        # 验证Repository被调用
        mock_repo_instance.fetch.assert_called_once_with(mock_conversation_id)


@pytest.mark.asyncio
async def test_get_conversation_not_found():
    """测试获取不存在的对话"""
    with patch("app.api.v1.endpoints.conversations.ConversationsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=None)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/conversations/non_existent_id"
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_get_conversation_project_mismatch():
    """测试获取不属于该项目的对话"""
    mock_conversation_id = str(ObjectId())
    mock_conversation = Conversation(
        id=mock_conversation_id,
        projectId="other_project_id",  # 不同的项目ID
        workflow=Workflow(
            agents=[],
            prompts=[],
            tools=[],
            pipelines=[],
            start_agent_name=None,
        ),
        reason={"type": "chat"},
        isLiveWorkflow=True,
        createdAt=datetime.now(),
        updatedAt=None,
        turns=None,
    )
    
    with patch("app.api.v1.endpoints.conversations.ConversationsRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=mock_conversation)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                f"/api/v1/test_project_id/conversations/{mock_conversation_id}"
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

