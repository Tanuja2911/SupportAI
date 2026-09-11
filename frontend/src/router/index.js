import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/LandingView.vue'),
    meta: { guest: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('../views/SetupBusinessView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/app',
    component: () => import('../views/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/KnowledgeBaseView.vue'),
      },
      {
        path: 'conversations',
        name: 'Conversations',
        component: () => import('../views/ConversationsView.vue'),
      },
      {
        path: 'conversations/:id',
        name: 'ConversationDetail',
        component: () => import('../views/ConversationDetailView.vue'),
      },
      {
        path: 'escalations',
        name: 'Escalations',
        component: () => import('../views/EscalationsView.vue'),
      },
      {
        path: 'knowledge-gaps',
        name: 'KnowledgeGaps',
        component: () => import('../views/KnowledgeGapsView.vue'),
      },
      {
        path: 'faq',
        name: 'FAQ',
        component: () => import('../views/FAQView.vue'),
      },
      {
        path: 'widget',
        name: 'Widget',
        component: () => import('../views/WidgetConfigView.vue'),
      },
      {
        path: 'ai-settings',
        name: 'AISettings',
        component: () => import('../views/AISettingsView.vue'),
      },
      {
        path: 'team',
        name: 'Team',
        component: () => import('../views/TeamView.vue'),
      },
      {
        path: 'sandbox',
        name: 'Sandbox',
        component: () => import('../views/SandboxView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const business = localStorage.getItem('currentBusiness')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token && business) {
    next('/app')
  } else if (to.meta.requiresAuth && !to.meta.guest && token && !business && to.name !== 'Setup') {
    next('/setup')
  } else {
    next()
  }
})

export default router
