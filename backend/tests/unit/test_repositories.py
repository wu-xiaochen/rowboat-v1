"""
Repository层测试
Tests for Repository layer
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.repositories.projects import ProjectsRepository
from app.repositories.conversations import ConversationsRepository
from app.models.schemas import (
    Project,
    Conversation,
    Turn,
    Workflow,
    Reason,
    ReasonType,
    Message,
    UserMessage,
)


@pytest.fixture
def sample_workflow():
    """创建示例工作流"""
    return Workflow(
        agents=[],
        prompts=[],
        tools=[],
        pipelines=[],
    )


@pytest.fixture
def sample_project(sample_workflow):
    """创建示例项目"""
    return Project(
        id=str(uuid.uuid4()),
        name="测试项目",
        createdAt=datetime.now(),
        createdByUserId="user123",
        secret="secret123",
        draftWorkflow=sample_workflow,
        liveWorkflow=sample_workflow,
    )


@pytest.fixture
def sample_conversation(sample_workflow):
    """创建示例对话"""
    return Conversation(
        id="conv123",
        projectId="proj123",
        workflow=sample_workflow,
        reason=Reason(type=ReasonType.USER_MESSAGE),
        isLiveWorkflow=True,
        createdAt=datetime.now(),
    )


class TestProjectsRepository:
    """ProjectsRepository测试"""
    
    @pytest.mark.asyncio
    async def test_create_project(self, sample_project):
        """测试：创建项目"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.create(sample_project)
            
            assert result is not None
            assert result.id == sample_project.id
            assert result.name == sample_project.name
            
            # 验证insert_one被调用
            mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, sample_project):
        """测试：根据ID获取项目（成功）"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            project_dict = sample_project.model_dump(by_alias=True)
            mock_collection.find_one = AsyncMock(return_value=project_dict)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.get_by_id(sample_project.id)
            
            assert result is not None
            assert result.id == sample_project.id
            assert result.name == sample_project.name
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """测试：根据ID获取项目（不存在）"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.get_by_id("non_existent_id")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self, sample_project):
        """测试：根据用户ID获取项目列表"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            project_dict = sample_project.model_dump(by_alias=True)
            
            # Mock cursor
            mock_cursor = AsyncMock()
            mock_cursor.__aiter__.return_value = [project_dict]
            
            mock_collection = AsyncMock()
            mock_collection.find = MagicMock(return_value=mock_cursor)
            mock_cursor.sort = MagicMock(return_value=mock_cursor)
            mock_cursor.skip = MagicMock(return_value=mock_cursor)
            mock_cursor.limit = MagicMock(return_value=mock_cursor)
            
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            results = await repo.get_by_user_id("user123")
            
            assert len(results) > 0
            assert results[0].created_by_user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_update_project(self, sample_project):
        """测试：更新项目"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_result = MagicMock(matched_count=1)
            mock_collection.update_one = AsyncMock(return_value=mock_result)
            
            # Mock get_by_id
            updated_project = sample_project.model_copy()
            updated_project.name = "更新后的项目"
            project_dict = updated_project.model_dump(by_alias=True)
            mock_collection.find_one = AsyncMock(return_value=project_dict)
            
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.update(sample_project.id, updated_project)
            
            assert result is not None
            assert result.name == "更新后的项目"
    
    @pytest.mark.asyncio
    async def test_delete_project(self, sample_project):
        """测试：删除项目"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_result = MagicMock(deleted_count=1)
            mock_collection.delete_one = AsyncMock(return_value=mock_result)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.delete(sample_project.id)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_exists(self):
        """测试：检查项目是否存在"""
        repo = ProjectsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.projects.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.count_documents = AsyncMock(return_value=1)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.exists("proj123")
            
            assert result is True


class TestConversationsRepository:
    """ConversationsRepository测试"""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, sample_conversation):
        """测试：创建对话"""
        repo = ConversationsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.conversations.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.create(sample_conversation)
            
            assert result is not None
            assert result.id == sample_conversation.id
            assert result.project_id == sample_conversation.project_id
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, sample_conversation):
        """测试：根据ID获取对话"""
        repo = ConversationsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.conversations.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            conversation_dict = sample_conversation.model_dump(by_alias=True)
            mock_collection.find_one = AsyncMock(return_value=conversation_dict)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.get_by_id(sample_conversation.id)
            
            assert result is not None
            assert result.id == sample_conversation.id
    
    @pytest.mark.asyncio
    async def test_get_by_project_id(self, sample_conversation):
        """测试：根据项目ID获取对话列表"""
        repo = ConversationsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.conversations.get_mongodb_db") as mock_db:
            conversation_dict = sample_conversation.model_dump(by_alias=True)
            
            # Mock cursor
            mock_cursor = AsyncMock()
            mock_cursor.__aiter__.return_value = [conversation_dict]
            
            mock_collection = AsyncMock()
            mock_collection.find = MagicMock(return_value=mock_cursor)
            mock_cursor.sort = MagicMock(return_value=mock_cursor)
            mock_cursor.skip = MagicMock(return_value=mock_cursor)
            mock_cursor.limit = MagicMock(return_value=mock_cursor)
            
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            results = await repo.get_by_project_id("proj123")
            
            assert len(results) > 0
            assert results[0].project_id == "proj123"
    
    @pytest.mark.asyncio
    async def test_add_turn(self, sample_conversation):
        """测试：向对话添加轮次"""
        repo = ConversationsRepository()
        
        # 创建示例轮次
        turn = Turn(
            id="turn123",
            conversationId="conv123",
            messages=[
                UserMessage(role="user", content="Hello")
            ],
            createdAt=datetime.now(),
        )
        
        # Mock数据库操作
        with patch("app.repositories.conversations.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_result = MagicMock(matched_count=1)
            mock_collection.update_one = AsyncMock(return_value=mock_result)
            
            # Mock get_by_id
            conversation_dict = sample_conversation.model_dump(by_alias=True)
            conversation_dict["turns"] = [turn.model_dump(by_alias=True)]
            mock_collection.find_one = AsyncMock(return_value=conversation_dict)
            
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.add_turn("conv123", turn)
            
            assert result is not None
            assert result.turns is not None
            assert len(result.turns) > 0
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """测试：删除对话"""
        repo = ConversationsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.conversations.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_result = MagicMock(deleted_count=1)
            mock_collection.delete_one = AsyncMock(return_value=mock_result)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.delete("conv123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_count_by_project_id(self):
        """测试：统计项目的对话数量"""
        repo = ConversationsRepository()
        
        # Mock数据库操作
        with patch("app.repositories.conversations.get_mongodb_db") as mock_db:
            mock_collection = AsyncMock()
            mock_collection.count_documents = AsyncMock(return_value=5)
            mock_db.return_value.__getitem__ = MagicMock(return_value=mock_collection)
            
            result = await repo.count_by_project_id("proj123")
            
            assert result == 5

