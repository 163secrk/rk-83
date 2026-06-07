<template>
  <div class="vehicle-maintenance">
    <div class="page-header">
      <div>
        <h2 class="page-title">车辆维保档案</h2>
        <div class="breadcrumb" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回车辆列表</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <el-card v-if="timelineData" class="vehicle-info-card">
      <div class="vehicle-header">
        <div class="vehicle-icon">
          <el-icon :size="48" color="#409EFF"><Van /></el-icon>
        </div>
        <div class="vehicle-basic">
          <h3 class="car-model">{{ timelineData.car_model }}</h3>
          <div class="car-tags">
            <el-tag type="primary" size="large">{{ timelineData.car_plate }}</el-tag>
            <el-tag v-if="timelineData.vin" type="info" size="large">VIN: {{ timelineData.vin }}</el-tag>
          </div>
        </div>
        <div class="vehicle-stats">
          <div class="stat-item">
            <div class="stat-value">{{ timelineData.total_maintenance_count }}</div>
            <div class="stat-label">维保次数</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value highlight">¥{{ formatMoney(timelineData.total_cost) }}</div>
            <div class="stat-label">累计费用</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">{{ timelineData.first_maintenance_date ? formatDate(timelineData.first_maintenance_date, 'date') : '-' }}</div>
            <div class="stat-label">首次维保</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">{{ timelineData.last_maintenance_date ? formatDate(timelineData.last_maintenance_date, 'date') : '-' }}</div>
            <div class="stat-label">最近维保</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="filter-card">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="loadData"
          />
        </el-form-item>
        <el-form-item label="保养类型">
          <el-select v-model="serviceTypeFilter" placeholder="全部类型" clearable @change="loadData" style="width: 160px">
            <el-option v-for="st in serviceTypes" :key="st" :label="st" :value="st" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilters">重置筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="timeline-card" v-loading="loading">
      <div v-if="!timelineData || timelineData?.records?.length === 0" class="empty-state">
        <el-empty description="暂无维保记录">
          <el-button type="primary">新增预约</el-button>
        </el-empty>
      </div>
      
      <el-timeline v-else-if="timelineData?.records?.length > 0">
        <el-timeline-item
          v-for="(record, index) in timelineData.records"
          :key="record.id"
          :timestamp="formatDate(record.date)"
          :type="getRecordTypeColor(record.type)"
          :color="getRecordStatusColor(record.status)"
          placement="top"
        >
          <el-card class="record-card" :class="getRecordClass(record.status)">
            <div class="record-header">
              <div class="record-title">
                <el-icon class="record-icon"><Tickets /></el-icon>
                <span class="service-type">{{ record.service_type }}</span>
                <el-tag :type="getRecordTypeTag(record.type)" size="small">
                  {{ record.type === 'work_order' ? '工单' : '预约' }}
                </el-tag>
                <el-tag :type="getStatusTagType(record.status)" size="small">
                  {{ getStatusText(record.status) }}
                </el-tag>
              </div>
              <div class="record-amount" v-if="record.total_amount > 0">
                <span class="amount-label">费用:</span>
                <span class="amount-value">¥{{ formatMoney(record.total_amount) }}</span>
              </div>
            </div>

            <div class="record-info">
              <div class="info-row" v-if="record.technician_name">
                <span class="info-label">技师:</span>
                <span class="info-value">{{ record.technician_name }}</span>
              </div>
              <div class="info-row" v-if="record.mileage">
                <span class="info-label">里程:</span>
                <span class="info-value">{{ record.mileage.toLocaleString() }} km</span>
              </div>
              <div class="info-row" v-if="record.labor_cost > 0">
                <span class="info-label">工时费:</span>
                <span class="info-value">¥{{ formatMoney(record.labor_cost) }}</span>
              </div>
              <div class="info-row" v-if="record.parts_total > 0">
                <span class="info-label">配件费:</span>
                <span class="info-value">¥{{ formatMoney(record.parts_total) }}</span>
              </div>
            </div>

            <div v-if="record.description" class="record-description">
              <span class="info-label">描述:</span>
              <span class="info-value">{{ record.description }}</span>
            </div>

            <div v-if="record.notes" class="record-description">
              <span class="info-label">备注:</span>
              <span class="info-value">{{ record.notes }}</span>
            </div>

            <div v-if="record.parts?.length > 0" class="record-parts">
              <div class="parts-header">
                <el-icon><Goods /></el-icon>
                <span>配件消耗</span>
              </div>
              <el-table :data="record.parts" size="small" border>
                <el-table-column prop="part_name" label="配件名称" />
                <el-table-column prop="part_code" label="配件编码" width="120" />
                <el-table-column prop="quantity" label="数量" width="80" align="center" />
                <el-table-column label="单价" width="100" align="right">
                  <template #default="{ row }">
                    ¥{{ formatMoney(row.unit_price) }}
                  </template>
                </el-table-column>
                <el-table-column label="小计" width="100" align="right">
                  <template #default="{ row }">
                    ¥{{ formatMoney(row.subtotal) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="record-footer">
              <el-button 
                v-if="record.work_order_id" 
                type="primary" 
                size="small" 
                @click="viewWorkOrder(record.work_order_id)"
              >
                查看工单详情
              </el-button>
              <el-button 
                v-if="record.appointment_id && !record.work_order_id" 
                type="success" 
                size="small"
              >
                创建工单
              </el-button>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { vehicleAPI } from '../api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const vehicleId = route.params.id
const timelineData = ref(null)
const serviceTypes = ref([])
const loading = ref(false)

const dateRange = ref([])
const serviceTypeFilter = ref('')

const loadServiceTypes = async () => {
  try {
    const types = await vehicleAPI.getServiceTypes(vehicleId)
    serviceTypes.value = types
  } catch (error) {
    console.error('加载服务类型失败', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (serviceTypeFilter.value) {
      params.service_type = serviceTypeFilter.value
    }
    
    const data = await vehicleAPI.getMaintenanceTimeline(vehicleId, params)
    timelineData.value = data
  } catch (error) {
    ElMessage.error('加载维保档案失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  dateRange.value = []
  serviceTypeFilter.value = ''
  loadData()
}

const formatDate = (date, type = 'datetime') => {
  if (!date) return '-'
  if (type === 'date') {
    return dayjs(date).format('YYYY-MM-DD')
  }
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const formatMoney = (num) => {
  return num?.toFixed(2) || '0.00'
}

const getRecordTypeColor = (type) => {
  return type === 'work_order' ? 'primary' : 'warning'
}

const getRecordStatusColor = (status) => {
  const colors = {
    completed: '#67c23a',
    in_progress: '#409eff',
    assigned: '#e6a23c',
    confirmed: '#909399',
    pending: '#f56c6c'
  }
  return colors[status] || '#909399'
}

const getRecordClass = (status) => {
  return `record-${status}`
}

const getRecordTypeTag = (type) => {
  return type === 'work_order' ? 'primary' : 'warning'
}

const getStatusTagType = (status) => {
  const types = {
    completed: 'success',
    in_progress: 'primary',
    assigned: 'warning',
    confirmed: 'info',
    pending: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    completed: '已完成',
    in_progress: '进行中',
    assigned: '已派单',
    confirmed: '已确认',
    pending: '待处理'
  }
  return texts[status] || status
}

const viewWorkOrder = (id) => {
  router.push(`/work-orders/${id}`)
}

const goBack = () => {
  router.push('/vehicles')
}

onMounted(() => {
  loadServiceTypes()
  loadData()
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

.vehicle-info-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.vehicle-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.vehicle-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vehicle-icon .el-icon {
  color: white;
}

.vehicle-basic {
  flex: 1;
}

.car-model {
  font-size: 22px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 12px 0;
}

.car-tags {
  display: flex;
  gap: 12px;
}

.vehicle-stats {
  display: flex;
  align-items: center;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-value.highlight {
  color: #f56c6c;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: #e4e7ed;
}

.filter-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.timeline-card {
  border-radius: 8px;
  border: none;
}

.empty-state {
  padding: 60px 0;
}

.record-card {
  margin-bottom: 16px;
  border-radius: 8px;
  transition: all 0.3s;
}

.record-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.record-completed {
  border-left: 4px solid #67c23a;
}

.record-in_progress {
  border-left: 4px solid #409eff;
}

.record-pending {
  border-left: 4px solid #f56c6c;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.record-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.record-icon {
  color: #409EFF;
  font-size: 20px;
}

.service-type {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.record-amount {
  display: flex;
  align-items: center;
  gap: 8px;
}

.amount-label {
  font-size: 14px;
  color: #909399;
}

.amount-value {
  font-size: 20px;
  font-weight: bold;
  color: #f56c6c;
}

.record-info {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label {
  font-size: 13px;
  color: #909399;
}

.info-value {
  font-size: 13px;
  color: #303133;
}

.record-description {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 6px;
  font-size: 13px;
}

.record-parts {
  margin: 16px 0;
}

.parts-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.parts-header .el-icon {
  color: #67c23a;
}

.record-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
