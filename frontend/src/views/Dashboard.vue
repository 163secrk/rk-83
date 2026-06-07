<template>
  <div class="dashboard">
    <h2 class="page-title">数据概览</h2>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card stat-blue">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.total_appointments || 0 }}</div>
              <div class="stat-label">总预约数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-orange">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.pending_appointments || 0 }}</div>
              <div class="stat-label">待处理预约</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-green">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Tickets /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.in_progress_work_orders || 0 }}</div>
              <div class="stat-label">进行中工单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-purple">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">¥{{ (stats?.total_revenue || 0).toFixed(2) }}</div>
              <div class="stat-label">总营收</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card stat-cyan">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Sunny /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.today_appointments || 0 }}</div>
              <div class="stat-label">今日预约</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-pink">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.completed_work_orders || 0 }}</div>
              <div class="stat-label">已完成工单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-lime">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Goods /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.total_parts || 0 }}</div>
              <div class="stat-label">配件种类</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card 
          class="stat-card stat-red clickable" 
          v-if="stats?.low_stock_parts > 0"
          @click="showLowStockDialog = true"
        >
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.low_stock_parts || 0 }}</div>
              <div class="stat-label">库存预警 <span class="view-detail">点击查看</span></div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card stat-green" v-else>
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">0</div>
              <div class="stat-label">库存预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div class="card-header">
              <span>最近预约</span>
              <el-button type="primary" size="small" @click="$router.push('/appointments')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentAppointments" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="customer.name" label="车主" />
            <el-table-column prop="service_type" label="服务类型" />
            <el-table-column prop="appointment_date" label="预约时间">
              <template #default="{ row }">
                {{ formatDate(row.appointment_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div class="card-header">
              <span>最近工单</span>
              <el-button type="primary" size="small" @click="$router.push('/work-orders')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentWorkOrders" v-loading="loading">
            <el-table-column prop="id" label="工单号" width="80" />
            <el-table-column prop="appointment.customer.name" label="车主" />
            <el-table-column prop="appointment.service_type" label="服务类型" />
            <el-table-column prop="technician.name" label="技师" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getWorkOrderStatusType(row.status)">
                  {{ getWorkOrderStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showLowStockDialog" title="库存预警详情" width="700px" top="5vh">
      <el-alert
        title="以下配件库存已低于安全线，请及时补货！"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-table :data="stats?.low_stock_parts_list || []" border empty-text="暂无预警配件">
        <el-table-column prop="code" label="配件编码" width="120" />
        <el-table-column prop="name" label="配件名称" />
        <el-table-column prop="specification" label="规格型号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column label="当前库存" width="120">
          <template #default="{ row }">
            <el-tag type="danger" size="large">
              {{ row.stock }} {{ row.unit }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="安全库存" width="100">
          <template #default="{ row }">
            {{ row.min_stock }} {{ row.unit }}
          </template>
        </el-table-column>
        <el-table-column label="差额" width="100">
          <template #default="{ row }">
            <span class="shortage">-{{ row.min_stock - row.stock }}</span>
          </template>
        </el-table-column>
        <el-table-column label="单价" width="100">
          <template #default="{ row }">
            ¥{{ row.price.toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showLowStockDialog = false">关闭</el-button>
        <el-button type="primary" @click="$router.push('/parts')">
          前往配件管理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { workOrderAPI, appointmentAPI } from '../api'
import dayjs from 'dayjs'

const stats = ref(null)
const recentAppointments = ref([])
const recentWorkOrders = ref([])
const loading = ref(false)
const showLowStockDialog = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    const [statsData, apptData, woData] = await Promise.all([
      workOrderAPI.getDashboardStats(),
      appointmentAPI.getList(),
      workOrderAPI.getList()
    ])
    stats.value = statsData
    recentAppointments.value = apptData.slice(0, 5)
    recentWorkOrders.value = woData.slice(0, 5)
  } catch (error) {
    console.error('加载数据失败', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    confirmed: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待确认',
    confirmed: '已确认',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getWorkOrderStatusType = (status) => {
  const types = {
    assigned: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getWorkOrderStatusText = (status) => {
  const texts = {
    assigned: '已派单',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  font-size: 24px;
  margin-bottom: 20px;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.view-detail {
  font-size: 12px;
  color: #409eff;
  margin-left: 8px;
  text-decoration: underline;
}

.shortage {
  color: #f56c6c;
  font-weight: bold;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-blue .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-orange .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-green .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-purple .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-cyan .stat-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-pink .stat-icon {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #333;
}

.stat-lime .stat-icon {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.stat-red .stat-icon {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.panel-card {
  border-radius: 8px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>
