"""
数据源管理功能集成测试
Integration tests for Data Sources management endpoints
严格复刻原项目逻辑的测试
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from app.main import app
from app.models.schemas import DataSource, DataSourceStatus, DataSourceType, DataSourceData
# 不再直接导入Repository，使用patch路径


@pytest.mark.asyncio
async def test_create_data_source_success():
    """测试创建数据源成功"""
    # Mock Repository
    mock_source_id = str(ObjectId())
    mock_data_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.PENDING,
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.create = AsyncMock(return_value=mock_data_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.post(
                "/api/v1/test_project_id/data-sources",
                json={
                    "name": "测试数据源",
                    "description": "测试描述",
                    "data": {"type": "urls"},
                    "status": "pending",
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "测试数据源"
        assert data["data"]["description"] == "测试描述"
        assert data["data"]["projectId"] == "test_project_id"
        assert data["data"]["status"] == "pending"
        assert "id" in data["data"]
        
        # 验证Repository被调用
        mock_repo_instance.create.assert_called_once()
        call_args = mock_repo_instance.create.call_args[0][0]
        assert call_args["name"] == "测试数据源"
        assert call_args["projectId"] == "test_project_id"


@pytest.mark.asyncio
async def test_create_data_source_file_type_no_status():
    """测试创建文件类型数据源时不能设置status"""
    # Mock Repository
    mock_source_id = str(ObjectId())
    mock_data_source = DataSource(
        id=mock_source_id,
        name="文件数据源",
        description="文件描述",
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.PENDING,  # 文件类型强制为pending
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.FILES_LOCAL),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.create = AsyncMock(return_value=mock_data_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            # 即使请求中设置了status，文件类型也会被强制为pending
            response = await ac.post(
                "/api/v1/test_project_id/data-sources",
                json={
                    "name": "文件数据源",
                    "description": "文件描述",
                    "data": {"type": "files_local"},
                    "status": "ready",  # 这个应该被忽略
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 文件类型应该强制为pending
        assert data["data"]["status"] == "pending"
        
        # 验证Repository被调用时status是pending
        mock_repo_instance.create.assert_called_once()
        call_args = mock_repo_instance.create.call_args[0][0]
        assert call_args["status"] == "pending"


@pytest.mark.asyncio
async def test_list_data_sources_success():
    """测试获取数据源列表成功"""
    # Mock Repository
    mock_sources = [
        DataSource(
            id=str(ObjectId()),
            name=f"数据源{i}",
            description=f"描述{i}",
            projectId="test_project_id",
            active=True,
            status=DataSourceStatus.READY,
            version=1,
            error=None,
            billingError=None,
            createdAt=datetime.now(),
            lastUpdatedAt=None,
            attempts=0,
            lastAttemptAt=None,
            data=DataSourceData(type=DataSourceType.URLS),
        )
        for i in range(3)
    ]
    
    # Mock list方法返回分页结果
    mock_list_result = {
        "items": mock_sources,
        "nextCursor": None,  # 没有下一页
    }
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/data-sources"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)  # 原项目返回数组
        assert len(data["data"]) == 3
        assert data["data"][0]["name"] == "数据源0"
        
        # 验证Repository被调用
        mock_repo_instance.list.assert_called_once()
        # list方法使用位置参数和关键字参数
        call_args = mock_repo_instance.list.call_args
        assert call_args[0][0] == "test_project_id"  # 第一个位置参数是project_id
        if len(call_args[1]) > 0:
            assert call_args[1].get("filters", {}) == {}  # 默认无过滤


@pytest.mark.asyncio
async def test_list_data_sources_with_filters():
    """测试带过滤条件的数据源列表"""
    # Mock Repository
    mock_sources = [
        DataSource(
            id=str(ObjectId()),
            name="激活的数据源",
            description="描述",
            projectId="test_project_id",
            active=True,
            status=DataSourceStatus.READY,
            version=1,
            error=None,
            billingError=None,
            createdAt=datetime.now(),
            lastUpdatedAt=None,
            attempts=0,
            lastAttemptAt=None,
            data=DataSourceData(type=DataSourceType.URLS),
        )
    ]
    
    mock_list_result = {
        "items": mock_sources,
        "nextCursor": None,
    }
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.list = AsyncMock(return_value=mock_list_result)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/data-sources",
                params={"active": True, "deleted": False}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证Repository被调用时传递了过滤条件
        mock_repo_instance.list.assert_called_once()
        call_kwargs = mock_repo_instance.list.call_args[1]
        assert call_kwargs["filters"]["active"] is True
        assert call_kwargs["filters"]["deleted"] is False


@pytest.mark.asyncio
async def test_get_data_source_success():
    """测试获取数据源详情成功"""
    # Mock Repository
    mock_source_id = str(ObjectId())
    mock_data_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.READY,
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=mock_data_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                f"/api/v1/test_project_id/data-sources/{mock_source_id}"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == mock_source_id
        assert data["data"]["name"] == "测试数据源"
        assert data["data"]["projectId"] == "test_project_id"
        
        # 验证Repository被调用
        mock_repo_instance.fetch.assert_called_once_with(mock_source_id)


@pytest.mark.asyncio
async def test_get_data_source_not_found():
    """测试获取不存在的数据源"""
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=None)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                "/api/v1/test_project_id/data-sources/non_existent_id"
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_get_data_source_project_mismatch():
    """测试获取不属于该项目的数据源"""
    mock_source_id = str(ObjectId())
    mock_data_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="other_project_id",  # 不同的项目ID
        active=True,
        status=DataSourceStatus.READY,
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=mock_data_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.get(
                f"/api/v1/test_project_id/data-sources/{mock_source_id}"
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_update_data_source_success():
    """测试更新数据源成功（只更新description）"""
    mock_source_id = str(ObjectId())
    existing_source = DataSource(
        id=mock_source_id,
        name="原名称",
        description="原描述",
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.READY,
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    updated_source = DataSource(
        id=mock_source_id,
        name="原名称",  # 名称不变
        description="新描述",  # 描述更新
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.READY,
        version=2,  # 版本号增加
        error=None,
        billingError=None,
        createdAt=existing_source.created_at,
        lastUpdatedAt=datetime.now(),
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=existing_source)
        mock_repo_instance.update = AsyncMock(return_value=updated_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.put(
                f"/api/v1/test_project_id/data-sources/{mock_source_id}",
                json={
                    "description": "新描述",
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["description"] == "新描述"
        assert data["data"]["version"] == 2  # 版本号增加
        
        # 验证Repository被调用，bumpVersion=True
        mock_repo_instance.update.assert_called_once()
        call_args = mock_repo_instance.update.call_args
        assert call_args[0][0] == mock_source_id
        assert call_args[0][1]["description"] == "新描述"
        # bumpVersion是第三个位置参数
        if len(call_args[0]) > 2:
            assert call_args[0][2] is True  # bumpVersion=True


@pytest.mark.asyncio
async def test_delete_data_source_success():
    """测试删除数据源成功（软删除）"""
    mock_source_id = str(ObjectId())
    existing_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.READY,
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    deleted_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="test_project_id",
        active=True,
        status=DataSourceStatus.DELETED,  # 状态变为deleted
        version=2,  # 版本号增加
        error=None,
        billingError=None,
        createdAt=existing_source.created_at,
        lastUpdatedAt=datetime.now(),
        attempts=0,  # attempts重置为0
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=existing_source)
        mock_repo_instance.update = AsyncMock(return_value=deleted_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.delete(
                f"/api/v1/test_project_id/data-sources/{mock_source_id}"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "删除成功" in data["message"]
        
        # 验证Repository被调用，软删除（update status为deleted）
        mock_repo_instance.update.assert_called_once()
        call_args = mock_repo_instance.update.call_args
        assert call_args[0][0] == mock_source_id
        update_data = call_args[0][1]
        assert update_data["status"] == DataSourceStatus.DELETED
        assert update_data["attempts"] == 0
        assert update_data["billingError"] is None
        # bumpVersion是第三个位置参数
        if len(call_args[0]) > 2:
            assert call_args[0][2] is True  # bumpVersion=True


@pytest.mark.asyncio
async def test_toggle_data_source_success():
    """测试切换数据源状态成功"""
    mock_source_id = str(ObjectId())
    existing_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="test_project_id",
        active=True,  # 当前激活
        status=DataSourceStatus.READY,
        version=1,
        error=None,
        billingError=None,
        createdAt=datetime.now(),
        lastUpdatedAt=None,
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    updated_source = DataSource(
        id=mock_source_id,
        name="测试数据源",
        description="测试描述",
        projectId="test_project_id",
        active=False,  # 切换为禁用
        status=DataSourceStatus.READY,
        version=1,  # 版本号不变（不bumpVersion）
        error=None,
        billingError=None,
        createdAt=existing_source.created_at,
        lastUpdatedAt=datetime.now(),
        attempts=0,
        lastAttemptAt=None,
        data=DataSourceData(type=DataSourceType.URLS),
    )
    
    with patch("app.api.v1.endpoints.data_sources.DataSourcesRepository") as mock_repo_class:
        mock_repo_instance = AsyncMock()
        mock_repo_instance.fetch = AsyncMock(return_value=existing_source)
        mock_repo_instance.update = AsyncMock(return_value=updated_source)
        mock_repo_class.return_value = mock_repo_instance
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0
        ) as ac:
            response = await ac.post(
                f"/api/v1/test_project_id/data-sources/{mock_source_id}/toggle",
                json={
                    "active": False,
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is False
        assert data["data"]["version"] == 1  # 版本号不变
        
        # 验证Repository被调用，不bumpVersion
        mock_repo_instance.update.assert_called_once()
        call_args = mock_repo_instance.update.call_args
        assert call_args[0][0] == mock_source_id
        assert call_args[0][1]["active"] is False
        # bumpVersion是第三个位置参数
        if len(call_args[0]) > 2:
            assert call_args[0][2] is False  # bumpVersion=False

