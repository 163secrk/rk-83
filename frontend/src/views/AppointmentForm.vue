<template>
  <div class="appointment-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="24" color="#409EFF"><CalendarPlus /></el-icon>
          <span>在线预约保养</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="form-content"
      >
        <el-divider content-position="left">车辆信息</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="车主姓名" prop="customer.name">
              <el-input v-model="form.customer.name" placeholder="请输入车主姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="customer.phone">
              <el-input v-model="form.customer.phone" placeholder="请输入联系电话" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="车型" prop="customer.car_model">
              <el-input v-model="form.customer.car_model" placeholder="例如：宝马5系、奔驰E级" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="车牌号" prop="customer.car_plate">
              <el-input v-model="form.customer.car_plate" placeholder="例如：京A12345" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">服务信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="服务类型" prop="service_type">
              <el-select v-model="form.service_type" placeholder="请选择服务类型" style="width: 100%">
                <el-option label="常规保养" value="常规保养" />
                <el-option label="大保养" value="大保养" />
                <el-option label="维修服务" value="维修服务" />
                <el-option label="钣金喷漆" value="钣金喷漆" />
                <el-option label="轮胎更换" value="轮胎更换" />
                <el-option label="空调维修" value="空调维修" />
                <el-option label="其他服务" value="其他服务" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预约时间" prop="appointment_date">
              <el-date-picker
                v-model="form.appointment_date"
                type="datetime"
                placeholder="选择预约时间"
                :disabled-date="disabledDate"
                :shortcuts="shortcuts"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="问题描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请描述您的车辆问题或保养需求..."
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="submitForm" :loading="submitting">
            <el-icon><Check /></el-icon>
            提交预约
          </el-button>
          <el-button size="large" @click="resetForm">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="tips-card" v-if="successAppointment">
      <template #header>
        <div class="success-header">
          <el-icon :size="24" color="#67C23A"><CircleCheck /></el-icon>
          <span>预约成功！</span>
        </div>
      </template>
      <div class="success-content">
        <p>您的预约已提交成功，我们会尽快安排技师为您服务。</p>
        <p><strong>预约单号：</strong>{{ successAppointment.id }}</p>
        <p><strong>车主姓名：</strong>{{ successAppointment.customer.name }}</p>
        <p><strong>车辆牌照：</strong>{{ successAppointment.customer.car_plate }}</p>
        <p><strong>服务类型：</strong>{{ successAppointment.service_type }}</p>
        <p><strong>预约时间：</strong>{{ formatDate(successAppointment.appointment_date) }}</p>
        <el-button type="primary" @click="newAppointment" style="margin-top: 16px">
          继续预约
        </el-button>
      </div>
    </el-card>

    <el-card class="tips-card">
      <template #header>
        <div class="tips-header">
          <el-icon :size="20" color="#E6A23C"><Warning /></el-icon>
          <span>温馨提示</span>
        </div>
      </template>
      <ul class="tips-list">
        <li>请提前15分钟到达4S店，以便我们做好接待准备</li>
        <li>请携带行驶证、驾驶证和保养手册</li>
        <li>如需取消或改期，请提前24小时联系我们</li>
        <li>工作时间：周一至周日 8:00 - 18:00</li>
        <li>服务热线：400-888-8888</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { appointmentAPI } from '../api'
import dayjs from 'dayjs'

const formRef = ref(null)
const submitting = ref(false)
const successAppointment = ref(null)

const form = reactive({
  customer_id: 0,
  service_type: '',
  description: '',
  appointment_date: null,
  customer: {
    name: '',
    phone: '',
    car_model: '',
    car_plate: ''
  }
})

const rules = {
  'customer.name': [
    { required: true, message: '请输入车主姓名', trigger: 'blur' }
  ],
  'customer.phone': [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  'customer.car_model': [
    { required: true, message: '请输入车型', trigger: 'blur' }
  ],
  'customer.car_plate': [
    { required: true, message: '请输入车牌号', trigger: 'blur' }
  ],
  service_type: [
    { required: true, message: '请选择服务类型', trigger: 'change' }
  ],
  appointment_date: [
    { required: true, message: '请选择预约时间', trigger: 'change' }
  ]
}

const shortcuts = [
  {
    text: '今天',
    value: () => new Date()
  },
  {
    text: '明天',
    value: () => {
      const date = new Date()
      date.setDate(date.getDate() + 1)
      return date
    }
  },
  {
    text: '后天',
    value: () => {
      const date = new Date()
      date.setDate(date.getDate() + 2)
      return date
    }
  }
]

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // #region debug-point H1:appointment-time-before-submit
        fetch("http://127.0.0.1:7777/event",{method:"POST",body:JSON.stringify({sessionId:"maintenance-system-bugs",runId:"pre-fix",hypothesisId:"H1",location:"AppointmentForm.vue:212",msg:"[DEBUG] 预约提交前时间值",data:{appointment_date_form:form.appointment_date,appointment_date_iso:form.appointment_date?.toISOString(),appointment_date_local:form.appointment_date?.toString(),timezone_offset:new Date().getTimezoneOffset()},ts:Date.now()})}).catch(()=>{});
        // #endregion
        const result = await appointmentAPI.create(form)
        // #region debug-point H1:appointment-time-after-response
        fetch("http://127.0.0.1:7777/event",{method:"POST",body:JSON.stringify({sessionId:"maintenance-system-bugs",runId:"pre-fix",hypothesisId:"H1",location:"AppointmentForm.vue:221",msg:"[DEBUG] 预约返回后时间值",data:{returned_appointment_date:result.appointment_date,returned_date_formatted:formatDate(result.appointment_date)},ts:Date.now()})}).catch(()=>{});
        // #endregion
        successAppointment.value = result
        ElMessage.success('预约提交成功！')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '提交失败，请重试')
      } finally {
        submitting.value = false
      }
    }
  })
}

const resetForm = () => {
  formRef.value?.resetFields()
  form.customer = {
    name: '',
    phone: '',
    car_model: '',
    car_plate: ''
  }
  successAppointment.value = null
}

const newAppointment = () => {
  resetForm()
}
</script>

<style scoped>
.appointment-form {
  max-width: 900px;
  margin: 0 auto;
}

.form-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.form-content {
  padding: 20px 0;
}

.tips-card {
  border-radius: 8px;
  border: none;
  background: #fffbe6;
}

.tips-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.success-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #67C23A;
}

.success-content {
  padding: 10px 0;
}

.success-content p {
  margin: 8px 0;
  color: #606266;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.tips-list li {
  margin: 8px 0;
  line-height: 1.6;
}

:deep(.el-divider__text) {
  background: #fff;
  font-weight: 600;
  color: #303133;
}
</style>
