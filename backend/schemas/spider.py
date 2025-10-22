# coding=utf-8
"""
爬虫数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional


class SpiderStatusResponse(BaseModel):
    """爬虫状态响应"""
    is_running: bool = Field(..., description="是否正在运行")
    pid: Optional[int] = Field(None, description="进程 ID")
    uptime: Optional[int] = Field(None, description="运行时长（秒）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_running": True,
                "pid": 12345,
                "uptime": 3600
            }
        }


class SpiderControlResponse(BaseModel):
    """爬虫控制响应"""
    status: str = Field(..., description="操作状态")
    message: Optional[str] = Field(None, description="消息")
    pid: Optional[int] = Field(None, description="进程 ID")


class SiteStatusItem(BaseModel):
    """站点状态项"""
    name: str = Field(..., description="站点名称")
    enabled: bool = Field(True, description="是否启用")
    support_page: bool = Field(..., description="是否支持分页")
    last_crawl: Optional[float] = Field(None, description="最后抓取时间")
    total_crawled: int = Field(0, description="总抓取数")
    valid_count: int = Field(0, description="有效数")
    success_rate: float = Field(0.0, description="成功率")


class SiteStatusResponse(BaseModel):
    """站点状态响应"""
    total: int = Field(..., description="总站点数")
    enabled: int = Field(..., description="启用站点数")
    sites: list[SiteStatusItem] = Field(..., description="站点列表")

