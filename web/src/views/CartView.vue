<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ordersApi } from '../api/orders'
import { useCartStore } from '../stores/cart'
import { formatEuro } from '../utils/format'
import { serverFieldErrors } from '../utils/validation'

const cart = useCartStore()
const router = useRouter()

const address = ref('')
const errors = ref({})
const serverError = ref('')
const submitting = ref(false)

// Nakon promjene vrati u polje stvarnu (ograničenu) količinu iz storea,
// npr. ako je korisnik upisao 999, a na zalihi ima 5.
function onQuantity(item, event) {
  cart.setQuantity(item.productId, event.target.value)
  event.target.value = item.quantity
}

async function checkout() {
  serverError.value = ''
  errors.value = {}
  if (address.value.trim().length < 5) {
    errors.value = { shipping_address: 'Unesi adresu dostave (najmanje 5 znakova)' }
    return
  }
  submitting.value = true
  try {
    const order = await ordersApi.create({
      shipping_address: address.value.trim(),
      items: cart.items.map((i) => ({ product_id: i.productId, quantity: i.quantity })),
    })
    cart.clear()
    router.push(`/orders/${order.id}`)
  } catch (e) {
    const fieldErrors = serverFieldErrors(e)
    if (fieldErrors.shipping_address) errors.value = fieldErrors
    // npr. "Nedovoljno zalihe za 'Majica' (dostupno: 2)"
    serverError.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <h1>Košarica</h1>

  <div v-if="cart.items.length === 0" class="state">
    Košarica je prazna. <RouterLink to="/products">Pogledaj katalog</RouterLink>
  </div>

  <template v-else>
    <table class="table">
      <thead>
        <tr><th>Proizvod</th><th class="num">Cijena</th><th>Količina</th><th class="num">Ukupno</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="i in cart.items" :key="i.productId">
          <td>{{ i.name }}</td>
          <td class="num">{{ formatEuro(i.priceCents) }}</td>
          <td>
            <input
              class="qty" type="number" min="1" :max="i.stock" :value="i.quantity"
              @change="onQuantity(i, $event)"
            />
            <small class="muted"> / {{ i.stock }}</small>
          </td>
          <td class="num">{{ formatEuro(i.quantity * i.priceCents) }}</td>
          <td class="num"><button class="btn btn-small btn-danger" @click="cart.remove(i.productId)">Ukloni</button></td>
        </tr>
      </tbody>
    </table>

    <div class="row" style="margin-top: 1rem">
      <span></span>
      <span class="total">Ukupno: {{ formatEuro(cart.totalCents) }}</span>
    </div>

    <form class="card form" novalidate @submit.prevent="checkout">
      <div class="field" :class="{ invalid: errors.shipping_address }">
        <label for="address">Adresa dostave</label>
        <textarea id="address" v-model="address" rows="2" placeholder="Ulica i broj, grad"></textarea>
        <span v-if="errors.shipping_address" class="field-error">{{ errors.shipping_address }}</span>
      </div>
      <p v-if="serverError" class="alert alert-error">{{ serverError }}</p>
      <button class="btn btn-primary" :disabled="submitting">
        {{ submitting ? 'Šaljem…' : 'Naruči' }}
      </button>
      <p class="hint muted">Narudžba se mora platiti u roku 24 sata, inače se automatski otkazuje.</p>
    </form>
  </template>
</template>
