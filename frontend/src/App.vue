<template>
  <el-container class="app-container">
    <el-header class="header">
      <div class="header-content">
        <h1 class="title">
          <el-icon :size="32" color="#409EFF"><Service /></el-icon>
          汽车4S店售后保养预约系统
        </h1>
      </div>
    </el-header>
    <el-container>
      <el-aside width="220px" class="aside">
        <el-menu
          :default-active="$route.path"
          class="menu"
          router
          background-color="#001529"
          text-color="#fff"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据概览</span>
          </el-menu-item>
          <el-menu-item index="/appointment">
            <el-icon><Calendar /></el-icon>
            <span>在线预约</span>
          </el-menu-item>
          <el-menu-item index="/appointments">
            <el-icon><List /></el-icon>
            <span>预约管理</span>
          </el-menu-item>
          <el-menu-item index="/work-orders">
            <el-icon><Tickets /></el-icon>
            <span>工单管理</span>
          </el-menu-item>
          <el-menu-item index="/customers">
            <el-icon><UserFilled /></el-icon>
            <span>客户管理</span>
          </el-menu-item>
          <el-menu-item index="/vehicles">
            <el-icon><Van /></el-icon>
            <span>车辆管理</span>
          </el-menu-item>
          <el-menu-item index="/technicians">
            <el-icon><User /></el-icon>
            <span>技师管理</span>
          </el-menu-item>
          <el-menu-item index="/parts">
            <el-icon><Goods /></el-icon>
            <span>配件库存</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  height: 100vh;
}

.header {
  background: linear-gradient(90deg, #1890ff 0%, #096dd9 100%);
  color: white;
  padding: 0;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  padding: 0 24px;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  font-size: 22px;
  margin: 0;
}

.aside {
  background: #001529;
  height: calc(100vh - 60px);
}

.menu {
  border-right: none;
}

.main {
  background: #f0f2f5;
  padding: 24px;
  overflow-y: auto;
}

:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.2) !important;
}
</style>
