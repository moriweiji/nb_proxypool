# coding=utf-8
"""
代理数据模型
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProxyModel(BaseModel):
    """代理基础模型"""
    ip: str = Field(..., description="IP 地址")
    port: int = Field(..., description="端口号")
    protocol: str = Field(default="http", description="协议类型")
    source: str = Field(..., description="来源站点")
    
    # 地理位置信息
    country: Optional[str] = Field(None, description="国家代码")
    country_name: Optional[str] = Field(None, description="国家名称")
    region: Optional[str] = Field(None, description="省份/州")
    city: Optional[str] = Field(None, description="城市")
    flag: Optional[str] = Field(None, description="国旗 emoji")
    
    # 生命周期信息
    created_at: Optional[float] = Field(None, description="创建时间戳")
    last_check: Optional[float] = Field(None, description="最后检测时间戳")
    check_count: Optional[int] = Field(0, description="检测次数")
    success_count: Optional[int] = Field(0, description="成功次数")
    fail_count: Optional[int] = Field(0, description="失败次数")
    avg_response_time: Optional[float] = Field(None, description="平均响应时间（秒）")
    status: Optional[str] = Field("active", description="状态：active/inactive")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip": "1.2.3.4",
                "port": 8080,
                "protocol": "http",
                "source": "kuaidaili",
                "country": "CN",
                "country_name": "中国",
                "region": "广东",
                "city": "深圳",
                "flag": "🇨🇳",
                "status": "active"
            }
        }


class ProxyListResponse(BaseModel):
    """代理列表响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    data: list[ProxyModel] = Field(..., description="代理列表")


class StatsResponse(BaseModel):
    """统计信息响应"""
    total: int = Field(..., description="总代理数")
    valid_count: int = Field(..., description="有效代理数")
    invalid_count: int = Field(0, description="无效代理数")
    check_rate: float = Field(0.0, description="检测率")
    avg_response_time: float = Field(0.0, description="平均响应时间")


class CountryStatsItem(BaseModel):
    """国家统计项"""
    country: str = Field(..., description="国家代码")
    country_name: str = Field(..., description="国家名称")
    flag: str = Field(..., description="国旗 emoji")
    count: int = Field(..., description="代理数量")
    percentage: float = Field(..., description="占比")


class CountryStatsResponse(BaseModel):
    """国家统计响应"""
    total: int = Field(..., description="总数")
    countries: list[CountryStatsItem] = Field(..., description="各国家统计")

