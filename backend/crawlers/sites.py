# coding=utf-8
"""
代理站点爬虫模块

包含多个免费代理网站的爬虫实现
"""

import json
import typing
import re
import nb_log
from pyquery import PyQuery as pq
from boost_spider.http.request_client import SpiderResponse

from backend.core.client import ProxyClient
from backend.core.checker import check_one_new_proxy


class BaseProxyFromSiteGetter(nb_log.LoggerMixin):
    """
    代理站点爬虫基类
    
    属性：
        site_name: 站点名称
        url_formatter: URL 格式化模板
        support_page: 是否支持分页
    """
    
    site_name = None
    url_formatter: str = None
    support_page = False
    
    @classmethod
    def class_name(cls):
        """获取类名"""
        return str(cls.__name__).split('.')[-1]
    
    def __init__(self, page=1, proxy_type=None):
        """
        初始化爬虫
        
        Args:
            page: 页码（从 1 开始）
            proxy_type: 代理类型（某些站点需要）
        """
        self.resp = None
        self.page = page
        self.kwargs = {
            'page': page,
            'proxy_type': proxy_type
        }
        
        self.logger.debug([self.class_name(), self.kwargs])
        self._format_the_url()
        
        self.proxy_list = []  # type: typing.List[str]
        self.proxy_dict_list_valid = []  # type: typing.List[dict]
    
    def _format_the_url(self):
        """格式化 URL"""
        self.url = self.url_formatter.format(**self.kwargs)
    
    def _request(self):
        """发起 HTTP 请求"""
        self.resp = ProxyClient(
            proxy_name_list=[ProxyClient.PROXY_FREE, ProxyClient.PROXY_NOPROXY],
            using_platfrom=self.site_name,
            request_retry_times=2
        ).get(url=self.url)  # type: SpiderResponse
    
    def _parse(self):
        """
        解析响应内容（通用实现）
        
        适用于这样的网页结构：
            <td>139.196.214.238</td>
            <td>2087</td>
        """
        res = re.findall(
            r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>',
            self.resp.text
        )
        for r in res:
            self.proxy_list.append(f'{r[0]}:{r[1]}')
    
    def get_proxies(self):
        """
        获取代理列表（主入口）
        
        Returns:
            代理列表
        """
        # 不支持分页的网站，page > 1 时返回空列表
        if self.support_page is False and self.page > 1:
            return []
        
        # 请求网页
        self._request()
        
        # 解析代理
        if self.resp is not None:
            self._parse()
        
        # 推送到检测队列
        self._check_all_proxies()
        
        return self.proxy_list
    
    def _check_all_proxies(self):
        """将所有代理推送到检测队列"""
        for proxy in self.proxy_list:
            proxy_dict = {
                'https': f'http://{proxy}',  # 注意：这里统一使用 http 协议
                'http': f'http://{proxy}',
                'platform': self.site_name
            }
            check_one_new_proxy.push(proxy_dict)


def get_proxy_getter_cls(site_proxy_cls_name: str):
    """
    根据类名获取爬虫类
    
    Args:
        site_proxy_cls_name: 类名字符串
    
    Returns:
        爬虫类
    """
    site_proxy_cls = globals()[site_proxy_cls_name]  # type: type[BaseProxyFromSiteGetter]
    return site_proxy_cls


# ==================== 具体站点爬虫实现 ====================

class ZjProxy(BaseProxyFromSiteGetter):
    """代理非常非常垃圾，完全不可用"""
    site_name = 'zj'
    url_formatter = 'https://zj.v.api.aa1.cn/api/proxyip/'
    support_page = False
    
    def _parse(self):
        self.proxy_list = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', self.resp.text)


class Kuaidaili(BaseProxyFromSiteGetter):
    """快代理 - 可用"""
    site_name = 'kuaidaili'
    url_formatter = 'https://www.kuaidaili.com/free/intr/{page}/'
    support_page = True
    
    def _parse(self):
        """
        解析快代理网页
        格式：
            <td data-title="IP">182.34.102.15</td>
            <td data-title="PORT">9999</td>
        """
        p_list = re.findall(
            r'<td data-title="IP">(.*?)</td>[\s\S]*?<td data-title="PORT">(.*?)</td>',
            self.resp.text
        )
        for t in p_list:
            self.proxy_list.append(f'{t[0]}:{t[1]}')


class Ip66(BaseProxyFromSiteGetter):
    """66代理 - 一个代理没有，垃圾"""
    site_name = '66ip'
    url_formatter = 'http://www.66ip.cn/{page}.html'
    support_page = True
    
    def _parse(self):
        doc = pq(self.resp.text)
        trs = doc('.containerbox table tr:gt(0)').items()
        for tr in trs:
            ip = tr.find('td:nth-child(1)').text()
            port = tr.find('td:nth-child(2)').text()
            self.proxy_list.append(':'.join([ip, port]))


class Ip3366(BaseProxyFromSiteGetter):
    """云代理 - 很差劲"""
    site_name = 'ip3366'
    url_formatter = 'http://www.ip3366.net/?stype={proxy_type}&page={page}.html'
    support_page = True
    
    find_tr = re.compile('<tr>(.*?)</tr>', re.S)
    
    def _parse(self):
        trs = self.find_tr.findall(self.resp.text)
        for s in range(1, len(trs)):
            find_ip = re.compile(r'<td>(\d+\.\d+\.\d+\.\d+)</td>')
            re_ip_address = find_ip.findall(trs[s])
            find_port = re.compile(r'<td>(\d+)</td>')
            re_port = find_port.findall(trs[s])
            for address, port in zip(re_ip_address, re_port):
                address_port = address + ':' + port
                self.proxy_list.append(address_port.replace(' ', ''))


class Xici(BaseProxyFromSiteGetter):
    """西刺代理 - 可用"""
    site_name = 'xici'
    url_formatter = 'https://www.xicidaili.com/wn/{page}'
    support_page = False  # xici网站太垃圾了，不分页
    
    find_tr = re.compile('<tr>(.*?)</tr>', re.S)
    
    def _parse(self):
        trs = self.find_tr.findall(self.resp.text)
        for s in range(1, len(trs)):
            find_ip = re.compile(r'<td>(\d+\.\d+\.\d+\.\d+)</td>')
            re_ip_address = find_ip.findall(trs[s])
            find_port = re.compile(r'<td>(\d+)</td>')
            re_port = find_port.findall(trs[s])
            for address, port in zip(re_ip_address, re_port):
                address_port = address + ':' + port
                self.proxy_list.append(address_port.replace(' ', ''))


class Ip89(BaseProxyFromSiteGetter):
    """89免费代理 - 可以"""
    site_name = '89ip'
    url_formatter = 'https://www.89ip.cn/index_{page}.html'
    support_page = True
    
    def _parse(self):
        proxies = re.findall(
            r'<td.*?>[\s\S]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s\S]*?</td>[\s\S]*?<td.*?>[\s\S]*?(\d+)[\s\S]*?</td>',
            self.resp.text
        )
        for proxy in proxies:
            self.proxy_list.append(':'.join(proxy))


class Ihuan(BaseProxyFromSiteGetter):
    """小幻代理 - 不错"""
    site_name = 'ihuan'
    url_formatter = 'https://ip.ihuan.me/address/5Lit5Zu9.html?page={page}'
    support_page = True
    
    def _parse(self):
        proxies = re.findall(
            r'>\s*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*?</a></td><td>(\d+)</td>',
            self.resp.text
        )
        for proxy in proxies:
            self.proxy_list.append(':'.join(proxy))


class Fatezero(BaseProxyFromSiteGetter):
    """Fatezero - 垃圾"""
    site_name = 'fatezero'
    url_formatter = 'http://proxylist.fatezero.org/proxy.list'
    support_page = False
    
    def _parse(self):
        for each in self.resp.text.split("\n"):
            if not each.startswith('{'):
                continue
            json_info = json.loads(each)
            if json_info.get("country") == "CN":
                self.proxy_list.append("%s:%s" % (json_info.get("host", ""), json_info.get("port", "")))


class Kaixin(BaseProxyFromSiteGetter):
    """开心代理 - 不错"""
    site_name = 'kaixin'
    url_formatter = 'http://www.kxdaili.com/dailiip/{proxy_type}/{page}.html'
    support_page = True


class Zdaye(BaseProxyFromSiteGetter):
    """站大爷 - 不错"""
    site_name = 'zdaye'
    url_formatter = 'https://www.zdaye.com/free/?ip=&adr=&checktime=&sleep=&cunhuo=&dengji=&nadr=&https=1&yys=&post=&px='
    support_page = False


class Uqidata(BaseProxyFromSiteGetter):
    """Uqidata - 不行"""
    site_name = 'uqidata'
    url_formatter = 'https://ip.uqidata.com/free/index.html'
    support_page = False


class Proxyhub(BaseProxyFromSiteGetter):
    """Proxyhub - 不可用"""
    site_name = 'proxyhub'
    url_formatter = 'https://proxyhub.me/'
    support_page = False


class Cool(BaseProxyFromSiteGetter):
    """Cool Proxy - 不行"""
    site_name = 'cool'
    url_formatter = 'https://cool-proxy.net/proxies.json'
    support_page = False
    
    def _parse(self):
        for proxy in json.loads(self.resp.text):
            ip = proxy['ip']
            port = proxy['port']
            if ip:
                self.proxy_list.append("%s:%s" % (ip, port))


class Beesproxy(BaseProxyFromSiteGetter):
    """Bees Proxy - 不错"""
    site_name = 'beesproxy'
    url_formatter = 'https://www.beesproxy.com/free/page/{page}'
    support_page = True
    
    def _format_the_url(self):
        if self.page == 1:
            self.url = 'https://www.beesproxy.com/free'
        else:
            self.url = self.url_formatter.format(**self.kwargs)


# 测试代码
if __name__ == '__main__':
    # 测试爬虫
    print("测试 89IP 爬虫...")
    for p in range(1, 3):
        print(f"抓取第 {p} 页...")
        proxies = get_proxy_getter_cls('Ip89')(page=p).get_proxies()
        print(f"  发现 {len(proxies)} 个代理")

