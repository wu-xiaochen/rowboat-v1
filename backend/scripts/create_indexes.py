"""
创建数据库索引脚本
Script to create database indexes for performance optimization
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings


async def create_indexes():
    """
    创建所有必要的数据库索引
    Create all necessary database indexes
    """
    settings = get_settings()
    
    # 连接MongoDB
    client = AsyncIOMotorClient(settings.mongodb_connection_string)
    db = client[settings.mongodb_connection_string.split("/")[-1].split("?")[0]]
    
    print("开始创建数据库索引...")
    
    # ==================== Projects 集合索引 ====================
    projects_collection = db["projects"]
    
    # id字段索引（唯一）
    await projects_collection.create_index("id", unique=True, name="idx_projects_id")
    print("✓ 创建 projects.id 索引")
    
    # createdByUserId字段索引（用于查询用户的项目）
    await projects_collection.create_index("createdByUserId", name="idx_projects_createdByUserId")
    print("✓ 创建 projects.createdByUserId 索引")
    
    # createdAt字段索引（用于排序）
    await projects_collection.create_index("createdAt", name="idx_projects_createdAt")
    print("✓ 创建 projects.createdAt 索引")
    
    # 复合索引：createdByUserId + createdAt（用于按用户查询并排序）
    await projects_collection.create_index(
        [("createdByUserId", 1), ("createdAt", -1)],
        name="idx_projects_user_created"
    )
    print("✓ 创建 projects (createdByUserId, createdAt) 复合索引")
    
    # ==================== Conversations 集合索引 ====================
    conversations_collection = db["conversations"]
    
    # id字段索引（唯一）
    await conversations_collection.create_index("id", unique=True, name="idx_conversations_id")
    print("✓ 创建 conversations.id 索引")
    
    # projectId字段索引（用于查询项目的对话）
    await conversations_collection.create_index("projectId", name="idx_conversations_projectId")
    print("✓ 创建 conversations.projectId 索引")
    
    # createdAt字段索引（用于排序）
    await conversations_collection.create_index("createdAt", name="idx_conversations_createdAt")
    print("✓ 创建 conversations.createdAt 索引")
    
    # 复合索引：projectId + createdAt（用于按项目查询并排序）
    await conversations_collection.create_index(
        [("projectId", 1), ("createdAt", -1)],
        name="idx_conversations_project_created"
    )
    print("✓ 创建 conversations (projectId, createdAt) 复合索引")
    
    # ==================== API Keys 集合索引 ====================
    api_keys_collection = db["api_keys"]
    
    # id字段索引（唯一）
    await api_keys_collection.create_index("id", unique=True, name="idx_api_keys_id")
    print("✓ 创建 api_keys.id 索引")
    
    # projectId字段索引（用于查询项目的API Keys）
    await api_keys_collection.create_index("projectId", name="idx_api_keys_projectId")
    print("✓ 创建 api_keys.projectId 索引")
    
    # key字段索引（用于API Key验证，唯一）
    await api_keys_collection.create_index("key", unique=True, name="idx_api_keys_key")
    print("✓ 创建 api_keys.key 索引")
    
    # 复合索引：key + isActive（用于API Key验证查询）
    await api_keys_collection.create_index(
        [("key", 1), ("isActive", 1)],
        name="idx_api_keys_key_active"
    )
    print("✓ 创建 api_keys (key, isActive) 复合索引")
    
    # createdAt字段索引（用于排序）
    await api_keys_collection.create_index("createdAt", name="idx_api_keys_createdAt")
    print("✓ 创建 api_keys.createdAt 索引")
    
    print("\n所有索引创建完成！")
    
    # 关闭连接
    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())

