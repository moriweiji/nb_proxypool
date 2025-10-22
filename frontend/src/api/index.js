import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 代理相关 API
export const proxyAPI = {
  // 获取代理列表
  getProxies(params) {
    return api.get('/admin/proxies', { params })
  },
  
  // 删除代理
  deleteProxy(proxyId) {
    return api.delete(`/admin/proxies/${proxyId}`)
  },
  
  // 测试代理
  testProxy(proxyUrl) {
    return api.post('/admin/proxies/test', null, { params: { proxy_url: proxyUrl } })
  },
  
  // 获取统计
  getStats() {
    return api.get('/admin/stats/overview')
  },
  
  // 获取国家统计
  getCountryStats() {
    return api.get('/admin/stats/countries')
  }
}

// 爬虫相关 API
export const spiderAPI = {
  // 启动爬虫
  start() {
    return api.post('/spider/start')
  },
  
  // 停止爬虫
  stop() {
    return api.post('/spider/stop')
  },
  
  // 获取状态
  getStatus() {
    return api.get('/spider/status')
  },
  
  // 获取站点配置
  getSites() {
    return api.get('/spider/sites')
  },
  
  // 获取日志
  getLogs(lines = 100) {
    return api.get('/spider/logs', { params: { lines } })
  }
}

