<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <div style="font-size: 14px; color: #666">总代理数</div>
          <div style="font-size: 32px; font-weight: bold; margin-top: 10px">
            {{ stats.total }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div style="font-size: 14px; color: #666">有效代理</div>
          <div style="font-size: 32px; font-weight: bold; margin-top: 10px; color: #67C23A">
            {{ stats.valid_count }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div style="font-size: 14px; color: #666">爬虫状态</div>
          <div style="font-size: 32px; font-weight: bold; margin-top: 10px" :style="{ color: spiderRunning ? '#67C23A' : '#909399' }">
            {{ spiderRunning ? '运行中' : '已停止' }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>国家分布</span>
          <el-button size="small" @click="refreshCountryStats">刷新</el-button>
        </div>
      </template>
      <el-table :data="countryStats" height="400">
        <el-table-column prop="flag" label="国旗" width="80" />
        <el-table-column prop="country_name" label="国家" />
        <el-table-column prop="count" label="数量" sortable />
        <el-table-column prop="percentage" label="占比" sortable>
          <template #default="{ row }">
            {{ row.percentage.toFixed(1) }}%
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { proxyAPI, spiderAPI } from '@/api'

const stats = ref({
  total: 0,
  valid_count: 0
})

const spiderRunning = ref(false)
const countryStats = ref([])

const loadStats = async () => {
  try {
    const res = await proxyAPI.getStats()
    stats.value = res.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadSpiderStatus = async () => {
  try {
    const res = await spiderAPI.getStatus()
    spiderRunning.value = res.data.is_running
  } catch (error) {
    console.error('加载爬虫状态失败:', error)
  }
}

const refreshCountryStats = async () => {
  try {
    const res = await proxyAPI.getCountryStats()
    countryStats.value = res.data.countries
  } catch (error) {
    console.error('加载国家统计失败:', error)
  }
}

onMounted(() => {
  loadStats()
  loadSpiderStatus()
  refreshCountryStats()
  
  // 定时刷新
  setInterval(loadStats, 30000)
  setInterval(loadSpiderStatus, 10000)
})
</script>

