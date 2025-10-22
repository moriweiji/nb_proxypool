<template>
  <div>
    <!-- 爬虫控制 -->
    <el-card>
      <template #header>
        <span>爬虫控制</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-statistic title="运行状态">
            <template #default>
              <el-tag :type="status.is_running ? 'success' : 'info'" size="large">
                {{ status.is_running ? '🟢 运行中' : '⚫ 已停止' }}
              </el-tag>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8" v-if="status.is_running">
          <el-statistic title="进程 ID" :value="status.pid || '-'" />
        </el-col>
        <el-col :span="8" v-if="status.is_running && status.uptime">
          <el-statistic title="运行时长">
            <template #default>
              {{ formatUptime(status.uptime) }}
            </template>
          </el-statistic>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <el-space>
        <el-button
          type="success"
          :disabled="status.is_running"
          @click="startSpider"
          :loading="operating"
        >
          ▶️ 启动爬虫
        </el-button>
        <el-button
          type="danger"
          :disabled="!status.is_running"
          @click="stopSpider"
          :loading="operating"
        >
          ⏸️ 停止爬虫
        </el-button>
        <el-button @click="refreshStatus">
          🔄 刷新状态
        </el-button>
      </el-space>
    </el-card>

    <!-- 站点状态 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>代理站点</span>
      </template>
      <el-table :data="sites" max-height="300">
        <el-table-column label="启用" width="60">
          <template #default="{ row }">
            <span v-if="row.enabled">✅</span>
            <span v-else>❌</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="站点名称" />
        <el-table-column prop="site_name" label="标识" />
        <el-table-column label="分页支持" width="100">
          <template #default="{ row }">
            {{ row.support_page ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- 日志查看 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div style="display: flex; justify-content: space-between">
          <span>运行日志</span>
          <el-button size="small" @click="refreshLogs">刷新日志</el-button>
        </div>
      </template>
      <el-scrollbar height="300px">
        <pre style="font-size: 12px; line-height: 1.5; margin: 0">{{ logs }}</pre>
      </el-scrollbar>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { spiderAPI } from '@/api'

const status = ref({
  is_running: false,
  pid: null,
  uptime: null
})

const sites = ref([])
const logs = ref('暂无日志')
const operating = ref(false)
let refreshTimer = null

const formatUptime = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${hours}h ${minutes}m ${secs}s`
}

const refreshStatus = async () => {
  try {
    const res = await spiderAPI.getStatus()
    status.value = res.data
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const startSpider = async () => {
  operating.value = true
  try {
    const res = await spiderAPI.start()
    ElMessage.success(res.data.message || '爬虫启动成功')
    await refreshStatus()
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    operating.value = false
  }
}

const stopSpider = async () => {
  operating.value = true
  try {
    const res = await spiderAPI.stop()
    ElMessage.success(res.data.message || '爬虫停止成功')
    await refreshStatus()
  } catch (error) {
    ElMessage.error('停止失败')
  } finally {
    operating.value = false
  }
}

const loadSites = async () => {
  try {
    const res = await spiderAPI.getSites()
    sites.value = res.data.sites
  } catch (error) {
    console.error('加载站点失败:', error)
  }
}

const refreshLogs = async () => {
  try {
    const res = await spiderAPI.getLogs(100)
    if (res.data.logs && res.data.logs.length > 0) {
      logs.value = res.data.logs.join('')
    } else {
      logs.value = res.data.message || '暂无日志'
    }
  } catch (error) {
    logs.value = '加载日志失败: ' + error.message
  }
}

onMounted(() => {
  refreshStatus()
  loadSites()
  refreshLogs()
  
  // 定时刷新状态
  refreshTimer = setInterval(() => {
    refreshStatus()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

