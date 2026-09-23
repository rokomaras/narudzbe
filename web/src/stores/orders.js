// =============================================================
// orders.js — Pinia store narudžbi (poslovni entitet)
// =============================================================
// Drži listu narudžbi + stanja loading/error, i akcije workflowa.
// Kad se narudžba promijeni (plati, pošalje...), zamijenimo je u listi
// pa se svi viewovi koji je prikazuju osvježe sami.
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ordersApi } from '../api/orders'

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref([])
  const loading = ref(false)
  const error = ref('')

  async function fetchOrders(status = '') {
    loading.value = true
    error.value = ''
    try {
      orders.value = await ordersApi.list(status)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function replace(order) {
    const i = orders.value.findIndex((o) => o.id === order.id)
    if (i >= 0) orders.value[i] = order
  }

  // kind: 'pay' | 'cancel' | 'ship' | 'deliver'
  async function act(kind, orderId) {
    const updated = await ordersApi[kind](orderId)
    replace(updated)
    return updated
  }

  return { orders, loading, error, fetchOrders, replace, act }
})
