#!/bin/bash
# 清理 .env 文件，统一配置格式
# 移除向后兼容的 PROVIDER_* 配置和重复的 COPILOT_MODEL/AGENT_MODEL

ENV_FILE=".env"
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 清理 .env 配置文件..."
echo "📋 备份文件: $BACKUP_FILE"

# 备份原文件
cp "$ENV_FILE" "$BACKUP_FILE"

# 使用 sed 移除向后兼容的配置行
# 移除 PROVIDER_* 前缀的配置（保留注释）
sed -i.bak '/^PROVIDER_/d' "$ENV_FILE"

# 移除 COPILOT_MODEL 和 AGENT_MODEL（现在使用 LLM_MODEL_ID）
sed -i.bak '/^COPILOT_MODEL=/d' "$ENV_FILE"
sed -i.bak '/^AGENT_MODEL=/d' "$ENV_FILE"

# 移除向后兼容的注释
sed -i.bak '/兼容旧的环境变量名/d' "$ENV_FILE"
sed -i.bak '/向后兼容/d' "$ENV_FILE"

# 统一 Embedding 配置命名（可选，如果需要）
# 如果使用 EMBEDDING_PROVIDER_*，可以改为 EMBEDDING_*
# 但为了保持兼容，暂时保留

# 清理临时文件
rm -f "$ENV_FILE.bak"

echo "✅ 清理完成！"
echo "📝 已移除的配置："
echo "   - PROVIDER_* 前缀的配置（向后兼容）"
echo "   - COPILOT_MODEL（使用 LLM_MODEL_ID）"
echo "   - AGENT_MODEL（使用 LLM_MODEL_ID）"
echo ""
echo "💾 备份文件保存在: $BACKUP_FILE"
echo "⚠️  请检查 .env 文件，确认配置正确后删除备份文件"

