"""
数据库连接管理
Database connection management for MongoDB, Redis, and Qdrant
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings


# 全局数据库连接实例
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_db: Optional[AsyncIOMotorDatabase] = None
_redis_client: Optional[Redis] = None
_qdrant_client: Optional[QdrantClient] = None


async def get_mongodb_client() -> AsyncIOMotorClient:
    """
    获取MongoDB客户端实例（单例模式）
    Get MongoDB client instance (singleton pattern)
    """
    global _mongodb_client
    if _mongodb_client is None:
        settings = get_settings()
        _mongodb_client = AsyncIOMotorClient(settings.mongodb_connection_string)
    return _mongodb_client


async def get_mongodb_db() -> AsyncIOMotorDatabase:
    """
    获取MongoDB数据库实例
    Get MongoDB database instance
    """
    global _mongodb_db
    if _mongodb_db is None:
        client = await get_mongodb_client()
        # 从连接字符串中提取数据库名称，默认使用"zhixinzhigou"
        settings = get_settings()
        connection_string = settings.mongodb_connection_string
        
        # 解析数据库名称
        if "/" in connection_string:
            db_name = connection_string.split("/")[-1].split("?")[0]
            if not db_name:
                db_name = "zhixinzhigou"
        else:
            db_name = "zhixinzhigou"
        
        _mongodb_db = client[db_name]
    return _mongodb_db


async def get_redis_client() -> Redis:
    """
    获取Redis客户端实例（单例模式）
    Get Redis client instance (singleton pattern)
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_client


def get_qdrant_client() -> QdrantClient:
    """
    获取Qdrant客户端实例（单例模式）
    Get Qdrant client instance (singleton pattern)
    
    注意：Qdrant客户端是同步的
    Note: Qdrant client is synchronous
    """
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        )
    return _qdrant_client


async def close_mongodb_connection():
    """
    关闭MongoDB连接
    Close MongoDB connection
    """
    global _mongodb_client, _mongodb_db
    if _mongodb_client is not None:
        _mongodb_client.close()
        _mongodb_client = None
        _mongodb_db = None


async def close_redis_connection():
    """
    关闭Redis连接
    Close Redis connection
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def close_qdrant_connection():
    """
    关闭Qdrant连接
    Close Qdrant connection
    """
    global _qdrant_client
    if _qdrant_client is not None:
        _qdrant_client.close()
        _qdrant_client = None


async def close_all_connections():
    """
    关闭所有数据库连接
    Close all database connections
    """
    await close_mongodb_connection()
    await close_redis_connection()
    close_qdrant_connection()


async def check_mongodb_connection() -> bool:
    """
    检查MongoDB连接是否正常
    Check if MongoDB connection is working
    """
    try:
        client = await get_mongodb_client()
        # 执行ping命令检查连接
        await client.admin.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB连接失败: {e}")
        return False


async def check_redis_connection() -> bool:
    """
    检查Redis连接是否正常
    Check if Redis connection is working
    """
    try:
        client = await get_redis_client()
        # 执行ping命令检查连接
        await client.ping()
        return True
    except Exception as e:
        print(f"Redis连接失败: {e}")
        return False


def check_qdrant_connection() -> bool:
    """
    检查Qdrant连接是否正常
    Check if Qdrant connection is working
    """
    try:
        client = get_qdrant_client()
        # 获取集合列表检查连接
        client.get_collections()
        return True
    except Exception as e:
        print(f"Qdrant连接失败: {e}")
        return False


async def initialize_databases():
    """
    初始化所有数据库连接
    Initialize all database connections
    """
    print("正在初始化数据库连接...")
    
    # 检查MongoDB连接
    if await check_mongodb_connection():
        print("✓ MongoDB连接成功")
    else:
        print("✗ MongoDB连接失败")
        
    # 检查Redis连接
    if await check_redis_connection():
        print("✓ Redis连接成功")
    else:
        print("✗ Redis连接失败")
    
    # 检查Qdrant连接
    if check_qdrant_connection():
        print("✓ Qdrant连接成功")
    else:
        print("✗ Qdrant连接失败")


async def create_mongodb_indexes():
    """
    创建MongoDB索引
    Create MongoDB indexes
    """
    db = await get_mongodb_db()
    
    # 项目集合索引
    await db.projects.create_index("name")
    await db.projects.create_index("created_at")
    
    # 会话集合索引
    await db.conversations.create_index("project_id")
    await db.conversations.create_index("created_at")
    
    # 智能体集合索引
    await db.agents.create_index("project_id")
    await db.agents.create_index("name")
    
    print("✓ MongoDB索引创建成功")


def create_qdrant_collection(collection_name: str, vector_size: int = 1536):
    """
    创建Qdrant集合
    Create Qdrant collection
    
    Args:
        collection_name: 集合名称
        vector_size: 向量维度（默认1536，适用于OpenAI embeddings）
    """
    client = get_qdrant_client()
    
    try:
        # 检查集合是否存在
        collections = client.get_collections().collections
        if any(col.name == collection_name for col in collections):
            print(f"Qdrant集合 '{collection_name}' 已存在")
            return
        
        # 创建集合
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"✓ Qdrant集合 '{collection_name}' 创建成功")
    except Exception as e:
        print(f"✗ 创建Qdrant集合失败: {e}")

