// =============================================================
// cart.js — Pinia store košarice (stanje koje dijele katalog, nav i košarica)
// =============================================================
// Košarica živi u pregledniku (localStorage) sve dok korisnik ne pošalje narudžbu.
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

const KEY = 'cart'

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

export const useCartStore = defineStore('cart', () => {
  // [{ productId, name, priceCents, stock, quantity }]
  const items = ref(load())

  watch(items, (value) => localStorage.setItem(KEY, JSON.stringify(value)), { deep: true })

  const count = computed(() => items.value.reduce((sum, i) => sum + i.quantity, 0))
  const totalCents = computed(() =>
    items.value.reduce((sum, i) => sum + i.quantity * i.priceCents, 0),
  )

  function add(product) {
    const existing = items.value.find((i) => i.productId === product.id)
    if (existing) {
      existing.stock = product.stock
      if (existing.quantity < product.stock) existing.quantity += 1
    } else if (product.stock > 0) {
      items.value.push({
        productId: product.id,
        name: product.name,
        priceCents: product.price_cents,
        stock: product.stock,
        quantity: 1,
      })
    }
  }

  function setQuantity(productId, quantity) {
    const item = items.value.find((i) => i.productId === productId)
    if (!item) return
    const q = Math.floor(Number(quantity))
    item.quantity = Number.isFinite(q) ? Math.min(Math.max(q, 1), item.stock) : 1
  }

  function remove(productId) {
    items.value = items.value.filter((i) => i.productId !== productId)
  }

  function clear() {
    items.value = []
  }

  return { items, count, totalCents, add, setQuantity, remove, clear }
})
