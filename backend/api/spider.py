# coding=utf-8
"""
爬虫控制 API（内部使用）

提供爬虫启动、停止、状态查询等功能
"""

from fastapi import APIRouter
from backend.core.spider_manager import spider_manager
from backend.schemas.spider import SpiderStatusResponse, SpiderControlResponse
from backend.core.settings import settings


router = APIRouter(prefix="/api/spider", tags=["Spider Control"])


@router.post("/start", response_model=SpiderControlResponse, summary="启动爬虫")
async def start_spider():
    """启动爬虫进程"""
    result = spider_manager.start()
    return result


@router.post("/stop", response_model=SpiderControlResponse, summary="停止爬虫")
async def stop_spider():
    """停止爬虫进程"""
    result = spider_manager.stop()
    return result


@router.get("/status", response_model=SpiderStatusResponse, summary="获取爬虫状态")
async def get_spider_status():
    """获取爬虫运行状态"""
    result = spider_manager.status()
    return result


@router.get("/sites", summary="获取站点配置")
async def get_sites_config():
    """获取爬虫站点配置"""
    from backend.crawlers.sites import (
        Kuaidaili, Xici, Ip89, Ihuan, Zdaye, Beesproxy, Kaixin
    )
    
    enabled_sites = settings.enabled_sites_list
    
    # 所有可用站点
    all_sites = {
        'Kuaidaili': Kuaidaili,
        'Xici': Xici,
        'Ip89': Ip89,
        'Ihuan': Ihuan,
        'Zdaye': Zdaye,
        'Beesproxy': Beesproxy,
        'Kaixin': Kaixin,
    }
    
    sites = []
    for name, cls in all_sites.items():
        sites.append({
            "name": name,
            "site_name": cls.site_name,
            "enabled": name in enabled_sites,
            "support_page": cls.support_page,
            "url": cls.url_formatter,
        })
    
    return {
        "total": len(sites),
        "enabled": len([s for s in sites if s['enabled']]),
        "sites": sites
    }


@router.get("/logs", summary="获取爬虫日志")
async def get_spider_logs(lines: int = 100):
    """
    获取爬虫日志
    
    - **lines**: 读取最后 N 行
    """
    import os
    from pathlib import Path
    
    log_path = Path(settings.log_path) / "proxy_check.log"
    
    if not log_path.exists():
        return {"logs": [], "message": "日志文件不存在"}
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return {
            "logs": recent_lines,
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
    except Exception as e:
        return {"logs": [], "error": str(e)}

