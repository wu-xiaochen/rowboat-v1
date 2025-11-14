#!/bin/bash
# 项目清理脚本
# Project cleanup script

echo "🧹 开始清理项目..."

# 清理 Python 缓存文件
echo "清理 Python 缓存文件..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null
echo "✅ Python 缓存已清理"

# 清理测试结果
echo "清理测试结果..."
find . -type d -name "coverage" -exec rm -rf {} + 2>/dev/null
find . -type d -name "test-results" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".nyc_output" -exec rm -rf {} + 2>/dev/null
echo "✅ 测试结果已清理"

# 清理临时文件
echo "清理临时文件..."
find . -maxdepth 3 -type f \( -name "*.tmp" -o -name "*.bak" -o -name "*.backup" -o -name "*.swp" -o -name "*.swo" \) -not -path "*/node_modules/*" -delete 2>/dev/null
echo "✅ 临时文件已清理"

# 清理前端构建缓存（可选，取消注释以启用）
# echo "清理前端构建缓存..."
# find . -type d -name ".next" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null
# find . -type d -name "dist" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null
# find . -type d -name "build" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null
# echo "✅ 构建缓存已清理"

echo ""
echo "✨ 清理完成！"
echo ""
echo "💡 提示："
echo "   - .next/ 目录是 Next.js 构建缓存，开发时会自动生成"
echo "   - node_modules/ 目录包含依赖，使用 npm install 重新安装"
echo "   - 如需清理构建缓存，取消脚本中相关注释"



