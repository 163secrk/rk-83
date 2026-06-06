<template>
  <div class="work-order-detail">
    <div class="page-header">
      <el-button @click="$router.push('/work-orders')">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
      <h2 class="page-title">工单详情 #{{ workOrder?.id }}</h2>
      <div class="header-actions">
        <el-button
          v-if="workOrder?.status === 'assigned'"
          type="primary"
          @click="startWork"
        >
          <el-icon><VideoPlay /></el-icon>
          开始维修
        </el-button>
        <el-button
          v-if="workOrder?.status === 'in_progress'"
          type="success"
          @click="completeWork"
        >
          <el-icon><CircleCheck /></el-icon>
          完成维修
        </el-button>
        <el-button type="primary" @click="showInvoiceDialog = true">
          <el-icon><Tickets /></el-icon>
          查看工单
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-title">
              <el-icon><User /></el-icon>
              客户与车辆信息
            </div>
          </template>
          <div class="info-grid" v-if="workOrder">
            <div class="info-item">
              <span class="label">车主姓名：</span>
              <span class="value">{{ workOrder.appointment.customer.name }}</span>
            </div>
            <div class="info-item">
              <span class="label">联系电话：</span>
              <span class="value">{{ workOrder.appointment.customer.phone }}</span>
            </div>
            <div class="info-item">
              <span class="label">车型：</span>
              <span class="value">{{ workOrder.appointment.customer.car_model }}</span>
            </div>
            <div class="info-item">
              <span class="label">车牌号：</span>
              <span class="value">{{ workOrder.appointment.customer.car_plate }}</span>
            </div>
            <div class="info-item">
              <span class="label">服务类型：</span>
              <span class="value">{{ workOrder.appointment.service_type }}</span>
            </div>
            <div class="info-item">
              <span class="label">技师：</span>
              <span class="value">{{ workOrder.technician.name }}</span>
            </div>
            <div class="info-item full-width">
              <span class="label">问题描述：</span>
              <span class="value">{{ workOrder.appointment.description || '无' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-title">
              <el-icon><Clock /></el-icon>
              工单状态
            </div>
          </template>
          <div class="status-timeline" v-if="workOrder">
            <el-steps :active="getStepIndex()" finish-status="success" simple>
              <el-step title="工单创建" :description="formatDate(workOrder.created_at)" />
              <el-step title="开始维修" :description="workOrder.actual_start ? formatDate(workOrder.actual_start) : '未开始'" />
              <el-step title="维修完成" :description="workOrder.actual_end ? formatDate(workOrder.actual_end) : '未完成'" />
            </el-steps>

            <div class="status-badge">
              <el-tag :type="getStatusType(workOrder.status)" size="large">
                {{ getStatusText(workOrder.status) }}
              </el-tag>
            </div>

            <el-form :model="costForm" label-width="100px" class="cost-form">
              <el-form-item label="工时费">
                <el-input-number
                  v-model="costForm.labor_cost"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                  :disabled="workOrder.status === 'completed'"
                />
              </el-form-item>
              <el-form-item label="配件费用">
                <el-input :value="'¥' + partsTotal.toFixed(2)" disabled />
              </el-form-item>
              <el-form-item label="总费用">
                <el-input :value="'¥' + totalAmount.toFixed(2)" disabled class="total-amount" />
              </el-form-item>
              <el-form-item label="维修备注">
                <el-input
                  v-model="costForm.notes"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入维修备注..."
                  :disabled="workOrder.status === 'completed'"
                />
              </el-form-item>
              <el-form-item v-if="workOrder.status !== 'completed'">
                <el-button type="primary" @click="saveCost">
                  保存费用
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="parts-card">
      <template #header>
        <div class="card-header">
          <div class="card-title">
            <el-icon><Goods /></el-icon>
            配件消耗
          </div>
          <el-button
            type="primary"
            @click="showAddPartDialog = true"
            :disabled="workOrder?.status === 'completed'"
          >
            <el-icon><Plus /></el-icon>
            添加配件
          </el-button>
        </div>
      </template>

      <el-table :data="workOrder?.parts || []" v-loading="loading" border empty-text="暂无配件消耗记录">
        <el-table-column prop="part.code" label="配件编码" width="120" />
        <el-table-column prop="part.name" label="配件名称" />
        <el-table-column prop="part.category" label="分类" width="120" />
        <el-table-column prop="quantity" label="数量" width="100">
          <template #default="{ row }">
            {{ row.quantity }} {{ row.part.unit }}
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="单价" width="120">
          <template #default="{ row }">
            ¥{{ row.unit_price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="subtotal" label="小计" width="120">
          <template #default="{ row }">
            ¥{{ row.subtotal.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" v-if="workOrder?.status !== 'completed'">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="removePart(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddPartDialog" title="添加配件" width="600px">
      <el-form :model="addPartForm" label-width="100px">
        <el-form-item label="选择配件" prop="part_id">
          <el-select
            v-model="addPartForm.part_id"
            placeholder="请选择配件"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="part in availableParts"
              :key="part.id"
              :label="`${part.name} (库存: ${part.stock}${part.unit}) - ¥${part.price}`"
              :value="part.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用数量" prop="quantity">
          <el-input-number
            v-model="addPartForm.quantity"
            :min="1"
            :max="selectedPart?.stock || 100"
            style="width: 100%"
          />
          <div v-if="selectedPart" class="stock-info">
            当前库存：{{ selectedPart.stock }} {{ selectedPart.unit }}，单价：¥{{ selectedPart.price }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPartDialog = false">取消</el-button>
        <el-button type="primary" @click="addPart" :loading="submitting">
          确认添加
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showInvoiceDialog" title="工单详情单" width="700px">
      <div class="invoice" v-if="invoice">
        <div class="invoice-header">
          <h3>汽车维修工单</h3>
          <p>工单号：#{{ invoice.work_order_id }}</p>
        </div>
        <div class="invoice-section">
          <h4>客户信息</h4>
          <div class="invoice-grid">
            <div>客户姓名：{{ invoice.customer_name }}</div>
            <div>联系电话：{{ invoice.customer_phone }}</div>
            <div>车型：{{ invoice.car_model }}</div>
            <div>车牌号：{{ invoice.car_plate }}</div>
          </div>
        </div>
        <div class="invoice-section">
          <h4>服务信息</h4>
          <div class="invoice-grid">
            <div>服务类型：{{ invoice.service_type }}</div>
            <div>技师：{{ invoice.technician_name }}</div>
            <div>工单状态：{{ getStatusText(invoice.status) }}</div>
            <div>开单时间：{{ formatDate(invoice.created_at) }}</div>
            <div v-if="invoice.actual_start">开始时间：{{ formatDate(invoice.actual_start) }}</div>
            <div v-if="invoice.actual_end">完成时间：{{ formatDate(invoice.actual_end) }}</div>
          </div>
        </div>
        <div class="invoice-section">
          <h4>费用明细</h4>
          <el-table :data="invoice.parts" border size="small">
            <el-table-column prop="name" label="配件名称" />
            <el-table-column prop="code" label="编码" width="100" />
            <el-table-column label="数量" width="80">
              <template #default="{ row }">
                {{ row.quantity }}{{ row.unit }}
              </template>
            </el-table-column>
            <el-table-column label="单价" width="100">
              <template #default="{ row }">
                ¥{{ row.unit_price.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="小计" width="100">
              <template #default="{ row }">
                ¥{{ row.subtotal.toFixed(2) }}
              </template>
            </el-table-column>
          </el-table>
          <div class="invoice-total">
            <div>工时费：<strong>¥{{ invoice.labor_cost.toFixed(2) }}</strong></div>
            <div>配件合计：<strong>¥{{ invoice.parts_total.toFixed(2) }}</strong></div>
            <div class="grand-total">总计：<strong>¥{{ invoice.total_amount.toFixed(2) }}</strong></div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showInvoiceDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workOrderAPI, partAPI } from '../api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const workOrderId = computed(() => route.params.id)

const workOrder = ref(null)
const loading = ref(false)
const submitting = ref(false)
const availableParts = ref([])
const invoice = ref(null)
const showAddPartDialog = ref(false)
const showInvoiceDialog = ref(false)

const costForm = reactive({
  labor_cost: 0,
  notes: ''
})

const addPartForm = reactive({
  part_id: null,
  quantity: 1
})

const selectedPart = computed(() => {
  if (!addPartForm.part_id) return null
  return availableParts.value.find(p => p.id === addPartForm.part_id)
})

const partsTotal = computed(() => {
  if (!workOrder.value) return 0
  return workOrder.value.parts.reduce((sum, p) => sum + p.subtotal, 0)
})

const totalAmount = computed(() => {
  return costForm.labor_cost + partsTotal.value
})

const loadWorkOrder = async () => {
  loading.value = true
  try {
    workOrder.value = await workOrderAPI.getById(workOrderId.value)
    costForm.labor_cost = workOrder.value.labor_cost
    costForm.notes = workOrder.value.notes || ''
  } catch (error) {
    ElMessage.error('加载工单详情失败')
    router.push('/work-orders')
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

const loadInvoice = async () => {
  try {
    invoice.value = await workOrderAPI.getInvoice(workOrderId.value)
  } catch (error) {
    ElMessage.error('加载工单详情失败')
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const getStepIndex = () => {
  if (!workOrder.value) return 0
  const status = workOrder.value.status
  if (status === 'assigned') return 0
  if (status === 'in_progress') return 1
  if (status === 'completed') return 2
  return 0
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

const startWork = async () => {
  try {
    await ElMessageBox.confirm('确认开始维修吗？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'primary'
    })
    await workOrderAPI.updateStatus(workOrderId.value, 'in_progress')
    ElMessage.success('已开始维修')
    loadWorkOrder()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const completeWork = async () => {
  try {
    await ElMessageBox.confirm('确认完成维修吗？完成后将无法修改。', '提示', {
      confirmButtonText: '确认完成',
      cancelButtonText: '取消',
      type: 'success'
    })
    await workOrderAPI.updateStatus(workOrderId.value, 'completed')
    ElMessage.success('工单已完成')
    loadWorkOrder()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const saveCost = async () => {
  submitting.value = true
  try {
    await workOrderAPI.update(workOrderId.value, costForm)
    ElMessage.success('费用信息已保存')
    loadWorkOrder()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

const addPart = async () => {
  if (!addPartForm.part_id) {
    ElMessage.warning('请选择配件')
    return
  }
  if (!addPartForm.quantity || addPartForm.quantity <= 0) {
    ElMessage.warning('请输入有效数量')
    return
  }
  
  submitting.value = true
  try {
    await workOrderAPI.addPart(workOrderId.value, addPartForm)
    ElMessage.success('配件添加成功')
    showAddPartDialog.value = false
    addPartForm.part_id = null
    addPartForm.quantity = 1
    loadWorkOrder()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    submitting.value = false
  }
}

const removePart = async (row) => {
  try {
    await ElMessageBox.confirm('确定要移除该配件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await workOrderAPI.removePart(workOrderId.value, row.part_id)
    ElMessage.success('配件已移除')
    loadWorkOrder()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '移除失败')
    }
  }
}

watch(showInvoiceDialog, (val) => {
  if (val) {
    loadInvoice()
  }
})

watch(showAddPartDialog, (val) => {
  if (val) {
    loadParts()
  }
})

onMounted(() => {
  loadWorkOrder()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  flex: 1;
  font-size: 24px;
  color: #303133;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.info-card,
.parts-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.info-item {
  flex: 1 1 calc(50% - 8px);
  min-width: 200px;
}

.info-item.full-width {
  flex: 1 1 100%;
}

.label {
  color: #909399;
  margin-right: 8px;
}

.value {
  color: #303133;
  font-weight: 500;
}

.status-timeline {
  padding: 10px 0;
}

.status-badge {
  text-align: center;
  margin: 20px 0;
}

.cost-form {
  margin-top: 20px;
}

.total-amount :deep(.el-input__wrapper) {
  background: #f0f9eb;
}

.total-amount :deep(.el-input__inner) {
  color: #67c23a;
  font-weight: bold;
  font-size: 18px;
}

.stock-info {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.invoice {
  padding: 20px;
}

.invoice-header {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #409eff;
}

.invoice-header h3 {
  margin: 0 0 10px 0;
  color: #409eff;
}

.invoice-section {
  margin-bottom: 20px;
}

.invoice-section h4 {
  color: #303133;
  margin: 0 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #ebeef5;
}

.invoice-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  color: #606266;
}

.invoice-total {
  margin-top: 16px;
  text-align: right;
}

.invoice-total > div {
  margin: 8px 0;
  font-size: 14px;
}

.invoice-total .grand-total {
  font-size: 18px;
  color: #f56c6c;
  border-top: 2px solid #ebeef5;
  padding-top: 10px;
  margin-top: 10px;
}
</style>
