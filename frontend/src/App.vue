<template>
  <div id="app">
    <el-container style="height: 100vh">
      <!-- 侧边栏 -->
      <el-aside width="200px" style="background-color: #304156">
        <div style="padding: 20px; color: #fff; font-size: 20px; font-weight: bold">
          🌐 nb_proxypool
        </div>
        <el-menu
          :default-active="$route.path"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <template #title>
              <span>📊 仪表盘</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/proxies">
            <template #title>
              <span>🌐 代理管理</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/spider">
            <template #title>
              <span>🕷️ 爬虫控制</span>
            </template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header style="background-color: #fff; box-shadow: 0 1px 4px rgba(0,21,41,.08)">
          <h2 style="margin: 0; line-height: 60px">{{ pageTitle }}</h2>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => {
  const titles = {
    '/': '仪表盘',
    '/proxies': '代理管理',
    '/spider': '爬虫控制'
  }
  return titles[route.path] || 'nb_proxypool'
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100%;
}
</style>

