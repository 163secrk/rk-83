<template>
  <div class="technician-detail">
    <div class="page-header">
      <div>
        <h2 class="page-title">技师详情</h2>
        <div class="breadcrumb" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回技师列表</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <el-card v-if="technicianData" class="technician-info-card">
      <div class="technician-header">
        <div class="technician-avatar">
          <el-icon :size="40" color="#fff"><UserFilled /></el-icon>
        </div>
        <div class="technician-basic">
          <h3 class="technician-name">{{ technicianData.name }}</h3>
          <div class="technician-info-row">
            <el-tag type="primary" size="large">{{ technicianData.phone }}</el-tag>
            <el-tag :type="getSpecialtyType(technicianData.specialty)" size="large">
              {{ technicianData.specialty }}
            </el-tag>
            <el-tag :type="getStatusType(technicianData.status)" size="large">
              {{ getStatusText(technicianData.status) }}
            </el-tag>
            <span class="register-time">入职时间: {{ formatDate(technicianData.created_at) }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card stat-orders">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Tickets /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ monthStats?.completed_orders || 0 }}</div>
              <div class="stat-label">本月已完成工单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card stat-hours">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ monthStats?.total_hours || 0 }}h</div>
              <div class="stat-label">本月总工时</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card stat-income">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">¥{{ monthStats?.total_income || 0 }}</div>
              <div class="stat-label">本月总收入</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="filter-card">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="工单状态">
          <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="loadWorkOrders" style="width: 150px">
            <el-option label="已派单" value="assigned" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilters">重置筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="work-orders-section">
      <div class="section-header">
        <h4 class="section-title">
          <el-icon><Tickets /></el-icon>
          工单列表
        </h4>
      </div>

      <el-table :data="workOrders" v-loading="loadingOrders" border>
        <el-table-column prop="id" label="工单号" width="80" />
        <el-table-column label="客户" width="150">
          <template #default="{ row }">
            {{ row.appointment?.customer?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="服务类型" width="120">
          <template #default="{ row }">
            {{ row.appointment?.service_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开始时间" width="160">
          <template #default="{ row }">
            {{ row.actual_start ? formatDate(row.actual_start) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="结束时间" width="160">
          <template #default="{ row }">
            {{ row.actual_end ? formatDate(row.actual_end) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="工时(h)" width="100" align="center">
          <template #default="{ row }">
            {{ calculateHours(row.actual_start, row.actual_end) }}
          </template>
        </el-table-column>
        <el-table-column prop="labor_cost" label="工时费" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.labor_cost || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="总金额" width="100" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ row.total_amount || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewWorkOrder(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loadingOrders && workOrders.length === 0" class="empty-orders">
        <el-empty description="暂无工单记录" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { technicianAPI, workOrderAPI } from '../api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const technicianId = route.params.id
const technicianData = ref(null)
const monthStats = ref(null)
const workOrders = ref([])
const loading = ref(false)
const loadingOrders = ref(false)
const statusFilter = ref('')

const loadData = async () => {
  loading.value = true
  try {
    const data = await technicianAPI.getDetail(technicianId)
    technicianData.value = data
    monthStats.value = data.month_stats
  } catch (error) {
    ElMessage.error('加载技师详情失败')
  } finally {
    loading.value = false
  }
}

const loadWorkOrders = async () => {
  loadingOrders.value = true
  try {
    const data = await technicianAPI.getWorkOrders(technicianId, statusFilter.value || undefined)
    workOrders.value = data
  } catch (error) {
    ElMessage.error('加载工单列表失败')
  } finally {
    loadingOrders.value = false
  }
}

const resetFilters = () => {
  statusFilter.value = ''
  loadWorkOrders()
}

const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const calculateHours = (start, end) => {
  if (!start || !end) return '-'
  const hours = dayjs(end).diff(dayjs(start), 'hour', true)
  return hours.toFixed(2)
}

const getStatusType = (status) => {
  const types = {
    available: 'success',
    busy: 'warning',
    off_duty: 'info',
    assigned: 'warning',
    in_progress: 'primary',
    completed: 'success'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    available: '空闲',
    busy: '工作中',
    off_duty: '休息',
    assigned: '已派单',
    in_progress: '进行中',
    completed: '已完成'
  }
  return texts[status] || status
}

const getSpecialtyType = (specialty) => {
  const types = {
    '机修': 'primary',
    '钣金': 'warning',
    '喷漆': 'danger',
    '电器': 'success',
    '轮胎': 'info',
    '空调': '',
    '综合维修': 'warning'
  }
  return types[specialty] || ''
}

const viewWorkOrder = (row) => {
  router.push(`/work-orders/${row.id}`)
}

const goBack = () => {
  router.push('/technicians')
}

onMounted(() => {
  loadData()
  loadWorkOrders()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  color: #303133;
  margin: 0 0 8px 0;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.3s;
}

.breadcrumb:hover {
  color: #409EFF;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.technician-info-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.technician-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.technician-avatar {
  width: 70px;
  height: 70px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.technician-basic {
  flex: 1;
}

.technician-name {
  font-size: 22px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 12px 0;
}

.technician-info-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.register-time {
  font-size: 13px;
  color: #909399;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  border: none;
}

.stat-orders {
  border-left: 4px solid #409eff;
}

.stat-hours {
  border-left: 4px solid #e6a23c;
}

.stat-income {
  border-left: 4px solid #67c23a;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-orders .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-hours .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-income .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.filter-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.work-orders-section {
  border-radius: 8px;
  border: none;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.section-title .el-icon {
  color: #409EFF;
}

.amount {
  font-weight: 600;
  color: #f56c6c;
}

.empty-orders {
  padding: 40px 0;
}
</style>
