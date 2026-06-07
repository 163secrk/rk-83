<template>
  <div class="technicians">
    <div class="page-header">
      <h2 class="page-title">技师管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新增技师
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-total">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ techStats?.total || 0 }}</div>
              <div class="stat-label">技师总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-available">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ techStats?.available || 0 }}</div>
              <div class="stat-label">空闲中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-busy">
              <el-icon :size="32"><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ techStats?.busy || 0 }}</div>
              <div class="stat-label">工作中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-off">
              <el-icon :size="32"><Moon /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ techStats?.off_duty || 0 }}</div>
              <div class="stat-label">休息中</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="专长">
          <el-select v-model="filters.specialty" placeholder="全部" clearable style="width: 150px" @change="loadData">
            <el-option label="机修" value="机修" />
            <el-option label="钣金" value="钣金" />
            <el-option label="喷漆" value="喷漆" />
            <el-option label="电器" value="电器" />
            <el-option label="轮胎" value="轮胎" />
            <el-option label="空调" value="空调" />
            <el-option label="综合维修" value="综合维修" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 150px" @change="loadData">
            <el-option label="空闲" value="available" />
            <el-option label="工作中" value="busy" />
            <el-option label="休息" value="off_duty" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="filters.sort_by" style="width: 150px" @change="loadData">
            <el-option label="按工作量" value="workload" />
            <el-option label="按工时" value="hours" />
            <el-option label="按收入" value="income" />
            <el-option label="按姓名" value="name" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="technicians" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column prop="specialty" label="专长" width="120" />
        <el-table-column label="本月工单数" width="120" align="center">
          <template #default="{ row }">
            <span class="stat-number">{{ row.month_stats?.completed_orders || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="本月工时" width="120" align="center">
          <template #default="{ row }">
            <span class="stat-number">{{ row.month_stats?.total_hours || 0 }}h</span>
          </template>
        </el-table-column>
        <el-table-column label="本月收入" width="120" align="center">
          <template #default="{ row }">
            <span class="stat-income">¥{{ row.month_stats?.total_income || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              详情
            </el-button>
            <el-dropdown @command="(cmd) => changeStatus(row, cmd)">
              <el-button type="success" size="small">
                更改状态
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="available">空闲</el-dropdown-item>
                  <el-dropdown-item command="busy">工作中</el-dropdown-item>
                  <el-dropdown-item command="off_duty">休息</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="danger" size="small" @click="deleteTech(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" title="新增技师" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入技师姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="专长" prop="specialty">
          <el-select v-model="form.specialty" placeholder="请选择专长" style="width: 100%">
            <el-option label="机修" value="机修" />
            <el-option label="钣金" value="钣金" />
            <el-option label="喷漆" value="喷漆" />
            <el-option label="电器" value="电器" />
            <el-option label="轮胎" value="轮胎" />
            <el-option label="空调" value="空调" />
            <el-option label="综合维修" value="综合维修" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="空闲" value="available" />
            <el-option label="休息" value="off_duty" />
          </el-select>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { technicianAPI } from '../api'
import dayjs from 'dayjs'

const router = useRouter()

const technicians = ref([])
const techStats = ref(null)
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const formRef = ref(null)

const filters = reactive({
  specialty: '',
  status: '',
  sort_by: 'workload'
})

const form = reactive({
  name: '',
  phone: '',
  specialty: '',
  status: 'available'
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  specialty: [{ required: true, message: '请选择专长', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.specialty) params.specialty = filters.specialty
    if (filters.status) params.status = filters.status
    if (filters.sort_by) params.sort_by = filters.sort_by
    
    const [list, stats] = await Promise.all([
      technicianAPI.getList(params),
      technicianAPI.getStatistics()
    ])
    technicians.value = list
    techStats.value = stats
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.specialty = ''
  filters.status = ''
  filters.sort_by = 'workload'
  loadData()
}

const viewDetail = (row) => {
  router.push(`/technicians/${row.id}`)
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const getStatusType = (status) => {
  const types = {
    available: 'success',
    busy: 'warning',
    off_duty: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    available: '空闲',
    busy: '工作中',
    off_duty: '休息'
  }
  return texts[status] || status
}

const changeStatus = async (row, status) => {
  try {
    await technicianAPI.updateStatus(row.id, status)
    ElMessage.success('状态已更新')
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await technicianAPI.create(form)
        ElMessage.success('添加成功')
        showAddDialog.value = false
        formRef.value.resetFields()
        form.status = 'available'
        loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '添加失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const deleteTech = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该技师吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await technicianAPI.delete(row.id)
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

.icon-available {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.icon-busy {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.icon-off {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #666;
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

.filter-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  border-radius: 8px;
  border: none;
}

.stat-number {
  font-weight: 600;
  color: #409eff;
  font-size: 16px;
}

.stat-income {
  font-weight: 600;
  color: #67c23a;
  font-size: 16px;
}
</style>
