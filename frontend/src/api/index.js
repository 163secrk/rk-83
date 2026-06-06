import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

request.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const appointmentAPI = {
  getList: (params) => request.get('/appointments', { params }),
  getById: (id) => request.get(`/appointments/${id}`),
  create: (data) => request.post('/appointments', data),
  update: (id, data) => request.put(`/appointments/${id}`, data),
  delete: (id) => request.delete(`/appointments/${id}`),
  getTodayStats: () => request.get('/appointments/statistics/today')
}

export const technicianAPI = {
  getList: (params) => request.get('/technicians', { params }),
  getById: (id) => request.get(`/technicians/${id}`),
  create: (data) => request.post('/technicians', data),
  update: (id, data) => request.put(`/technicians/${id}`, data),
  updateStatus: (id, status) => request.put(`/technicians/${id}/status?status=${status}`),
  delete: (id) => request.delete(`/technicians/${id}`),
  getWorkOrders: (id, status) => request.get(`/technicians/${id}/work-orders`, { params: { status } }),
  getStatistics: () => request.get('/technicians/statistics/summary')
}

export const partAPI = {
  getList: (params) => request.get('/parts', { params }),
  getById: (id) => request.get(`/parts/${id}`),
  create: (data) => request.post('/parts', data),
  update: (id, data) => request.put(`/parts/${id}`, data),
  updateStock: (id, quantity, operation) => 
    request.patch(`/parts/${id}/stock?quantity=${quantity}&operation=${operation}`),
  delete: (id) => request.delete(`/parts/${id}`),
  getCategories: () => request.get('/parts/categories/list'),
  getInventoryStats: () => request.get('/parts/statistics/inventory'),
  getUsageHistory: (id, params) => request.get(`/parts/${id}/usage-history`, { params })
}

export const workOrderAPI = {
  getList: (params) => request.get('/work-orders', { params }),
  getById: (id) => request.get(`/work-orders/${id}`),
  create: (data) => request.post('/work-orders', data),
  update: (id, data) => request.put(`/work-orders/${id}`, data),
  updateStatus: (id, status) => request.put(`/work-orders/${id}/status?status=${status}`),
  addPart: (id, data) => request.post(`/work-orders/${id}/parts`, data),
  removePart: (orderId, partId) => request.delete(`/work-orders/${orderId}/parts/${partId}`),
  delete: (id) => request.delete(`/work-orders/${id}`),
  getDashboardStats: () => request.get('/work-orders/statistics/dashboard'),
  getInvoice: (id) => request.get(`/work-orders/${id}/invoice`)
}
