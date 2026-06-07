<template>
  <div class="parts">
    <div class="page-header">
      <h2 class="page-title">配件库存管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新增配件
      </el-button>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-total">
              <el-icon :size="32"><Goods /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ inventoryStats?.total_parts || 0 }}</div>
              <div class="stat-label">配件种类</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-value">
              <el-icon :size="32"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">¥{{ (inventoryStats?.total_value || 0).toFixed(2) }}</div>
              <div class="stat-label">库存总值</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" v-if="inventoryStats?.low_stock > 0">
          <div class="stat-content">
            <div class="stat-icon icon-warning">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ inventoryStats?.low_stock || 0 }}</div>
              <div class="stat-label">库存预警</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" v-else>
          <div class="stat-content">
            <div class="stat-icon icon-ok">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">0</div>
              <div class="stat-label">库存预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" v-if="inventoryStats?.out_of_stock > 0">
          <div class="stat-content">
            <div class="stat-icon icon-danger">
              <el-icon :size="32"><Close /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ inventoryStats?.out_of_stock || 0 }}</div>
              <div class="stat-label">缺货</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card" v-else>
          <div class="stat-content">
            <div class="stat-icon icon-ok">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">0</div>
              <div class="stat-label">缺货</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable style="width: 140px">
            <el-option
              v-for="cat in categories"
              :key="cat"
              :label="cat"
              :value="cat"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="库存预警">
          <el-switch v-model="filters.low_stock" active-text="仅显示预警" />
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索配件名称/编码"
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
      <el-table :data="parts" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="code" label="配件编码" width="120" />
        <el-table-column prop="name" label="配件名称" />
        <el-table-column prop="specification" label="规格型号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="price" label="单价" width="120">
          <template #default="{ row }">
            ¥{{ row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.stock <= row.min_stock ? 'danger' : 'success'"
            >
              {{ row.stock }} {{ row.unit }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="min_stock" label="预警值" width="100" />
        <el-table-column label="库存价值" width="120">
          <template #default="{ row }">
            ¥{{ (row.price * row.stock).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="showStockDialog(row, 'add')"
            >
              <el-icon><Plus /></el-icon>
              入库
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="showStockDialog(row, 'subtract')"
              :disabled="row.stock <= 0"
            >
              <el-icon><Minus /></el-icon>
              出库
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deletePart(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" title="新增配件" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="配件编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入配件编码" />
        </el-form-item>
        <el-form-item label="配件名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入配件名称" />
        </el-form-item>
        <el-form-item label="规格型号" prop="specification">
          <el-input v-model="form.specification" placeholder="如：5W-30、195/65 R15" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择或输入分类" allow-create style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat"
              :label="cat"
              :value="cat"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="单价" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="库存" prop="stock">
              <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位" prop="unit">
              <el-input v-model="form.unit" placeholder="个/套/瓶" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="预警值" prop="min_stock">
          <el-input-number v-model="form.min_stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确认添加
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showStockDialogVisible" :title="stockDialogTitle" width="400px">
      <el-form label-width="100px">
        <el-form-item label="配件名称">
          <el-input :value="currentPart?.name" disabled />
        </el-form-item>
        <el-form-item label="当前库存">
          <el-input :value="currentPart?.stock + ' ' + currentPart?.unit" disabled />
        </el-form-item>
        <el-form-item :label="stockDialogTitle">
          <el-input-number
            v-model="stockQuantity"
            :min="1"
            :max="stockOperation === 'subtract' ? (currentPart?.stock || 1) : undefined"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStockDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmStockChange" :loading="submitting">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { partAPI } from '../api'

const parts = ref([])
const categories = ref([])
const inventoryStats = ref(null)
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const showStockDialogVisible = ref(false)
const formRef = ref(null)

const filters = reactive({
  category: '',
  low_stock: false,
  keyword: ''
})

const form = reactive({
  code: '',
  name: '',
  specification: '',
  category: '',
  price: 0,
  stock: 0,
  min_stock: 10,
  unit: '个',
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入配件编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入配件名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

const currentPart = ref(null)
const stockOperation = ref('add')
const stockQuantity = ref(1)

const stockDialogTitle = computed(() => {
  return stockOperation.value === 'add' ? '配件入库' : '配件出库'
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.category) params.category = filters.category
    if (filters.low_stock) params.low_stock = true
    if (filters.keyword) params.keyword = filters.keyword
    
    const [list, cats, stats] = await Promise.all([
      partAPI.getList(params),
      partAPI.getCategories(),
      partAPI.getInventoryStats()
    ])
    parts.value = list
    categories.value = cats
    inventoryStats.value = stats
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.category = ''
  filters.low_stock = false
  filters.keyword = ''
  loadData()
}

const showStockDialog = (row, operation) => {
  currentPart.value = row
  stockOperation.value = operation
  stockQuantity.value = 1
  showStockDialogVisible.value = true
}

const confirmStockChange = async () => {
  if (!stockQuantity.value || stockQuantity.value <= 0) {
    ElMessage.warning('请输入有效数量')
    return
  }
  
  submitting.value = true
  try {
    await partAPI.updateStock(currentPart.value.id, stockQuantity.value, stockOperation.value)
    ElMessage.success(stockOperation.value === 'add' ? '入库成功' : '出库成功')
    showStockDialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await partAPI.create(form)
        ElMessage.success('添加成功')
        showAddDialog.value = false
        formRef.value.resetFields()
        Object.assign(form, {
          code: '',
          name: '',
          specification: '',
          category: '',
          price: 0,
          stock: 0,
          min_stock: 10,
          unit: '个',
          description: ''
        })
        loadData()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '添加失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const deletePart = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该配件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await partAPI.delete(row.id)
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

.icon-value {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.icon-warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.icon-danger {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
}

.icon-ok {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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

.filter-card,
.table-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}
</style>
