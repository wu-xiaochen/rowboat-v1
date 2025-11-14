# 脚本目录说明

本目录包含项目开发和维护相关的工具脚本。

## 🚀 常用脚本

### 服务管理
- **start_services.sh** - 启动所有服务（数据库、后端、前端）
- **wait_for_services.sh** - 等待服务启动完成

### 测试脚本
- **run_all_tests.sh** - 运行所有测试
- **run_basic_tests.sh** - 运行基础测试
- **run_tests_with_services.sh** - 在服务环境下运行测试
- **quick_test.sh** - 快速测试

### 清理和维护
- **cleanup.sh** - 清理项目缓存和临时文件
- **cleanup_docs.sh** - 清理过期的文档文件
- **cleanup-env-config.sh** - 清理环境配置

### 日志查看
- **view_backend_logs.sh** - 查看后端日志
- **view_copilot_logs.sh** - 查看Copilot日志
- **monitor_logs.sh** - 监控日志

### 开发和调试
- **check_legacy_code.sh** - 检查遗留代码
- **test_api_manually.sh** - 手动测试API
- **test_copilot_api.sh** - 测试Copilot API

## 📝 脚本使用说明

所有脚本都可以直接执行：

```bash
# 给脚本添加执行权限（如果需要）
chmod +x scripts/script_name.sh

# 执行脚本
./scripts/script_name.sh
```

## ⚠️ 注意事项

- 某些脚本可能需要特定的环境配置
- 测试脚本需要确保相关服务已启动
- 清理脚本会删除缓存和临时文件，请谨慎使用

