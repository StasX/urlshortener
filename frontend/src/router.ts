import { createRouter, createWebHistory } from 'vue-router'
import { initializeAuth, user } from './auth'
import HomeView from './views/HomeView.vue'
import AuthView from './views/AuthView.vue'
import DashboardView from './views/DashboardView.vue'
import ErrorView from './views/ErrorView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView, meta: { title: 'Make every link count' } },
    { path: '/home', redirect: '/' },
    { path: '/login', component: AuthView, props: { mode: 'login' }, meta: { title: 'Sign in' } },
    { path: '/register', component: AuthView, props: { mode: 'register' }, meta: { title: 'Create an account' } },
    { path: '/dashboard', component: DashboardView, meta: { protected: true, title: 'Dashboard' } },
    { path: '/:pathMatch(.*)*', component: ErrorView, meta: { title: 'Page not found' } },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async to => {
  await initializeAuth()
  if (to.meta.protected && !user.value) return { path: '/login', query: { next: '/dashboard' } }
})
router.afterEach(to => { document.title = `${to.meta.title || 'Shorty'} · Shorty` })
