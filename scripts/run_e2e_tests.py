#!/usr/bin/env python3
"""
端到端测试脚本
E2E Test Script using Browser MCP

使用方法：
1. 确保后端和前端服务已启动
2. 运行此脚本：python scripts/run_e2e_tests.py
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# 测试结果存储
test_results: List[Dict[str, Any]] = []


def log_test(test_name: str, status: str, details: str = "", screenshot: str = ""):
    """记录测试结果"""
    result = {
        "test_name": test_name,
        "status": status,  # "passed", "failed", "skipped"
        "details": details,
        "screenshot": screenshot,
        "timestamp": datetime.now().isoformat(),
    }
    test_results.append(result)
    print(f"[{status.upper()}] {test_name}: {details}")


async def test_basic_navigation():
    """测试1：基础导航"""
    test_name = "基础导航和品牌显示"
    
    try:
        # 这里应该使用浏览器MCP工具
        # 由于需要实际浏览器环境，这里提供测试框架
        log_test(test_name, "skipped", "需要浏览器MCP环境")
    except Exception as e:
        log_test(test_name, "failed", str(e))


async def test_create_project():
    """测试2：创建项目"""
    test_name = "创建项目"
    
    try:
        log_test(test_name, "skipped", "需要浏览器MCP环境")
    except Exception as e:
        log_test(test_name, "failed", str(e))


async def test_workflow_editor():
    """测试3：工作流编辑器"""
    test_name = "工作流编辑器"
    
    try:
        log_test(test_name, "skipped", "需要浏览器MCP环境")
    except Exception as e:
        log_test(test_name, "failed", str(e))


async def test_chat_functionality():
    """测试4：聊天功能"""
    test_name = "聊天功能"
    
    try:
        log_test(test_name, "skipped", "需要浏览器MCP环境")
    except Exception as e:
        log_test(test_name, "failed", str(e))


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始端到端测试")
    print("=" * 60)
    print()
    
    # 检查服务是否运行
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8001/api/v1/health", timeout=2)
        print("✅ 后端服务运行正常")
    except Exception:
        print("❌ 后端服务未运行，请先启动服务")
        return
    
    try:
        urllib.request.urlopen("http://localhost:3001", timeout=2)
        print("✅ 前端服务运行正常")
    except Exception:
        print("❌ 前端服务未运行，请先启动服务")
        return
    
    print()
    
    # 运行测试
    await test_basic_navigation()
    await test_create_project()
    await test_workflow_editor()
    await test_chat_functionality()
    
    # 生成测试报告
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "passed")
    failed = sum(1 for r in test_results if r["status"] == "failed")
    skipped = sum(1 for r in test_results if r["status"] == "skipped")
    
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")
    print(f"总计: {len(test_results)}")
    
    # 保存测试结果
    with open("E2E_TEST_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 E2E_TEST_RESULTS.json")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

