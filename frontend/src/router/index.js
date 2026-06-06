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
    path: '/parts',
    name: 'Parts',
    component: () => import('../views/Parts.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
