# 日志监控指南
# Log Monitoring Guide

**创建日期**：2025-01-27

## 📝 日志文件位置

### 后端日志
- **文件路径**：`/tmp/backend.log`
- **内容**：后端服务运行日志、API请求日志、错误日志

### 前端日志
- **文件路径**：`/tmp/frontend.log`
- **内容**：前端服务运行日志、构建日志、错误日志

## 🔍 监控方式

### 方式1: 使用监控脚本（推荐）

```bash
./scripts/monitor_logs.sh
```

脚本提供交互式菜单，可以选择：
- 监控后端日志（实时）
- 监控前端日志（实时）
- 同时监控后端和前端日志（实时）
- 查看最近日志

### 方式2: 直接使用tail命令

#### 实时监控后端日志
```bash
tail -f /tmp/backend.log
```

#### 实时监控前端日志
```bash
tail -f /tmp/frontend.log
```

#### 同时监控两个日志
```bash
tail -f /tmp/backend.log /tmp/frontend.log
```

### 方式3: 查看最近日志

#### 查看后端最近50行
```bash
tail -50 /tmp/backend.log
```

#### 查看前端最近50行
```bash
tail -50 /tmp/frontend.log
```

#### 查看后端最近100行并高亮错误
```bash
tail -100 /tmp/backend.log | grep -E "(ERROR|error|Error|Exception|Traceback)" --color=always
```

#### 查看前端最近100行并高亮错误
```bash
tail -100 /tmp/frontend.log | grep -E "(ERROR|error|Error|Failed|failed)" --color=always
```

## 🎯 常用监控命令

### 监控后端API请求
```bash
tail -f /tmp/backend.log | grep -E "(GET|POST|PUT|DELETE|/api/)"
```

### 监控后端错误
```bash
tail -f /tmp/backend.log | grep -E "(ERROR|Exception|Traceback|Failed)"
```

### 监控前端构建错误
```bash
tail -f /tmp/frontend.log | grep -E "(error|Error|Failed|failed)"
```

### 带时间戳的监控
```bash
tail -f /tmp/backend.log | while read line; do echo "[$(date '+%H:%M:%S')] $line"; done
```

## 🛑 停止监控

### 停止tail监控
按 `Ctrl+C`

### 停止后台监控进程
```bash
# 查看监控进程
ps aux | grep "tail -f"

# 停止监控进程
kill $(cat /tmp/monitor.pid 2>/dev/null)
```

## 📊 日志分析

### 统计错误数量
```bash
grep -c "ERROR\|Exception\|Traceback" /tmp/backend.log
```

### 查看最近的错误
```bash
grep -E "(ERROR|Exception|Traceback)" /tmp/backend.log | tail -20
```

### 查看API请求统计
```bash
grep -E "(GET|POST|PUT|DELETE)" /tmp/backend.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

## 🔧 日志配置

### 后端日志级别
在 `backend/.env` 中配置：
```bash
DEBUG=true  # 开启调试模式，显示详细日志
```

### 前端日志
Next.js开发模式会自动输出详细日志到控制台和日志文件。

## 📋 日志文件管理

### 清空日志文件
```bash
# 清空后端日志
> /tmp/backend.log

# 清空前端日志
> /tmp/frontend.log
```

### 备份日志文件
```bash
# 备份后端日志
cp /tmp/backend.log /tmp/backend.log.$(date +%Y%m%d_%H%M%S)

# 备份前端日志
cp /tmp/frontend.log /tmp/frontend.log.$(date +%Y%m%d_%H%M%S)
```

### 查看日志文件大小
```bash
ls -lh /tmp/backend.log /tmp/frontend.log
```

## 🚀 快速开始

1. **启动服务**（如果未启动）：
   ```bash
   # 后端
   cd backend && python main.py > /tmp/backend.log 2>&1 &
   
   # 前端
   cd apps/rowboat && npm run dev > /tmp/frontend.log 2>&1 &
   ```

2. **开始监控**：
   ```bash
   ./scripts/monitor_logs.sh
   ```

3. **或直接监控**：
   ```bash
   tail -f /tmp/backend.log /tmp/frontend.log
   ```

---

**维护者**：开发团队  
**最后更新**：2025-01-27

