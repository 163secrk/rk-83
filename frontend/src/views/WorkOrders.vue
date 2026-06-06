<template>
  <div class="work-orders">
    <div class="page-header">
      <h2 class="page-title">工单管理</h2>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="已派单" value="assigned" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="技师">
          <el-select v-model="filters.technician_id" placeholder="全部技师" clearable style="width: 180px">
            <el-option
              v-for="tech in technicians"
              :key="tech.id"
              :label="tech.name"
              :value="tech.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="workOrders" v-loading="loading" border>
        <el-table-column prop="id" label="工单号" width="80" />
        <el-table-column label="车主信息" width="160">
          <template #default="{ row }">
            <div>{{ row.appointment.customer.name }}</div>
            <div class="sub-text">{{ row.appointment.customer.phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="车辆信息" width="160">
          <template #default="{ row }">
            <div>{{ row.appointment.customer.car_model }}</div>
            <div class="sub-text">{{ row.appointment.customer.car_plate }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="appointment.service_type" label="服务类型" width="120" />
        <el-table-column prop="technician.name" label="技师" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="总费用" width="120">
          <template #default="{ row }">
            ¥{{ row.total_amount.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteOrder(row)"
              :disabled="['in_progress', 'completed'].includes(row.status)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workOrderAPI, technicianAPI } from '../api'
import dayjs from 'dayjs'

const router = useRouter()

const workOrders = ref([])
const technicians = ref([])
const loading = ref(false)

const filters = reactive({
  status: '',
  technician_id: null
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.technician_id) params.technician_id = filters.technician_id
    
    workOrders.value = await workOrderAPI.getList(params)
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadTechnicians = async () => {
  try {
    technicians.value = await technicianAPI.getList()
  } catch (error) {
    ElMessage.error('加载技师列表失败')
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const getStatusType = (status) => {
  const types = {
    assigned: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    assigned: '已派单',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const resetFilters = () => {
  filters.status = ''
  filters.technician_id = null
  loadData()
}

const viewDetail = (row) => {
  router.push(`/work-orders/${row.id}`)
}

const deleteOrder = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该工单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await workOrderAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadData()
  loadTechnicians()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  color: #303133;
  margin: 0;
}

.filter-card,
.table-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.sub-text {
  font-size: 12px;
  color: #909399;
}
</style>
