# coding=utf-8
"""
爬虫管理器

负责启动、停止、监控爬虫进程
"""

import multiprocessing
import time
from typing import Optional
from funboost import funboost_aps_scheduler, ctrl_c_recv
from backend.crawlers.sites import *
from backend.core.checker import check_one_new_proxy, check_one_exist_proxy, scan_exists_proxy, show_proxy_count
from backend.core.settings import settings


class SpiderManager:
    """
    爬虫管理器（单例）
    
    功能：
    - 启动爬虫进程
    - 停止爬虫进程
    - 查询运行状态
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.process: Optional[multiprocessing.Process] = None
        self.is_running = False
        self.start_time: Optional[float] = None
        self._initialized = True
    
    def start(self) -> dict:
        """
        启动爬虫
        
        Returns:
            状态字典
        """
        if self.is_running and self.process and self.process.is_alive():
            return {
                "status": "already_running",
                "message": "爬虫已在运行中",
                "pid": self.process.pid
            }
        
        # 创建并启动进程
        self.process = multiprocessing.Process(target=self._run_spider, daemon=True)
        self.process.start()
        self.is_running = True
        self.start_time = time.time()
        
        return {
            "status": "started",
            "message": "爬虫启动成功",
            "pid": self.process.pid
        }
    
    def stop(self) -> dict:
        """
        停止爬虫
        
        Returns:
            状态字典
        """
        if not self.is_running or not self.process:
            return {
                "status": "not_running",
                "message": "爬虫未运行"
            }
        
        # 终止进程
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            
            # 强制杀死
            if self.process.is_alive():
                self.process.kill()
                self.process.join()
        
        self.is_running = False
        self.start_time = None
        
        return {
            "status": "stopped",
            "message": "爬虫已停止"
        }
    
    def status(self) -> dict:
        """
        获取爬虫状态
        
        Returns:
            状态字典
        """
        # 检查进程是否真的在运行
        if self.process and not self.process.is_alive():
            self.is_running = False
            self.start_time = None
        
        uptime = None
        if self.is_running and self.start_time:
            uptime = int(time.time() - self.start_time)
        
        return {
            "is_running": self.is_running,
            "pid": self.process.pid if self.process and self.process.is_alive() else None,
            "uptime": uptime
        }
    
    def _run_spider(self):
        """
        爬虫主逻辑（在子进程中运行）
        
        这是原 run_proxy.py 的逻辑
        """
        try:
            # 启动定时调度器
            funboost_aps_scheduler.start()
            
            # 获取启用的站点列表
            enabled_sites_names = settings.enabled_sites_list
            
            # 站点类映射
            site_classes = {
                'Kuaidaili': Kuaidaili,
                'Xici': Xici,
                'Ip89': Ip89,
                'Ihuan': Ihuan,
                'Zdaye': Zdaye,
                'Beesproxy': Beesproxy,
                'Kaixin': Kaixin,
                'Ip66': Ip66,
                'Ip3366': Ip3366,
            }
            
            # 定时任务：抓取代理
            max_pages = settings.max_crawl_pages
            interval = settings.spider_interval
            
            for p in range(1, max_pages + 1):
                for site_name in enabled_sites_names:
                    site_cls = site_classes.get(site_name)
                    if not site_cls:
                        continue
                    
                    # 页数越靠后，定时运行间隔越大（减少对网站的压力）
                    if site_cls.support_page or (not site_cls.support_page and p == 1):
                        funboost_aps_scheduler.add_push_job(
                            self._get_proxies_from_site,
                            'interval',
                            seconds=p * interval,
                            kwargs={
                                "site_proxy_cls_name": site_cls.class_name(),
                                "page": p
                            }
                        )
            
            # Kaixin 站点特殊处理（支持 proxy_type）
            if 'Kaixin' in enabled_sites_names:
                for p in range(1, max_pages + 1):
                    for proxy_type in [1, 2]:
                        funboost_aps_scheduler.add_push_job(
                            self._get_proxies_from_site,
                            'interval',
                            seconds=interval * p,
                            kwargs={
                                "site_proxy_cls_name": Kaixin.class_name(),
                                "page": p,
                                "proxy_type": proxy_type
                            }
                        )
            
            # 定时任务：扫描已存在的代理
            funboost_aps_scheduler.add_push_job(scan_exists_proxy, 'interval', seconds=30)
            
            # 定时任务：显示代理数量
            funboost_aps_scheduler.add_push_job(show_proxy_count, 'interval', seconds=10)
            
            # 启动消费者
            from funboost import boost, BrokerEnum
            
            # 使用装饰器定义任务
            @boost('get_proxies_from_sites', broker_kind=BrokerEnum.REDIS, qps=0.5, is_print_detail_exception=False)
            def get_proxies_from_sites(site_proxy_cls_name: str, page, proxy_type=None):
                """从指定站点获取代理"""
                from backend.crawlers.sites import get_proxy_getter_cls
                get_proxy_getter_cls(site_proxy_cls_name)(page=page, proxy_type=proxy_type).get_proxies()
            
            self._get_proxies_from_site = get_proxies_from_sites
            
            # 启动消费
            get_proxies_from_sites.consume()
            check_one_new_proxy.consume()
            check_one_exist_proxy.consume()
            scan_exists_proxy.consume()
            show_proxy_count.consume()
            
            # 阻塞等待 Ctrl+C
            ctrl_c_recv()
            
        except KeyboardInterrupt:
            print("爬虫进程收到停止信号")
        except Exception as e:
            print(f"爬虫进程异常: {e}")
            import traceback
            traceback.print_exc()


# 全局单例
spider_manager = SpiderManager()


# 测试代码
if __name__ == '__main__':
    print("启动爬虫管理器...")
    result = spider_manager.start()
    print(result)
    
    time.sleep(3)
    
    print("\n查询状态...")
    status = spider_manager.status()
    print(status)
    
    print("\n停止爬虫...")
    result = spider_manager.stop()
    print(result)

