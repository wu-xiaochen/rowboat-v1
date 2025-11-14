# 测试运行指南
# Testing Guide with Services

## 概述
本指南说明如何运行测试，确保前后端服务完整运行。

## 测试超时设置
- **测试超时时间**: 60秒（1分钟）
- **配置位置**: `backend/pytest.ini`
- **超时方法**: thread（线程模式）

## 运行测试

### 方法1: 使用测试脚本（推荐）
使用 `scripts/test_with_services.sh` 脚本自动启动前后端服务并运行测试：

```bash
# 运行所有测试
./scripts/test_with_services.sh

# 运行特定测试文件
./scripts/test_with_services.sh tests/test_api_endpoints.py

# 运行特定测试类
./scripts/test_with_services.sh tests/test_api_endpoints.py::TestHealthEndpoints

# 运行特定测试函数
./scripts/test_with_services.sh tests/test_api_endpoints.py::TestHealthEndpoints::test_health_check
```

### 方法2: 手动启动服务
如果服务已经在运行，可以直接运行测试：

```bash
cd backend
python -m pytest tests/ -v --tb=short --timeout=60 --timeout-method=thread
```

### 方法3: 仅运行后端测试（不需要前端服务）
后端API测试使用 `ASGITransport`，不需要实际运行后端服务：

```bash
cd backend
python -m pytest tests/ -v --tb=short --timeout=60 --timeout-method=thread
```

## 服务配置

### 后端服务
- **端口**: 8001
- **健康检查**: `http://localhost:8001/api/v1/health`
- **启动命令**: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8001`

### 前端服务
- **端口**: 3001
- **健康检查**: `http://localhost:3001`
- **启动命令**: `npm run dev` (在 `apps/rowboat` 目录)

## 测试类型

### 1. 单元测试
- **位置**: `backend/tests/unit/`
- **特点**: 不依赖外部服务，使用 mock
- **运行**: `pytest tests/unit/ -v`

### 2. 集成测试
- **位置**: `backend/tests/integration/`
- **特点**: 可能需要数据库连接，使用 `ASGITransport` 测试 API
- **运行**: `pytest tests/integration/ -v`

### 3. API端点测试
- **位置**: `backend/tests/test_api_endpoints.py`
- **特点**: 使用 `ASGITransport` 直接测试 FastAPI 应用
- **运行**: `pytest tests/test_api_endpoints.py -v`

## 测试超时配置

### pytest.ini 配置
```ini
[pytest]
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --timeout=60
    --timeout-method=thread
```

### 测试中的超时设置
- **AsyncClient 超时**: 30秒
- **测试超时**: 60秒（pytest-timeout）
- **连接超时**: 5秒（MongoDB）

## 常见问题

### 1. 测试超时
如果测试超时，检查：
- 网络连接是否正常
- 数据库服务是否运行
- Mock 是否正确设置

### 2. 服务启动失败
检查：
- 端口是否被占用
- 环境变量是否配置正确
- 依赖是否安装完整

### 3. 数据库连接失败
单元测试应该使用 mock，不依赖实际数据库。如果集成测试需要数据库：
- 确保 MongoDB 服务运行
- 检查连接字符串配置
- 使用测试数据库（非生产数据库）

## 测试覆盖率

运行测试覆盖率报告：

```bash
cd backend
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

查看 HTML 报告：

```bash
open htmlcov/index.html
```

## 持续集成

在 CI/CD 环境中运行测试：

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt

# 运行测试
pytest tests/ -v --tb=short --timeout=60 --timeout-method=thread

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=xml
```

## 注意事项

1. **测试环境变量**: 测试使用测试环境变量，不会影响生产环境
2. **数据库隔离**: 单元测试使用 mock，不操作实际数据库
3. **服务清理**: 测试脚本会自动清理启动的服务
4. **超时设置**: 所有测试必须在60秒内完成
5. **异步测试**: 使用 `pytest-asyncio` 处理异步测试

## 参考文档

- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-timeout 文档](https://pytest-timeout.readthedocs.io/)
- [httpx 文档](https://www.python-httpx.org/)

