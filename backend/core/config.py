# coding=utf-8
"""
代理池配置模块（兼容旧版本）

新版本请使用 backend.core.settings.Settings
此文件保留以兼容旧代码
"""

from functools import lru_cache
from funboost import RedisMixin
from backend.core.settings import settings


class ProxyPoolConfig:
    """代理池配置（从 settings 读取）"""
    
    @property
    def PROXY_KEY_IN_REDIS_DEFAULT(self):
        return settings.proxy_key
    
    @property
    def REQUESTS_TIMEOUT(self):
        return settings.proxy_timeout
    
    @property
    def CHECK_PROXY_VALIDITY_URL(self):
        return settings.proxy_check_url
    
    @property
    def CHECK_NEW_PROXY_QPS(self):
        return settings.check_new_proxy_qps
    
    @property
    def CHECK_EXIST_PROXY_QPS(self):
        return settings.check_exist_proxy_qps
    
    @property
    def CHECK_NEW_PROXY_CONCURRENT(self):
        return settings.check_new_proxy_concurrent
    
    @property
    def CHECK_EXIST_PROXY_CONCURRENT(self):
        return settings.check_exist_proxy_concurrent
    
    @property
    def PROXY_RESCAN_INTERVAL(self):
        return settings.proxy_rescan_interval


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

