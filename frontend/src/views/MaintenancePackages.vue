<template>
  <div class="maintenance-packages">
    <div class="page-header">
      <h2 class="page-title">保养套餐管理</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon>
        新增套餐
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索套餐名称/描述"
            clearable
            style="width: 200px"
            @keyup.enter="loadData"
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
      <el-table :data="packages" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="套餐名称" width="180" />
        <el-table-column prop="description" label="套餐描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="包含服务" min-width="180">
          <template #default="{ row }">
            <div class="service-tags">
              <el-tag
                v-for="(service, idx) in row.services"
                :key="idx"
                size="small"
                type="primary"
                effect="light"
                style="margin-right: 4px; margin-bottom: 4px"
              >
                {{ service.service_type }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="包含配件" min-width="200">
          <template #default="{ row }">
            <div class="part-list">
              <span
                v-for="(part, idx) in row.parts"
                :key="idx"
                class="part-item"
              >
                {{ part.part.name }} x{{ part.quantity }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="package_price" label="套餐价" width="120">
          <template #default="{ row }">
            <span class="package-price">¥{{ row.package_price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active === 1 ? 'success' : 'info'">
              {{ row.is_active === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              :type="row.is_active === 1 ? 'warning' : 'success'"
              size="small"
              @click="toggleActive(row)"
            >
              {{ row.is_active === 1 ? '停用' : '启用' }}
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deletePackage(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="showDialog"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="套餐名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入套餐名称" />
        </el-form-item>
        <el-form-item label="套餐描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入套餐描述"
          />
        </el-form-item>
        <el-form-item label="套餐价" prop="package_price">
          <el-input-number
            v-model="form.package_price"
            :min="0"
            :precision="2"
            style="width: 100%"
          />
        </el-form-item>

        <el-divider content-position="left">包含服务项目</el-divider>
        <el-form-item label="服务项目">
          <div class="service-section">
            <el-select
              v-model="selectedService"
              placeholder="选择服务类型"
              style="width: 200px; margin-right: 10px"
            >
              <el-option label="常规保养" value="常规保养" />
              <el-option label="大保养" value="大保养" />
              <el-option label="维修服务" value="维修服务" />
              <el-option label="钣金喷漆" value="钣金喷漆" />
              <el-option label="轮胎更换" value="轮胎更换" />
              <el-option label="空调维修" value="空调维修" />
              <el-option label="其他服务" value="其他服务" />
            </el-select>
            <el-button type="primary" @click="addService">
              <el-icon><Plus /></el-icon>
              添加
            </el-button>
          </div>
          <div class="selected-services" style="margin-top: 10px">
            <el-tag
              v-for="(service, idx) in form.services"
              :key="idx"
              closable
              type="primary"
              effect="light"
              style="margin-right: 8px; margin-bottom: 8px"
              @close="removeService(idx)"
            >
              {{ service.service_type }}
            </el-tag>
            <span v-if="form.services.length === 0" class="empty-tip">
              暂无服务项目，请添加
            </span>
          </div>
        </el-form-item>

        <el-divider content-position="left">包含配件列表</el-divider>
        <el-form-item label="配件列表">
          <div class="part-section">
            <el-select
              v-model="selectedPartId"
              placeholder="选择配件"
              filterable
              style="width: 300px; margin-right: 10px"
            >
              <el-option
                v-for="part in availableParts"
                :key="part.id"
                :label="`${part.name} (${part.code}) - ¥${part.price}`"
                :value="part.id"
              />
            </el-select>
            <el-input-number
              v-model="selectedPartQuantity"
              :min="1"
              :max="100"
              style="width: 120px; margin-right: 10px"
            />
            <el-button type="primary" @click="addPart">
              <el-icon><Plus /></el-icon>
              添加
            </el-button>
          </div>
          <el-table
            :data="form.parts"
            border
            size="small"
            style="margin-top: 10px"
            v-if="form.parts.length > 0"
          >
            <el-table-column prop="part_id" label="配件ID" width="80" />
            <el-table-column label="配件名称">
              <template #default="{ row }">
                {{ getPartName(row.part_id) }}
              </template>
            </el-table-column>
            <el-table-column label="配件编码" width="120">
              <template #default="{ row }">
                {{ getPartCode(row.part_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="100" />
            <el-table-column label="操作" width="100">
              <template #default="{ $index }">
                <el-button type="danger" size="small" @click="removePart($index)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <span v-else class="empty-tip">
            暂无配件，请添加
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? '保存修改' : '确认添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { packageAPI, partAPI } from '../api'

const packages = ref([])
const availableParts = ref([])
const loading = ref(false)
const submitting = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const selectedService = ref('')
const selectedPartId = ref(null)
const selectedPartQuantity = ref(1)

const filters = reactive({
  is_active: null,
  keyword: ''
})

const form = reactive({
  name: '',
  description: '',
  package_price: 0,
  is_active: 1,
  services: [],
  parts: []
})

const rules = {
  name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  package_price: [{ required: true, message: '请输入套餐价', trigger: 'blur' }]
}

const dialogTitle = computed(() => {
  return isEdit.value ? '编辑套餐' : '新增套餐'
})

const getPartName = (partId) => {
  const part = availableParts.value.find(p => p.id === partId)
  return part ? part.name : '未知配件'
}

const getPartCode = (partId) => {
  const part = availableParts.value.find(p => p.id === partId)
  return part ? part.code : ''
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.is_active !== null && filters.is_active !== '') {
      params.is_active = filters.is_active
    }
    if (filters.keyword) params.keyword = filters.keyword
    
    packages.value = await packageAPI.getList(params)
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadParts = async () => {
  try {
    availableParts.value = await partAPI.getList()
  } catch (error) {
    ElMessage.error('加载配件列表失败')
  }
}

const resetFilters = () => {
  filters.is_active = null
  filters.keyword = ''
  loadData()
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    package_price: 0,
    is_active: 1,
    services: [],
    parts: []
  })
  selectedService.value = ''
  selectedPartId.value = null
  selectedPartQuantity.value = 1
}

const openAddDialog = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  loadParts()
  showDialog.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    package_price: row.package_price,
    is_active: row.is_active,
    services: [...row.services],
    parts: [...row.parts]
  })
  loadParts()
  showDialog.value = true
}

const addService = () => {
  if (!selectedService.value) {
    ElMessage.warning('请选择服务类型')
    return
  }
  const exists = form.services.some(s => s.service_type === selectedService.value)
  if (exists) {
    ElMessage.warning('该服务类型已添加')
    return
  }
  form.services.push({ service_type: selectedService.value })
  selectedService.value = ''
}

const removeService = (index) => {
  form.services.splice(index, 1)
}

const addPart = () => {
  if (!selectedPartId.value) {
    ElMessage.warning('请选择配件')
    return
  }
  if (!selectedPartQuantity.value || selectedPartQuantity.value <= 0) {
    ElMessage.warning('请输入有效数量')
    return
  }
  const exists = form.parts.some(p => p.part_id === selectedPartId.value)
  if (exists) {
    ElMessage.warning('该配件已添加')
    return
  }
  form.parts.push({
    part_id: selectedPartId.value,
    quantity: selectedPartQuantity.value
  })
  selectedPartId.value = null
  selectedPartQuantity.value = 1
}

const removePart = (index) => {
  form.parts.splice(index, 1)
}

const submitForm = async () => {
  if (!formRef.value) return
  
  if (form.services.length === 0) {
    ElMessage.warning('请至少添加一个服务项目')
    return
  }
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await packageAPI.update(editingId.value, form)
          ElMessage.success('修改成功')
        } else {
          await packageAPI.create(form)
          ElMessage.success('添加成功')
        }
        showDialog.value = false
        resetForm()
        loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const toggleActive = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active === 1 ? '停用' : '启用'}该套餐吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await packageAPI.toggleActive(row.id)
    ElMessage.success(row.is_active === 1 ? '已停用' : '已启用')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

const deletePackage = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该套餐吗？删除后无法恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await packageAPI.delete(row.id)
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

.service-tags {
  display: flex;
  flex-wrap: wrap;
}

.part-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.part-item {
  font-size: 13px;
  color: #606266;
}

.package-price {
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}

.service-section,
.part-section {
  display: flex;
  align-items: center;
}

.selected-services {
  min-height: 32px;
}

.empty-tip {
  color: #c0c4cc;
  font-size: 13px;
}

:deep(.el-divider__text) {
  background: #fff;
  font-weight: 600;
  color: #303133;
}
</style>
