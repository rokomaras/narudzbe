// =============================================================
// auth.js — Pinia store za prijavljenog korisnika
// =============================================================
// Zašto store, a ne lokalni ref? Prijavljeni korisnik treba SVIMA:
// navigaciji, route guardu, API klijentu, više viewova.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '../api/auth'
import { clearTokens, getTokens, setTokens } from '../api/tokens'
import { useCartStore } from './cart'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const initialized = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const homeRoute = computed(() => (isAdmin.value ? '/admin/orders' : '/products'))

  // Poziva se JEDNOM pri pokretanju: ako u localStorageu ima tokena,
  // provjeri s backendom tko smo (/auth/me). Ako je access istekao,
  // API klijent će sam napraviti refresh.
  async function init() {
    if (initialized.value) return
    const { access, refresh } = getTokens()
    if (access || refresh) {
      try {
        user.value = await authApi.me()
      } catch {
        clearTokens()
        user.value = null
      }
    }
    initialized.value = true
  }

  async function login(username, password) {
    const tokens = await authApi.login(username, password)
    setTokens(tokens.access_token, tokens.refresh_token)
    user.value = await authApi.me()
  }

  async function register(payload) {
    await authApi.register(payload)
    await login(payload.username, payload.password)
  }

  function logout() {
    clearTokens()
    user.value = null
    useCartStore().clear()
  }

  return { user, initialized, isAuthenticated, isAdmin, homeRoute, init, login, register, logout }
})
