<template>
  <div class="customers">
    <div class="page-header">
      <h2 class="page-title">客户管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新增客户
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-total">
              <el-icon :size="32"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ customerStats?.total || 0 }}</div>
              <div class="stat-label">客户总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-vehicles">
              <el-icon :size="32"><Van /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ customerStats?.totalVehicles || 0 }}</div>
              <div class="stat-label">车辆总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-revenue">
              <el-icon :size="32"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">¥{{ formatMoney(customerStats?.totalCost || 0) }}</div>
              <div class="stat-label">累计消费</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <el-form :inline="true" class="search-form">
        <el-form-item label="客户姓名">
          <el-input v-model="searchParams.name" placeholder="请输入姓名" clearable @input="loadData" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="searchParams.phone" placeholder="请输入手机号" clearable @input="loadData" />
        </el-form-item>
      </el-form>

      <el-table :data="customers" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column label="车辆数" width="100">
          <template #default="{ row }">
            <el-tag type="primary">{{ row.vehicles?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="车辆信息">
          <template #default="{ row }">
            <div v-if="row.vehicles?.length" class="vehicle-list">
              <div v-for="v in row.vehicles" :key="v.id" class="vehicle-item">
                <span class="car-model">{{ v.car_model }}</span>
                <el-tag size="small" type="info">{{ v.car_plate }}</el-tag>
              </div>
            </div>
            <span v-else class="text-muted">暂无车辆</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              查看详情
            </el-button>
            <el-button type="success" size="small" @click="manageVehicles(row)">
              车辆管理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" title="新增客户" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入客户姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确认添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { customerAPI, vehicleAPI } from '../api'
import dayjs from 'dayjs'

const router = useRouter()
const customers = ref([])
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const formRef = ref(null)

const searchParams = reactive({
  name: '',
  phone: ''
})

const form = reactive({
  name: '',
  phone: ''
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const customerStats = computed(() => {
  const total = customers.value.length
  const totalVehicles = customers.value.reduce((sum, c) => sum + (c.vehicles?.length || 0), 0)
  const totalCost = 0
  return { total, totalVehicles, totalCost }
})

const loadData = async () => {
  loading.value = true
  try {
    const list = await customerAPI.getList(searchParams)
    customers.value = list
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const formatMoney = (num) => {
  return num.toFixed(2)
}

const viewDetail = (row) => {
  router.push(`/customers/${row.id}`)
}

const manageVehicles = (row) => {
  router.push({ path: '/vehicles', query: { customer_id: row.id } })
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await customerAPI.create(form)
        ElMessage.success('添加成功')
        showAddDialog.value = false
        formRef.value.resetFields()
        loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '添加失败')
      } finally {
        submitting.value = false
      }
    }
  })
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

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  border: none;
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

.icon-total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.icon-vehicles {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.table-card {
  border-radius: 8px;
  border: none;
}

.search-form {
  margin-bottom: 20px;
}

.vehicle-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.vehicle-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.car-model {
  font-size: 13px;
  color: #303133;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}
</style>
