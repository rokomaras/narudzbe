import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { setSessionExpiredHandler } from './api/client'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './styles/global.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// Kad refresh token ne prođe (sesija istekla): odjavi i vrati na login.
setSessionExpiredHandler(() => {
  useAuthStore().logout()
  router.push({
    name: 'login',
    query: { redirect: router.currentRoute.value.fullPath, expired: '1' },
  })
})

app.mount('#app')
