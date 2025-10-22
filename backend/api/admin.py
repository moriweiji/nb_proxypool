# coding=utf-8
"""
内部管理 API（Web 端调用，无需认证）

提供代理管理、统计等功能
"""

import json
import time
import re
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.core.config import get_redis, proxy_config
from backend.core.checker import check_one_new_proxy
from backend.utils.geoip import get_geoip_locator
from backend.schemas.proxy import ProxyListResponse, StatsResponse, CountryStatsResponse, CountryStatsItem


router = APIRouter(prefix="/api/admin", tags=["Admin API"])


@router.get("/proxies", response_model=ProxyListResponse, summary="获取代理列表")
async def get_proxies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    country: Optional[str] = Query(None, description="国家代码筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（IP/城市）")
):
    """获取代理列表（分页、筛选）"""
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 获取所有代理
    all_proxies = redis.zrange(proxy_key, 0, -1)
    proxy_list = [json.loads(p) for p in all_proxies]
    
    # 筛选
    if country:
        proxy_list = [p for p in proxy_list if p.get('country', '').upper() == country.upper()]
    
    if keyword:
        keyword_lower = keyword.lower()
        proxy_list = [
            p for p in proxy_list
            if keyword_lower in p.get('http', '').lower()
            or keyword_lower in p.get('city', '').lower()
        ]
    
    # 分页
    total = len(proxy_list)
    start = (page - 1) * size
    end = start + size
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "data": proxy_list[start:end]
    }


@router.delete("/proxies/{proxy_id}", summary="删除指定代理")
async def delete_proxy(proxy_id: str):
    """
    删除指定代理
    
    proxy_id 格式：{ip}:{port}
    """
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 查找并删除
    all_proxies = redis.zrange(proxy_key, 0, -1)
    deleted = False
    
    for proxy_str in all_proxies:
        proxy = json.loads(proxy_str)
        http_proxy = proxy.get('http', '')
        
        if proxy_id in http_proxy:
            redis.zrem(proxy_key, proxy_str)
            deleted = True
            break
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    return {"status": "deleted", "proxy_id": proxy_id}


@router.post("/proxies/test", summary="测试代理")
async def test_proxy(proxy_url: str):
    """测试指定代理是否有效"""
    # 构造代理字典
    proxy_dict = {
        'http': proxy_url,
        'https': proxy_url,
        'platform': 'manual_test'
    }
    
    # 测试（不保存到数据库）
    is_valid = check_one_new_proxy(proxy_dict, is_save_to_db=False)
    
    return {
        "proxy": proxy_url,
        "is_valid": is_valid,
        "status": "✅ 有效" if is_valid else "❌ 无效"
    }


@router.get("/stats/overview", response_model=StatsResponse, summary="获取概览统计")
async def get_stats_overview():
    """获取代理池概览统计"""
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 统计总数
    total = redis.zcount(proxy_key, 0, time.time())
    
    return {
        "total": total,
        "valid_count": total,  # 池中的都是有效的
        "invalid_count": 0,
        "check_rate": 100.0,
        "avg_response_time": 0.0
    }


@router.get("/stats/countries", response_model=CountryStatsResponse, summary="获取国家统计")
async def get_country_stats():
    """获取各国家代理统计"""
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 获取所有代理
    all_proxies = redis.zrange(proxy_key, 0, -1)
    proxy_list = [json.loads(p) for p in all_proxies]
    
    # 统计
    country_map = {}
    total = len(proxy_list)
    
    for proxy in proxy_list:
        country = proxy.get('country', 'UNKNOWN')
        country_name = proxy.get('country_name', country)
        flag = proxy.get('flag', '🏳️')
        
        if country not in country_map:
            country_map[country] = {
                'country': country,
                'country_name': country_name,
                'flag': flag,
                'count': 0
            }
        
        country_map[country]['count'] += 1
    
    # 计算百分比
    countries = []
    for data in country_map.values():
        data['percentage'] = (data['count'] / total * 100) if total > 0 else 0
        countries.append(CountryStatsItem(**data))
    
    # 按数量排序
    countries.sort(key=lambda x: x.count, reverse=True)
    
    return {
        "total": total,
        "countries": countries
    }


@router.get("/stats/trend", summary="获取趋势数据")
async def get_trend_data(hours: int = Query(24, ge=1, le=168)):
    """
    获取代理数量趋势数据
    
    - **hours**: 时间范围（小时）
    """
    # 简化实现：返回模拟数据
    # 生产环境应该从 Redis TimeSeries 或其他时序数据库读取
    
    import random
    from datetime import datetime, timedelta
    
    now = datetime.now()
    data_points = []
    
    for i in range(hours):
        timestamp = (now - timedelta(hours=hours-i-1)).timestamp()
        count = random.randint(100, 500)  # 模拟数据
        data_points.append({
            "timestamp": timestamp,
            "count": count
        })
    
    return {
        "hours": hours,
        "data": data_points
    }

