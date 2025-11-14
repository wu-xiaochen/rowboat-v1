#!/bin/bash

# 清理过期的文档文件
# 保留重要的文档，删除过期的测试报告和状态文档

cd "$(dirname "$0")/.." || exit 1

DOCS_DIR="docs"

echo "🧹 开始清理docs目录..."

# 要保留的重要文档
KEEP_FILES=(
    "copilot-fix-plan.md"
    "TESTING_GUIDE.md"
    "TESTING_PLAN.md"
    "COMPREHENSIVE_TESTING_GUIDE.md"
    "HOW_TO_VIEW_BACKEND_LOGS.md"
    "LOG_DEBUGGING_GUIDE.md"
    "API_ENDPOINTS_IMPLEMENTATION_PLAN.md"
    "FEATURE_COMPARISON.md"
    "LEGACY_CODE_CLEANUP.md"
)

# 要删除的过期文档模式
DELETE_PATTERNS=(
    "*TEST_*.md"
    "*FINAL_*.md"
    "*COMPLETE_*.md"
    "*COMPLETION_*.md"
    "*STATUS_*.md"
    "*REPORT_*.md"
    "*SUMMARY_*.md"
    "*PROGRESS_*.md"
    "*100_PERCENT_*.md"
    "*EXECUTION_*.md"
    "*VERIFICATION_*.md"
    "*FIXES_*.md"
    "*FIX_*.md"
    "*DEBUG_*.md"
    "*MESSAGE_*.md"
    "*IMPLEMENTATION_*.md"
    "*ALIGNMENT_*.md"
    "*UPDATE_*.md"
    "*MIGRATION_*.md"
    "*CONFIGURATION_*.md"
    "*HANDLING_*.md"
    "*ANALYSIS_*.md"
    "*REQUIRED_*.md"
    "*RESULTS_*.md"
    "*PLAN_*.md"
)

# 统计删除的文件数
DELETED_COUNT=0

# 遍历docs目录
for file in "$DOCS_DIR"/*.md; do
    if [ ! -f "$file" ]; then
        continue
    fi
    
    filename=$(basename "$file")
    
    # 检查是否在保留列表中
    KEEP=false
    for keep_file in "${KEEP_FILES[@]}"; do
        if [ "$filename" == "$keep_file" ]; then
            KEEP=true
            break
        fi
    done
    
    if [ "$KEEP" == true ]; then
        echo "✅ 保留: $filename"
        continue
    fi
    
    # 检查是否匹配删除模式
    DELETE=false
    for pattern in "${DELETE_PATTERNS[@]}"; do
        if [[ "$filename" == $pattern ]]; then
            DELETE=true
            break
        fi
    done
    
    if [ "$DELETE" == true ]; then
        echo "🗑️  删除: $filename"
        rm -f "$file"
        ((DELETED_COUNT++))
    else
        echo "⚠️  未处理: $filename (请手动检查)"
    fi
done

echo ""
echo "✨ 清理完成！删除了 $DELETED_COUNT 个过期文档"
echo "📝 保留的重要文档："
for keep_file in "${KEEP_FILES[@]}"; do
    if [ -f "$DOCS_DIR/$keep_file" ]; then
        echo "   - $keep_file"
    fi
done

