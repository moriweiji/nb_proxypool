# coding=utf-8
"""
代理池配置模块

包含 Redis 配置、代理池配置等
"""

from functools import lru_cache
from funboost import RedisMixin


class ProxyPoolConfig:
    """代理池配置"""
    
    # Redis 中代理池的键名
    PROXY_KEY_IN_REDIS_DEFAULT = 'proxy_free'
    
    # 请求超时时间（秒）
    REQUESTS_TIMEOUT = 5
    
    # 代理检测 URL
    CHECK_PROXY_VALIDITY_URL = 'https://www.baidu.com/'
    
    # QPS 限制
    CHECK_NEW_PROXY_QPS = 100
    CHECK_EXIST_PROXY_QPS = 100
    
    # 并发数
    CHECK_NEW_PROXY_CONCURRENT = 300
    CHECK_EXIST_PROXY_CONCURRENT = 400
    
    # 代理扫描间隔（秒）
    # 代理最后检测时间超过此值将重新检测
    PROXY_RESCAN_INTERVAL = 5


@lru_cache()
def get_redis():
    """
    获取 Redis 客户端实例（单例）
    
    Returns:
        Redis 客户端
    """
    return RedisMixin().redis_db_frame


# 全局配置实例
proxy_config = ProxyPoolConfig()

