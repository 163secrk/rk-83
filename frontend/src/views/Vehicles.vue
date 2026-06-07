<template>
  <div class="vehicles">
    <div class="page-header">
      <h2 class="page-title">车辆管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新增车辆
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-total">
              <el-icon :size="32"><Van /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ vehicleStats?.total || 0 }}</div>
              <div class="stat-label">车辆总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-maintenance">
              <el-icon :size="32"><Tools /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ vehicleStats?.withMaintenance || 0 }}</div>
              <div class="stat-label">有维保记录</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-total-mileage">
              <el-icon :size="32"><Odometer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatMileage(vehicleStats?.totalMileage || 0) }} km</div>
              <div class="stat-label">总里程数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <el-form :inline="true" class="search-form">
        <el-form-item label="所属客户">
          <el-select v-model="searchParams.customer_id" placeholder="全部客户" clearable @change="loadData" style="width: 180px">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="车牌号">
          <el-input v-model="searchParams.car_plate" placeholder="请输入车牌号" clearable @input="loadData" />
        </el-form-item>
      </el-form>

      <el-table :data="vehicles" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="客户信息" width="180">
          <template #default="{ row }">
            <div>
              <div class="customer-name">{{ row.customer?.name || '-' }}</div>
              <div class="customer-phone text-muted">{{ row.customer?.phone || '-' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="car_model" label="车型" min-width="180" />
        <el-table-column prop="car_plate" label="车牌号" width="120">
          <template #default="{ row }">
            <el-tag type="primary">{{ row.car_plate }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="vin" label="VIN码" width="180" show-overflow-tooltip />
        <el-table-column label="里程(km)" width="120">
          <template #default="{ row }">
            {{ formatMileage(row.mileage) }}
          </template>
        </el-table-column>
        <el-table-column prop="color" label="颜色" width="80" />
        <el-table-column label="购车日期" width="120">
          <template #default="{ row }">
            {{ row.purchase_date ? formatDate(row.purchase_date, 'date') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewMaintenance(row)">
              维保档案
            </el-button>
            <el-button type="success" size="small" @click="editVehicle(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="deleteVehicle(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="isEdit ? '编辑车辆' : '新增车辆'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="所属客户" prop="customer_id">
          <el-select v-model="form.customer_id" placeholder="请选择客户" style="width: 100%">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name + ' - ' + c.phone" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="车型" prop="car_model">
          <el-input v-model="form.car_model" placeholder="如：大众帕萨特 2023款" />
        </el-form-item>
        <el-form-item label="车牌号" prop="car_plate">
          <el-input v-model="form.car_plate" placeholder="如：京A12345" />
        </el-form-item>
        <el-form-item label="VIN码">
          <el-input v-model="form.vin" placeholder="车辆识别代码" />
        </el-form-item>
        <el-form-item label="当前里程">
          <el-input-number v-model="form.mileage" :min="0" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-input v-model="form.color" placeholder="如：黑色" />
        </el-form-item>
        <el-form-item label="购车日期">
          <el-date-picker v-model="form.purchase_date" type="date" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remarks" type="textarea" :rows="3" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确认{{ isEdit ? '修改' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { vehicleAPI, customerAPI } from '../api'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()

const vehicles = ref([])
const customerOptions = ref([])
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const searchParams = reactive({
  customer_id: null,
  car_plate: ''
})

const form = reactive({
  customer_id: null,
  car_model: '',
  car_plate: '',
  vin: '',
  mileage: 0,
  color: '',
  purchase_date: null,
  remarks: ''
})

const rules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  car_model: [{ required: true, message: '请输入车型', trigger: 'blur' }],
  car_plate: [{ required: true, message: '请输入车牌号', trigger: 'blur' }]
}

const vehicleStats = computed(() => {
  const total = vehicles.value.length
  const withMaintenance = vehicles.value.filter(v => v.mileage > 0).length
  const totalMileage = vehicles.value.reduce((sum, v) => sum + (v.mileage || 0), 0)
  return { total, withMaintenance, totalMileage }
})

const loadCustomers = async () => {
  try {
    const list = await customerAPI.getList()
    customerOptions.value = list
  } catch (error) {
    ElMessage.error('加载客户列表失败')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const list = await vehicleAPI.getList(searchParams)
    vehicles.value = list
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (date, type = 'datetime') => {
  if (type === 'date') {
    return dayjs(date).format('YYYY-MM-DD')
  }
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const formatMileage = (mileage) => {
  return mileage?.toLocaleString() || '0'
}

const viewMaintenance = (row) => {
  router.push(`/vehicles/${row.id}/maintenance`)
}

const editVehicle = (row) => {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    customer_id: row.customer_id,
    car_model: row.car_model,
    car_plate: row.car_plate,
    vin: row.vin || '',
    mileage: row.mileage || 0,
    color: row.color || '',
    purchase_date: row.purchase_date ? dayjs(row.purchase_date).toDate() : null,
    remarks: row.remarks || ''
  })
  showAddDialog.value = true
}

const deleteVehicle = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该车辆吗？删除后相关数据将无法恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await vehicleAPI.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await vehicleAPI.update(editId.value, form)
          ElMessage.success('修改成功')
        } else {
          await vehicleAPI.create(form)
          ElMessage.success('添加成功')
        }
        showAddDialog.value = false
        formRef.value.resetFields()
        loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  if (route.query.customer_id) {
    searchParams.customer_id = parseInt(route.query.customer_id)
  }
  loadCustomers()
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

.icon-maintenance {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.icon-total-mileage {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
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

.customer-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.customer-phone {
  font-size: 12px;
}

.text-muted {
  color: #909399;
}
</style>
