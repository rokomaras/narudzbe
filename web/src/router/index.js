// =============================================================
// router/index.js — rute i ROUTE GUARDOVI
// =============================================================
// meta.public  : dostupno bez prijave (login, registracija)
// meta.role    : 'admin' | 'customer' — samo ta rola smije unutra
// Guard radi na SVAKOJ navigaciji, pa i kad korisnik ručno upiše URL.
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', redirect: '/products' },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue'), meta: { public: true } },

  // --- kupac ---
  { path: '/products', name: 'products', component: () => import('../views/ProductsView.vue'), meta: { role: 'customer' } },
  { path: '/cart', name: 'cart', component: () => import('../views/CartView.vue'), meta: { role: 'customer' } },
  { path: '/orders', name: 'orders', component: () => import('../views/OrdersView.vue'), meta: { role: 'customer' } },

  // --- oba (vlasnik ili admin; backend dodatno provjerava ownership) ---
  { path: '/orders/:id(\\d+)', name: 'order-detail', component: () => import('../views/OrderDetailView.vue'), props: true, meta: {} },

  // --- admin ---
  { path: '/admin/orders', name: 'admin-orders', component: () => import('../views/OrdersView.vue'), meta: { role: 'admin' } },
  { path: '/admin/products', name: 'admin-products', component: () => import('../views/admin/AdminProductsView.vue'), meta: { role: 'admin' } },
  { path: '/admin/products/new', name: 'admin-product-new', component: () => import('../views/admin/AdminProductFormView.vue'), meta: { role: 'admin' } },
  {
    path: '/admin/products/:id(\\d+)/edit',
    name: 'admin-product-edit',
    component: () => import('../views/admin/AdminProductFormView.vue'),
    props: true,
    meta: { role: 'admin' },
  },

  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue'), meta: { public: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.initialized) await auth.init()

  // Javne stranice: prijavljenog korisnika s login/register šaljemo na njegov početak.
  if (to.meta.public) {
    if (auth.isAuthenticated && (to.name === 'login' || to.name === 'register')) {
      return auth.homeRoute
    }
    return true
  }

  // Nije prijavljen -> na login (zapamti kamo je htio)
  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // Prijavljen, ali kriva rola -> na svoj početak
  if (to.meta.role && to.meta.role !== auth.user.role) {
    return auth.homeRoute
  }

  return true
})

export default router
