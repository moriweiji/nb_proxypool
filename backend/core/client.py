# coding=utf-8
"""
代理请求客户端

提供与 requests 100% 兼容的代理请求接口
"""

import json
import random
from boost_spider.http.request_client import RequestClient
from backend.core.config import get_redis, proxy_config


class ProxyClient(RequestClient):
    """
    代理请求客户端
    
    特点：
    - API 与 requests 100% 兼容
    - 自动从 Redis 代理池获取代理
    - 支持代理失败自动切换
    - 支持 noproxy 和 free 代理混合使用
    
    使用示例：
        # 轮流使用 free 代理和 noproxy，最多重试 4 次
        client = ProxyClient(
            proxy_name_list=[ProxyClient.PROXY_FREE, ProxyClient.PROXY_NOPROXY],
            request_retry_times=4
        )
        response = client.get('https://www.baidu.com')
    """
    
    # 代理类型常量
    PROXY_FREE = 'free'
    PROXY_NOPROXY = 'noproxy'
    
    def _request_with_free_proxy(self, method, url, verify=None, timeout=None, headers=None, cookies=None, **kwargs):
        """
        使用 Redis 中的免费代理发起请求
        
        Args:
            method: HTTP 方法（GET/POST/等）
            url: 请求 URL
            verify: SSL 验证
            timeout: 超时时间
            headers: 请求头
            cookies: Cookies
            **kwargs: 其他参数
        
        Returns:
            Response 对象
        
        Raises:
            Exception: 代理池为空时抛出异常，触发切换到 noproxy
        """
        redis = get_redis()
        proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
        
        # 从 Redis 获取所有可用代理
        proxies_list = redis.zrange(proxy_key, 0, -1)
        
        if len(proxies_list) == 0:
            err_msg = f'request_with_free_proxy: Redis {proxy_key} 键中没有代理 IP'
            self.logger.warning(err_msg)
            raise Exception(err_msg)  # 报错触发换成 noproxy 重试
        
        # 随机选择一个代理
        proxy_str = random.choice(proxies_list)
        proxies = json.loads(proxy_str)
        
        # 发起请求
        resp = self.ss.request(
            method, url,
            verify=verify or self._verify,
            timeout=timeout or self._timeout,
            headers=headers,
            cookies=cookies,
            proxies=proxies,
            **kwargs
        )
        
        return resp
    
    # 代理名称到请求方法的映射
    # 用户可以扩展此映射来添加自定义代理类型
    PROXYNAME__REQUEST_METHED_MAP = {
        'noproxy': RequestClient._request_with_no_proxy,
        'free': _request_with_free_proxy,
    }


# 测试代码
if __name__ == '__main__':
    # 测试：按照 free代理 → noproxy 的顺序请求，最多重试 4 次
    client = ProxyClient(
        proxy_name_list=[ProxyClient.PROXY_FREE, ProxyClient.PROXY_NOPROXY],
        request_retry_times=4
    )
    
    try:
        response = client.get('https://www.baidu.com')
        print(f"✅ 请求成功！状态码：{response.status_code}")
        print(f"   响应长度：{len(response.text)} 字符")
    except Exception as e:
        print(f"❌ 请求失败：{e}")

