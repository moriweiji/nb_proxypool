# coding=utf-8
"""
对外公开 API（需要 API Key 认证）

提供给第三方程序调用的代理获取接口
"""

import json
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.core.config import get_redis, proxy_config
from backend.utils.auth import verify_api_key
from backend.schemas.proxy import ProxyModel


router = APIRouter(prefix="/api/public", tags=["Public API"])


@router.get("/proxy/random", summary="获取随机代理")
async def get_random_proxy(
    country: str = Query(None, description="国家代码筛选（如 CN、US）"),
    _api_key: str = Depends(verify_api_key)
):
    """
    获取随机代理
    
    - **country**: 可选，指定国家代码（如 CN、US、JP）
    - 需要在请求头中提供 X-API-Key
    """
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 获取所有代理
    all_proxies = redis.zrange(proxy_key, 0, -1)
    
    if not all_proxies:
        raise HTTPException(status_code=404, detail="No proxy available")
    
    # 解析代理列表
    proxy_list = [json.loads(p) for p in all_proxies]
    
    # 按国家筛选
    if country:
        proxy_list = [p for p in proxy_list if p.get('country', '').upper() == country.upper()]
        
        if not proxy_list:
            raise HTTPException(
                status_code=404,
                detail=f"No proxy available for country: {country}"
            )
    
    # 随机选择一个
    selected = random.choice(proxy_list)
    
    return selected


@router.get("/proxy/list", summary="批量获取代理")
async def get_proxy_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    country: str = Query(None, description="国家代码筛选"),
    _api_key: str = Depends(verify_api_key)
):
    """
    批量获取代理（分页）
    
    - **page**: 页码（从 1 开始）
    - **size**: 每页数量（1-100）
    - **country**: 可选，按国家筛选
    """
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 获取所有代理
    all_proxies = redis.zrange(proxy_key, 0, -1)
    proxy_list = [json.loads(p) for p in all_proxies]
    
    # 按国家筛选
    if country:
        proxy_list = [p for p in proxy_list if p.get('country', '').upper() == country.upper()]
    
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


@router.get("/countries", summary="获取可用国家列表")
async def get_available_countries(_api_key: str = Depends(verify_api_key)):
    """
    获取所有可用的国家列表及代理数量
    """
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 获取所有代理
    all_proxies = redis.zrange(proxy_key, 0, -1)
    proxy_list = [json.loads(p) for p in all_proxies]
    
    # 统计各国家数量
    country_stats = {}
    for proxy in proxy_list:
        country = proxy.get('country', 'UNKNOWN')
        country_name = proxy.get('country_name', country)
        flag = proxy.get('flag', '🏳️')
        
        if country not in country_stats:
            country_stats[country] = {
                'country': country,
                'country_name': country_name,
                'flag': flag,
                'count': 0
            }
        
        country_stats[country]['count'] += 1
    
    # 按数量排序
    countries = sorted(country_stats.values(), key=lambda x: x['count'], reverse=True)
    
    return {
        "total": len(countries),
        "countries": countries
    }

