<template>
  <div class="customer-detail">
    <div class="page-header">
      <div>
        <h2 class="page-title">客户详情</h2>
        <div class="breadcrumb" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回客户列表</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <el-card v-if="customerData" class="customer-info-card">
      <div class="customer-header">
        <div class="customer-avatar">
          <el-icon :size="40" color="#fff"><UserFilled /></el-icon>
        </div>
        <div class="customer-basic">
          <h3 class="customer-name">{{ customerData.name }}</h3>
          <div class="customer-info-row">
            <el-tag type="primary" size="large">{{ customerData.phone }}</el-tag>
            <span class="register-time">注册时间: {{ formatDate(customerData.created_at) }}</span>
          </div>
        </div>
        <div class="customer-stats">
          <div class="stat-item">
            <div class="stat-value">{{ customerData.vehicles?.length || 0 }}</div>
            <div class="stat-label">名下车辆</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">{{ customerData.total_maintenance_count || 0 }}</div>
            <div class="stat-label">维保总次数</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value highlight">¥{{ formatMoney(customerData.total_cost || 0) }}</div>
            <div class="stat-label">累计消费</div>
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

    <el-card v-if="customerData?.vehicles?.length > 0" class="vehicles-section">
      <div class="section-header">
        <h4 class="section-title">
          <el-icon><Van /></el-icon>
          名下车辆
        </h4>
      </div>

      <el-tabs v-model="activeVehicleId" type="card" class="vehicle-tabs">
        <el-tab-pane 
          v-for="vehicle in customerData.vehicles" 
          :key="vehicle.vehicle_id" 
          :label="vehicle.car_model + ' (' + vehicle.car_plate + ')'"
          :name="String(vehicle.vehicle_id)"
        >
          <div class="vehicle-stats-row">
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="mini-stat">
                  <div class="mini-stat-value">{{ vehicle.total_maintenance_count }}</div>
                  <div class="mini-stat-label">维保次数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="mini-stat">
                  <div class="mini-stat-value highlight">¥{{ formatMoney(vehicle.total_cost) }}</div>
                  <div class="mini-stat-label">累计费用</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="mini-stat">
                  <div class="mini-stat-value">{{ vehicle.first_maintenance_date ? formatDate(vehicle.first_maintenance_date, 'date') : '-' }}</div>
                  <div class="mini-stat-label">首次维保</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="mini-stat">
                  <div class="mini-stat-value">{{ vehicle.last_maintenance_date ? formatDate(vehicle.last_maintenance_date, 'date') : '-' }}</div>
                  <div class="mini-stat-label">最近维保</div>
                </div>
              </el-col>
            </el-row>
          </div>

          <div class="vehicle-actions">
            <el-button type="primary" @click="viewVehicleMaintenance(vehicle.vehicle_id)">
              <el-icon><Document /></el-icon>
              查看完整维保档案
            </el-button>
          </div>

          <div v-if="!vehicle.records || vehicle.records?.length === 0" class="empty-records">
            <el-empty description="暂无维保记录" />
          </div>

          <div v-else-if="vehicle.records?.length > 0" class="timeline-wrapper">
            <el-timeline>
              <el-timeline-item
                v-for="record in vehicle.records"
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

                  <div v-if="record.parts?.length > 0" class="record-parts">
                    <el-table :data="record.parts" size="small" border>
                      <el-table-column prop="part_name" label="配件名称" />
                      <el-table-column prop="part_code" label="编码" width="100" />
                      <el-table-column prop="quantity" label="数量" width="60" align="center" />
                      <el-table-column label="小计" width="90" align="right">
                        <template #default="{ row }">
                          ¥{{ formatMoney(row.subtotal) }}
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card v-else-if="customerData" class="no-vehicles-card">
      <el-empty description="该客户暂无车辆信息">
        <el-button type="primary" @click="addVehicle">添加车辆</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { customerAPI, vehicleAPI } from '../api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const customerId = route.params.id
const customerData = ref(null)
const serviceTypes = ref([])
const loading = ref(false)
const activeVehicleId = ref('')

const dateRange = ref([])
const serviceTypeFilter = ref('')

const loadServiceTypes = async () => {
  try {
    const types = await customerAPI.getServiceTypes(customerId)
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
    
    const data = await customerAPI.getDetail(customerId, params)
    customerData.value = data
    
    if (data.vehicles?.length > 0 && !activeVehicleId.value) {
      activeVehicleId.value = String(data.vehicles[0].vehicle_id)
    }
  } catch (error) {
    ElMessage.error('加载客户详情失败')
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

const viewVehicleMaintenance = (vehicleId) => {
  router.push(`/vehicles/${vehicleId}/maintenance`)
}

const addVehicle = () => {
  router.push({ path: '/vehicles', query: { customer_id: customerId, action: 'add' } })
}

const goBack = () => {
  router.push('/customers')
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

.customer-info-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.customer-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.customer-avatar {
  width: 70px;
  height: 70px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.customer-basic {
  flex: 1;
}

.customer-name {
  font-size: 22px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 12px 0;
}

.customer-info-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.register-time {
  font-size: 13px;
  color: #909399;
}

.customer-stats {
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

.vehicles-section {
  border-radius: 8px;
  border: none;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.section-title .el-icon {
  color: #409EFF;
}

.vehicle-tabs {
  margin-top: 20px;
}

.vehicle-stats-row {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.mini-stat {
  text-align: center;
  padding: 12px;
  background: white;
  border-radius: 8px;
}

.mini-stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.mini-stat-value.highlight {
  color: #f56c6c;
}

.mini-stat-label {
  font-size: 12px;
  color: #909399;
}

.vehicle-actions {
  margin-bottom: 20px;
}

.empty-records {
  padding: 40px 0;
}

.timeline-wrapper {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 10px;
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
  margin-bottom: 12px;
}

.record-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.record-icon {
  color: #409EFF;
  font-size: 18px;
}

.service-type {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.record-amount {
  display: flex;
  align-items: center;
  gap: 8px;
}

.amount-label {
  font-size: 13px;
  color: #909399;
}

.amount-value {
  font-size: 18px;
  font-weight: bold;
  color: #f56c6c;
}

.record-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 12px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 6px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 12px;
  color: #303133;
}

.record-description {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 6px;
  font-size: 12px;
}

.record-parts {
  margin: 12px 0;
}

.no-vehicles-card {
  border-radius: 8px;
  border: none;
}
</style>
