# coding=utf-8
"""
IP 地理位置查询模块 - 混合策略

策略优先级：
1. Redis 缓存（最快，< 0.1ms）
2. 本地 GeoIP2 数据库（快速，< 1ms）
3. ip-api.com 在线 API（备用，100-500ms）
"""

import json
from pathlib import Path
from typing import Optional, Dict
import httpx

try:
    import geoip2.database
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False


class GeoIPLocator:
    """
    IP 地理位置查询器（混合策略）
    
    特点：
    - 优先使用本地 GeoIP2 数据库（性能最优）
    - 本地查询失败时降级到 ip-api.com
    - Redis 缓存查询结果（避免重复查询）
    """
    
    # 国家代码到中文名称映射
    COUNTRY_CN_MAP = {
        "CN": "中国", "US": "美国", "JP": "日本", "KR": "韩国",
        "SG": "新加坡", "HK": "香港", "TW": "台湾", "GB": "英国",
        "DE": "德国", "FR": "法国", "RU": "俄罗斯", "CA": "加拿大",
        "AU": "澳大利亚", "IN": "印度", "TH": "泰国", "VN": "越南",
        "MY": "马来西亚", "PH": "菲律宾", "ID": "印度尼西亚", "BR": "巴西",
        "MX": "墨西哥", "IT": "意大利", "ES": "西班牙", "NL": "荷兰",
        "CH": "瑞士", "SE": "瑞典", "NO": "挪威", "DK": "丹麦",
        "FI": "芬兰", "PL": "波兰", "CZ": "捷克", "AT": "奥地利",
        "BE": "比利时", "PT": "葡萄牙", "GR": "希腊", "TR": "土耳其",
        "ZA": "南非", "EG": "埃及", "AR": "阿根廷", "CL": "智利",
        "CO": "哥伦比亚", "PE": "秘鲁", "NZ": "新西兰", "IE": "爱尔兰",
        "IL": "以色列", "SA": "沙特阿拉伯", "AE": "阿联酋", "KW": "科威特",
        "PK": "巴基斯坦", "BD": "孟加拉国", "LK": "斯里兰卡", "MM": "缅甸",
        "KH": "柬埔寨", "LA": "老挝", "NP": "尼泊尔", "MN": "蒙古",
        "KZ": "哈萨克斯坦", "UZ": "乌兹别克斯坦", "UA": "乌克兰", "RO": "罗马尼亚",
        "HU": "匈牙利", "BG": "保加利亚", "RS": "塞尔维亚", "HR": "克罗地亚",
    }
    
    # 国家代码到旗帜 emoji 映射（Unicode 区域指示符）
    @staticmethod
    def get_flag_emoji(country_code: str) -> str:
        """根据国家代码生成旗帜 emoji"""
        if not country_code or len(country_code) != 2:
            return "🏳️"
        
        # 转换为区域指示符 (A=🇦, B=🇧, ...)
        # 原理：国旗 emoji = 两个区域指示符字母组合
        # 例如：CN = 🇨🇳 = U+1F1E8 U+1F1F3
        try:
            offset = 0x1F1E6 - ord('A')  # 🇦 的 Unicode 码点
            return ''.join(chr(ord(c) + offset) for c in country_code.upper())
        except:
            return "🏳️"
    
    def __init__(self, redis_client=None):
        """
        初始化 GeoIP 查询器
        
        Args:
            redis_client: Redis 客户端实例（可选）
        """
        self.redis = redis_client
        self.reader = None
        self.geoip_db_path = Path(__file__).parent.parent.parent / "data" / "GeoLite2-City.mmdb"
        
        # 尝试加载本地 GeoIP2 数据库
        if GEOIP2_AVAILABLE and self.geoip_db_path.exists():
            try:
                self.reader = geoip2.database.Reader(str(self.geoip_db_path))
                print(f"✅ GeoIP2 数据库加载成功: {self.geoip_db_path}")
            except Exception as e:
                print(f"⚠️ GeoIP2 数据库加载失败: {e}")
        else:
            if not GEOIP2_AVAILABLE:
                print("⚠️ geoip2 库未安装，将仅使用在线 API")
            elif not self.geoip_db_path.exists():
                print(f"⚠️ GeoIP2 数据库文件不存在: {self.geoip_db_path}")
                print("   请运行 `bash scripts/download_geoip.sh` 下载数据库")
    
    def locate(self, ip: str) -> Dict[str, str]:
        """
        查询 IP 地理位置（主入口）
        
        Args:
            ip: IP 地址
        
        Returns:
            包含国家/地区信息的字典：
            {
                "country": "CN",          # 国家代码
                "country_name": "中国",    # 国家名称
                "region": "广东",          # 省份/州
                "city": "深圳",            # 城市
                "flag": "🇨🇳"             # 国旗 emoji
            }
        """
        # 1. 检查 Redis 缓存
        if self.redis:
            try:
                cache_key = f"geoip:{ip}"
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Redis 缓存读取失败: {e}")
        
        # 2. 优先本地 GeoIP2 查询
        result = self._locate_local(ip)
        
        # 3. 本地失败则用在线 API
        if not result.get("country"):
            result = self._locate_online(ip)
        
        # 4. 缓存结果（7天）
        if self.redis and result.get("country"):
            try:
                cache_key = f"geoip:{ip}"
                self.redis.setex(cache_key, 7 * 24 * 3600, json.dumps(result, ensure_ascii=False))
            except Exception as e:
                print(f"Redis 缓存写入失败: {e}")
        
        return result
    
    def _locate_local(self, ip: str) -> Dict[str, str]:
        """
        本地 GeoIP2 数据库查询（< 1ms）
        
        Args:
            ip: IP 地址
        
        Returns:
            地理位置信息字典
        """
        if not self.reader:
            return {}
        
        try:
            response = self.reader.city(ip)
            country_code = response.country.iso_code or ""
            
            # 提取信息
            result = {
                "country": country_code,
                "country_name": self.COUNTRY_CN_MAP.get(
                    country_code, 
                    response.country.name or ""
                ),
                "region": "",
                "city": "",
                "flag": self.get_flag_emoji(country_code)
            }
            
            # 省份/州信息
            if response.subdivisions:
                result["region"] = response.subdivisions.most_specific.name or ""
            
            # 城市信息
            if response.city and response.city.name:
                result["city"] = response.city.name
            
            return result
            
        except geoip2.errors.AddressNotFoundError:
            # IP 不在数据库中
            return {}
        except Exception as e:
            print(f"本地 GeoIP2 查询失败 {ip}: {e}")
            return {}
    
    def _locate_online(self, ip: str) -> Dict[str, str]:
        """
        在线 ip-api.com 查询（备用，100-500ms）
        
        免费版限制：45次/分钟
        
        Args:
            ip: IP 地址
        
        Returns:
            地理位置信息字典
        """
        try:
            # 使用中文语言参数，获取中文国家名
            url = f"http://ip-api.com/json/{ip}"
            params = {
                "lang": "zh-CN",
                "fields": "status,country,countryCode,region,city"
            }
            
            with httpx.Client(timeout=3) as client:
                resp = client.get(url, params=params)
                data = resp.json()
                
                if data.get("status") == "success":
                    country_code = data.get("countryCode", "")
                    return {
                        "country": country_code,
                        "country_name": data.get("country", ""),
                        "region": data.get("region", ""),
                        "city": data.get("city", ""),
                        "flag": self.get_flag_emoji(country_code)
                    }
                    
        except httpx.TimeoutException:
            print(f"在线 API 查询超时: {ip}")
        except Exception as e:
            print(f"在线 API 查询失败 {ip}: {e}")
        
        # 查询失败，返回未知
        return {
            "country": "",
            "country_name": "未知",
            "region": "",
            "city": "",
            "flag": "🏳️"
        }
    
    def batch_locate(self, ip_list: list) -> Dict[str, Dict[str, str]]:
        """
        批量查询 IP 地理位置
        
        Args:
            ip_list: IP 地址列表
        
        Returns:
            字典：{ip: location_info}
        """
        results = {}
        for ip in ip_list:
            results[ip] = self.locate(ip)
        return results
    
    def get_country_stats(self, proxy_list: list) -> Dict[str, int]:
        """
        统计代理国家分布
        
        Args:
            proxy_list: 代理列表，每个代理包含 ip 字段
        
        Returns:
            国家统计字典：{country_code: count}
        """
        stats = {}
        for proxy in proxy_list:
            ip = proxy.get("ip")
            if not ip:
                continue
            
            location = self.locate(ip)
            country = location.get("country", "UNKNOWN")
            stats[country] = stats.get(country, 0) + 1
        
        return stats


# 全局单例（延迟初始化，需要传入 redis_client）
_geoip_locator_instance: Optional[GeoIPLocator] = None


def get_geoip_locator(redis_client=None) -> GeoIPLocator:
    """
    获取 GeoIP 查询器单例
    
    Args:
        redis_client: Redis 客户端实例
    
    Returns:
        GeoIPLocator 实例
    """
    global _geoip_locator_instance
    
    if _geoip_locator_instance is None:
        _geoip_locator_instance = GeoIPLocator(redis_client)
    
    return _geoip_locator_instance


# 测试代码
if __name__ == "__main__":
    # 测试（无 Redis）
    locator = GeoIPLocator()
    
    # 测试 IP
    test_ips = [
        "8.8.8.8",      # Google DNS（美国）
        "114.114.114.114",  # 中国 DNS
        "1.1.1.1",      # Cloudflare DNS
    ]
    
    print("\n=== GeoIP 查询测试 ===\n")
    for ip in test_ips:
        result = locator.locate(ip)
        print(f"{ip:20s} -> {result['flag']} {result['country_name']:10s} ({result['country']}) "
              f"{result['region']} {result['city']}")
    
    print("\n=== 国旗 emoji 测试 ===\n")
    test_countries = ["CN", "US", "JP", "KR", "GB", "FR", "DE", "RU"]
    for code in test_countries:
        flag = GeoIPLocator.get_flag_emoji(code)
        name = GeoIPLocator.COUNTRY_CN_MAP.get(code, code)
        print(f"{code} -> {flag} {name}")

