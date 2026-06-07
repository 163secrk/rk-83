import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/appointment',
    name: 'AppointmentForm',
    component: () => import('../views/AppointmentForm.vue')
  },
  {
    path: '/appointments',
    name: 'Appointments',
    component: () => import('../views/Appointments.vue')
  },
  {
    path: '/work-orders',
    name: 'WorkOrders',
    component: () => import('../views/WorkOrders.vue')
  },
  {
    path: '/work-orders/:id',
    name: 'WorkOrderDetail',
    component: () => import('../views/WorkOrderDetail.vue')
  },
  {
    path: '/technicians',
    name: 'Technicians',
    component: () => import('../views/Technicians.vue')
  },
  {
    path: '/technicians/:id',
    name: 'TechnicianDetail',
    component: () => import('../views/TechnicianDetail.vue')
  },
  {
    path: '/parts',
    name: 'Parts',
    component: () => import('../views/Parts.vue')
  },
  {
    path: '/customers',
    name: 'Customers',
    component: () => import('../views/Customers.vue')
  },
  {
    path: '/customers/:id',
    name: 'CustomerDetail',
    component: () => import('../views/CustomerDetail.vue')
  },
  {
    path: '/vehicles',
    name: 'Vehicles',
    component: () => import('../views/Vehicles.vue')
  },
  {
    path: '/vehicles/:id/maintenance',
    name: 'VehicleMaintenance',
    component: () => import('../views/VehicleMaintenance.vue')
  },
  {
    path: '/packages',
    name: 'MaintenancePackages',
    component: () => import('../views/MaintenancePackages.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
