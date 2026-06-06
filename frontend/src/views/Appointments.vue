<template>
  <div class="appointments">
    <div class="page-header">
      <h2 class="page-title">预约管理</h2>
      <el-button type="primary" @click="goToAppointment">
        <el-icon><Plus /></el-icon>
        新增预约
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="待确认" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
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
      <el-table :data="appointments" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="车主信息" width="180">
          <template #default="{ row }">
            <div>{{ row.customer.name }}</div>
            <div class="sub-text">{{ row.customer.phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="车辆信息" width="180">
          <template #default="{ row }">
            <div>{{ row.customer.car_model }}</div>
            <div class="sub-text">{{ row.customer.car_plate }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="service_type" label="服务类型" width="120" />
        <el-table-column label="预约时间" width="160">
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
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="createWorkOrder(row)"
              :disabled="row.status !== 'pending'"
            >
              <el-icon><Tickets /></el-icon>
              创建工单
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="confirmAppointment(row)"
              :disabled="row.status !== 'pending'"
            >
              确认
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteAppointment(row)"
              :disabled="row.status === 'completed'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="workOrderDialogVisible" title="创建工单" width="500px">
      <el-form :model="workOrderForm" label-width="100px">
        <el-form-item label="选择技师" prop="technician_id">
          <el-select
            v-model="workOrderForm.technician_id"
            placeholder="请选择技师"
            style="width: 100%"
          >
            <el-option
              v-for="tech in availableTechnicians"
              :key="tech.id"
              :label="`${tech.name} - ${tech.specialty}`"
              :value="tech.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="workOrderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitWorkOrder" :loading="submitting">
          确认创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appointmentAPI, technicianAPI, workOrderAPI } from '../api'
import dayjs from 'dayjs'

const router = useRouter()

const appointments = ref([])
const loading = ref(false)
const submitting = ref(false)
const workOrderDialogVisible = ref(false)
const currentAppointment = ref(null)
const availableTechnicians = ref([])

const filters = reactive({
  status: '',
  dateRange: []
})

const workOrderForm = reactive({
  appointment_id: 0,
  technician_id: null
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }
    appointments.value = await appointmentAPI.getList(params)
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadTechnicians = async () => {
  try {
    availableTechnicians.value = await technicianAPI.getList({ status: 'available' })
  } catch (error) {
    ElMessage.error('加载技师列表失败')
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

const goToAppointment = () => {
  router.push('/appointment')
}

const resetFilters = () => {
  filters.status = ''
  filters.dateRange = []
  loadData()
}

const confirmAppointment = async (row) => {
  try {
    await appointmentAPI.update(row.id, { status: 'confirmed' })
    ElMessage.success('预约已确认')
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const createWorkOrder = async (row) => {
  currentAppointment.value = row
  workOrderForm.appointment_id = row.id
  workOrderForm.technician_id = null
  await loadTechnicians()
  workOrderDialogVisible.value = true
}

const submitWorkOrder = async () => {
  if (!workOrderForm.technician_id) {
    ElMessage.warning('请选择技师')
    return
  }
  
  submitting.value = true
  try {
    await workOrderAPI.create(workOrderForm)
    ElMessage.success('工单创建成功')
    workOrderDialogVisible.value = false
    loadData()
    router.push('/work-orders')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

const deleteAppointment = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该预约吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await appointmentAPI.delete(row.id)
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
