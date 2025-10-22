<template>
  <div>
    <!-- 工具栏 -->
    <el-row :gutter="10" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-input v-model="searchKeyword" placeholder="搜索 IP 或城市" clearable @change="loadProxies" />
      </el-col>
      <el-col :span="4">
        <el-select v-model="filterCountry" placeholder="按国家筛选" clearable @change="loadProxies">
          <el-option label="全部" value="" />
          <el-option v-for="c in countries" :key="c" :label="c" :value="c" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="loadProxies">🔄 刷新</el-button>
      </el-col>
    </el-row>

    <!-- 代理列表 -->
    <el-table :data="proxies" v-loading="loading" height="600">
      <el-table-column label="国旗" width="60">
        <template #default="{ row }">
          <span style="font-size: 24px">{{ row.flag || '🏳️' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="代理地址" width="200">
        <template #default="{ row }">
          <code>{{ row.http || row.https }}</code>
        </template>
      </el-table-column>
      <el-table-column prop="country_name" label="国家" width="120" />
      <el-table-column prop="city" label="城市" width="120" />
      <el-table-column prop="platform" label="来源" width="120" />
      <el-table-column label="状态" width="100">
        <template #default>
          <el-tag type="success">✅ 在线</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="testProxy(row)">测试</el-button>
          <el-button size="small" type="danger" @click="deleteProxy(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 20px; justify-content: flex-end"
      @current-change="loadProxies"
      @size-change="loadProxies"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { proxyAPI } from '@/api'

const proxies = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterCountry = ref('')
const countries = ref(['CN', 'US', 'JP', 'KR', 'GB', 'FR', 'DE'])

const loadProxies = async () => {
  loading.value = true
  try {
    const res = await proxyAPI.getProxies({
      page: page.value,
      size: pageSize.value,
      country: filterCountry.value || undefined,
      keyword: searchKeyword.value || undefined
    })
    proxies.value = res.data.data
    total.value = res.data.total
  } catch (error) {
    ElMessage.error('加载代理列表失败')
  } finally {
    loading.value = false
  }
}

const testProxy = async (row) => {
  try {
    const proxyUrl = row.http || row.https
    ElMessage.info('正在测试代理...')
    const res = await proxyAPI.testProxy(proxyUrl)
    ElMessage({
      type: res.data.is_valid ? 'success' : 'error',
      message: res.data.status
    })
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const deleteProxy = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个代理吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const proxyUrl = row.http || row.https
    const match = proxyUrl.match(/(\d+\.\d+\.\d+\.\d+):(\d+)/)
    if (match) {
      const proxyId = `${match[1]}:${match[2]}`
      await proxyAPI.deleteProxy(proxyId)
      ElMessage.success('删除成功')
      loadProxies()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadProxies()
  setInterval(loadProxies, 60000) // 每分钟刷新
})
</script>

