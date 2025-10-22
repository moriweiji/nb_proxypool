# coding=utf-8
"""
代理检测模块（增强版）

功能：
- 检测代理有效性
- 记录代理生命周期信息
- 集成 GeoIP 地理位置识别
- 统计代理质量数据
"""

import json
import time
import re
import nb_log
from typing import Dict, Any

from boost_spider import RequestClient
from backend.core.config import get_redis, proxy_config
from backend.utils.geoip import get_geoip_locator
from funboost import boost, BrokerEnum, ConcurrentModeEnum


# 日志记录器
logger = nb_log.get_logger('proxy_check', log_filename='proxy_check.log')
logger_proxy_error = nb_log.get_logger('proxy_error', log_filename='proxy_error.log')


def extract_ip_from_proxy(proxy_dict: Dict[str, Any]) -> str:
    """
    从代理字典中提取 IP 地址
    
    Args:
        proxy_dict: 代理字典，格式如 {"http": "http://1.2.3.4:8080"}
    
    Returns:
        IP 地址字符串
    """
    # 从 http 或 https 字段提取 IP
    proxy_url = proxy_dict.get('http') or proxy_dict.get('https', '')
    
    # 使用正则提取 IP
    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', proxy_url)
    if match:
        return match.group(1)
    
    return ''


def enrich_proxy_with_geoip(proxy_dict: Dict[str, Any], redis_client) -> Dict[str, Any]:
    """
    为代理添加地理位置信息
    
    Args:
        proxy_dict: 原始代理字典
        redis_client: Redis 客户端
    
    Returns:
        增强后的代理字典（包含国家、地区等信息）
    """
    # 提取 IP
    ip = extract_ip_from_proxy(proxy_dict)
    if not ip:
        return proxy_dict
    
    # 查询地理位置
    try:
        geoip_locator = get_geoip_locator(redis_client)
        location = geoip_locator.locate(ip)
        
        # 添加地理位置信息到代理字典
        proxy_dict.update({
            'ip': ip,
            'country': location.get('country', ''),
            'country_name': location.get('country_name', ''),
            'region': location.get('region', ''),
            'city': location.get('city', ''),
            'flag': location.get('flag', '🏳️'),
        })
    except Exception as e:
        logger.warning(f"GeoIP 查询失败 {ip}: {e}")
    
    return proxy_dict


def save_proxy_details(proxy_dict: Dict[str, Any], is_valid: bool, response_time: float = 0):
    """
    保存代理详细信息到 Redis（用于生命周期监控）
    
    Args:
        proxy_dict: 代理字典
        is_valid: 是否有效
        response_time: 响应时间（秒）
    """
    try:
        redis = get_redis()
        ip = proxy_dict.get('ip', '')
        port_match = re.search(r':(\d+)', proxy_dict.get('http', ''))
        port = port_match.group(1) if port_match else ''
        
        if not ip or not port:
            return
        
        # 详细信息键
        detail_key = f"proxy_detail:{ip}:{port}"
        
        # 检查是否是新代理
        is_new = not redis.exists(detail_key)
        
        # 获取或初始化详细信息
        if is_new:
            details = {
                'ip': ip,
                'port': port,
                'protocol': 'http',
                'source': proxy_dict.get('platform', 'unknown'),
                'country': proxy_dict.get('country', ''),
                'country_name': proxy_dict.get('country_name', ''),
                'region': proxy_dict.get('region', ''),
                'city': proxy_dict.get('city', ''),
                'flag': proxy_dict.get('flag', '🏳️'),
                'created_at': time.time(),
                'last_check': time.time(),
                'check_count': 1,
                'success_count': 1 if is_valid else 0,
                'fail_count': 0 if is_valid else 1,
                'total_response_time': response_time,
                'avg_response_time': response_time,
                'status': 'active' if is_valid else 'inactive',
            }
        else:
            # 更新现有信息
            details = json.loads(redis.get(detail_key) or '{}')
            details['last_check'] = time.time()
            details['check_count'] = details.get('check_count', 0) + 1
            
            if is_valid:
                details['success_count'] = details.get('success_count', 0) + 1
                details['status'] = 'active'
            else:
                details['fail_count'] = details.get('fail_count', 0) + 1
                details['status'] = 'inactive'
            
            # 更新平均响应时间
            total_rt = details.get('total_response_time', 0) + response_time
            details['total_response_time'] = total_rt
            details['avg_response_time'] = total_rt / details['check_count']
        
        # 保存到 Redis（保留 30 天）
        redis.setex(detail_key, 30 * 24 * 3600, json.dumps(details, ensure_ascii=False))
        
    except Exception as e:
        logger.warning(f"保存代理详细信息失败: {e}")


@boost('check_one_new_proxy', qps=proxy_config.CHECK_NEW_PROXY_QPS, 
       broker_kind=BrokerEnum.REDIS, concurrent_num=proxy_config.CHECK_NEW_PROXY_CONCURRENT)
def check_one_new_proxy(proxy_dict: Dict[str, Any], is_save_to_db: bool = True, exist_proxy: bool = False):
    """
    检测单个新代理（funboost 任务）
    
    Args:
        proxy_dict: 代理字典，格式如 {"http": "http://1.2.3.4:8080", "platform": "kuaidaili"}
        is_save_to_db: 是否保存到数据库
        exist_proxy: 是否是已存在的代理（用于日志）
    
    Returns:
        bool: 代理是否有效
    """
    is_valid = False
    response_time = 0
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 发起检测请求
        RequestClient(
            using_platfrom=proxy_dict.get('platform', 'unknown'),
            request_retry_times=0
        ).get(
            proxy_config.CHECK_PROXY_VALIDITY_URL,
            timeout=proxy_config.REQUESTS_TIMEOUT,
            proxies=proxy_dict,
            verify=False
        )
        
        # 计算响应时间
        response_time = time.time() - start_time
        is_valid = True
        
    except Exception as e:
        logger_proxy_error.warning(f'{type(e).__name__}: {e}')
    
    # 日志记录
    proxy_type_str = '旧代理' if exist_proxy else '新代理'
    if is_valid:
        logger.info(f'✅ {proxy_dict} {proxy_type_str} 有效 (响应时间: {response_time:.2f}s)')
    else:
        logger.warning(f'❌ {proxy_dict} {proxy_type_str} 无效')
    
    # 保存到数据库
    if is_save_to_db:
        redis = get_redis()
        proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
        
        # 添加地理位置信息
        proxy_dict = enrich_proxy_with_geoip(proxy_dict, redis)
        
        if is_valid:
            # 有效代理：添加到 Sorted Set（score 为当前时间戳）
            redis.zadd(proxy_key, {json.dumps(proxy_dict, ensure_ascii=False): time.time()})
        else:
            # 无效代理：从 Sorted Set 中删除
            redis.zrem(proxy_key, json.dumps(proxy_dict, ensure_ascii=False))
        
        # 保存详细信息（用于生命周期监控）
        save_proxy_details(proxy_dict, is_valid, response_time)
    
    return is_valid


@boost('check_one_exist_proxy', qps=proxy_config.CHECK_EXIST_PROXY_QPS,
       broker_kind=BrokerEnum.REDIS, concurrent_num=proxy_config.CHECK_EXIST_PROXY_CONCURRENT)
def check_one_exist_proxy(proxy_dict: Dict[str, Any], is_save_to_db: bool = True):
    """
    检测单个已存在的代理（funboost 任务）
    
    Args:
        proxy_dict: 代理字典
        is_save_to_db: 是否保存到数据库
    
    Returns:
        bool: 代理是否有效
    """
    return check_one_new_proxy(proxy_dict, is_save_to_db, exist_proxy=True)


@boost('scan_exists_proxy', broker_kind=BrokerEnum.REDIS, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD)
def scan_exists_proxy():
    """
    扫描已存在的代理并重新检测（funboost 任务）
    
    逻辑：
    - 从 Redis Sorted Set 中获取 score < (当前时间 - 5秒) 的代理
    - 这些代理最后检测时间超过 5 秒，需要重新检测
    
    Returns:
        int: 推送检测的代理数量
    """
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 获取需要重新检测的代理（最后检测时间 > 5秒前）
    cutoff_time = time.time() - proxy_config.PROXY_RESCAN_INTERVAL
    proxy_dict_str_list = redis.zrangebyscore(proxy_key, 0, cutoff_time)
    
    # 推送到检测队列
    for proxy_dict_str in proxy_dict_str_list:
        try:
            proxy_dict = json.loads(proxy_dict_str)
            check_one_exist_proxy.push(proxy_dict)
        except Exception as e:
            logger.warning(f"解析代理失败: {e}")
    
    if len(proxy_dict_str_list) > 0:
        logger.info(f"📤 推送 {len(proxy_dict_str_list)} 个代理进行重新检测")
    
    return len(proxy_dict_str_list)


@boost('show_proxy_count', broker_kind=BrokerEnum.REDIS, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD)
def show_proxy_count():
    """
    显示当前代理池中的代理数量（funboost 任务）
    
    Returns:
        int: 代理数量
    """
    redis = get_redis()
    proxy_key = proxy_config.PROXY_KEY_IN_REDIS_DEFAULT
    
    # 统计有效代理数量（score >= 0 且 <= 当前时间）
    count = redis.zcount(proxy_key, 0, time.time())
    
    logger.info(f'📊 当前 {proxy_key} 键中共有 {count} 个代理')
    
    return count


# 测试代码
if __name__ == '__main__':
    # 测试代理检测
    test_proxy = {
        'http': 'http://1.2.3.4:8080',
        'https': 'http://1.2.3.4:8080',
        'platform': 'test'
    }
    
    print("测试代理检测功能...")
    result = check_one_new_proxy(test_proxy, is_save_to_db=False)
    print(f"检测结果：{'✅ 有效' if result else '❌ 无效'}")

