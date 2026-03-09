import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'diaries',
        name: 'diaries',
        component: () => import('@/views/DiaryListView.vue'),
        meta: { title: '日记列表' },
      },
      {
        path: 'diaries/:id',
        name: 'diary-detail',
        component: () => import('@/views/DiaryDetailView.vue'),
        meta: { title: '日记详情' },
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('@/views/ProjectsView.vue'),
        meta: { title: '项目管理' },
      },
      {
        path: 'stats',
        name: 'stats',
        component: () => import('@/views/StatsView.vue'),
        meta: { title: '统计概览' },
      },
      {
        path: 'report',
        name: 'report',
        component: () => import('@/views/AnnualReportView.vue'),
        meta: { title: '年度报告' },
      },
      {
        path: 'watcher',
        name: 'watcher',
        component: () => import('@/views/WatcherView.vue'),
        meta: { title: 'Git 监听' },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'DevDiary'} - DevDiary`
  next()
})

export default router
