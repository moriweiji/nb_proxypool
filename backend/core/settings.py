# coding=utf-8
"""
应用配置（从环境变量加载）

使用 pydantic-settings 自动从 .env 文件加载配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""
    
    # ==================== Redis 配置 ====================
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    
    # ==================== 代理池配置 ====================
    proxy_key: str = "proxy_free"
    proxy_timeout: int = 5
    proxy_check_url: str = "https://www.baidu.com/"
    check_new_proxy_qps: int = 100
    check_exist_proxy_qps: int = 100
    check_new_proxy_concurrent: int = 300
    check_exist_proxy_concurrent: int = 400
    proxy_rescan_interval: int = 5
    
    # ==================== API 配置 ====================
    api_port: int = 8000
    frontend_port: int = 5173
    api_keys: str = "demo_key_12345"  # 多个 key 用逗号分隔（API Token）
    
    # ==================== 日志配置 ====================
    log_path: str = "/root/pythonlogs"
    log_level: str = "INFO"
    
    # ==================== GeoIP 配置 ====================
    geoip_db_path: str = "data/GeoLite2-City.mmdb"
    enable_geoip: bool = True
    
    # ==================== 爬虫配置 ====================
    spider_interval: int = 30
    enabled_sites: str = "Kuaidaili,Xici,Ip89,Ihuan,Zdaye,Beesproxy"
    max_crawl_pages: int = 4
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def api_keys_list(self) -> List[str]:
        """获取 API Keys 列表"""
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]
    
    @property
    def enabled_sites_list(self) -> List[str]:
        """获取启用的站点列表"""
        return [s.strip() for s in self.enabled_sites.split(",") if s.strip()]
    
    @property
    def redis_url(self) -> str:
        """构建 Redis 连接 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# 全局配置实例
settings = Settings()


# 测试代码
if __name__ == "__main__":
    print("=== 应用配置 ===\n")
    print(f"Redis URL: {settings.redis_url}")
    print(f"代理池键名: {settings.proxy_key}")
    print(f"API Keys: {settings.api_keys_list}")
    print(f"启用站点: {settings.enabled_sites_list}")
    print(f"GeoIP 数据库: {settings.geoip_db_path}")
    print(f"日志路径: {settings.log_path}")

