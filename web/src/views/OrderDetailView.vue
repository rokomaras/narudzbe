<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ordersApi } from '../api/orders'
import StateBlock from '../components/StateBlock.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useLoader } from '../composables/useLoader'
import { useAuthStore } from '../stores/auth'
import { useOrdersStore } from '../stores/orders'
import { formatDate, formatEuro } from '../utils/format'

const props = defineProps({ id: { type: String, required: true } })

const auth = useAuthStore()
const store = useOrdersStore()

const { data: order, loading, error, load } = useLoader(() => ordersApi.get(props.id))
load()
watch(() => props.id, load)

// lokalne količine za uređivanje stavki: { [itemId]: količina }
const qty = reactive({})
watch(
  order,
  (o) => {
    if (o) for (const item of o.items) qty[item.id] = item.quantity
  },
  { immediate: true },
)

const busy = ref(false)
const actionError = ref('')

const isOwner = computed(() => order.value && order.value.user_id === auth.user.id)
const status = computed(() => order.value?.status)
const canPay = computed(() => isOwner.value && status.value === 'pending')
const canCancel = computed(
  () => (isOwner.value || auth.isAdmin) && ['pending', 'paid'].includes(status.value),
)
const canShip = computed(() => auth.isAdmin && status.value === 'paid')
const canDeliver = computed(() => auth.isAdmin && status.value === 'shipped')
const canEditItems = computed(() => isOwner.value && !auth.isAdmin && status.value === 'pending')
const backLink = computed(() => (auth.isAdmin ? '/admin/orders' : '/orders'))

// Zajednički omotač za sve akcije: busy stanje + prikaz greške s servera.
async function run(fn) {
  busy.value = true
  actionError.value = ''
  try {
    order.value = await fn()
    store.replace(order.value)
  } catch (e) {
    actionError.value = e.message
  } finally {
    busy.value = false
  }
}

const pay = () => run(() => ordersApi.pay(order.value.id))
const cancel = () => {
  if (confirm('Sigurno želiš otkazati narudžbu?')) return run(() => ordersApi.cancel(order.value.id))
}
const ship = () => run(() => ordersApi.ship(order.value.id))
const deliver = () => run(() => ordersApi.deliver(order.value.id))
const saveItem = (item) => run(() => ordersApi.updateItem(order.value.id, item.id, Number(qty[item.id])))
const removeItem = (item) =>
  run(async () => {
    await ordersApi.removeItem(order.value.id, item.id) // 204 bez tijela
    return ordersApi.get(order.value.id)
  })
</script>

<template>
  <RouterLink :to="backLink">← Natrag na narudžbe</RouterLink>

  <StateBlock :loading="loading" :error="error" :empty="!order" empty-text="Narudžba nije pronađena." @retry="load">
    <template v-if="order">
      <div class="row" style="margin-top: 1rem">
        <h1 style="margin: 0">Narudžba #{{ order.id }}</h1>
        <StatusBadge :status="order.status" />
      </div>

      <div class="card" style="margin-bottom: 1rem">
        <p><strong>Kupac:</strong> {{ order.customer_username }}</p>
        <p><strong>Adresa dostave:</strong> {{ order.shipping_address }}</p>
        <p><strong>Naručeno:</strong> {{ formatDate(order.created_at) }}</p>
        <p v-if="order.paid_at"><strong>Plaćeno:</strong> {{ formatDate(order.paid_at) }}</p>
      </div>

      <p v-if="actionError" class="alert alert-error">{{ actionError }}</p>

      <table class="table">
        <thead>
          <tr>
            <th>Proizvod</th><th class="num">Cijena</th><th>Količina</th><th class="num">Ukupno</th>
            <th v-if="canEditItems"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in order.items" :key="item.id">
            <td>{{ item.product_name }}</td>
            <td class="num">{{ formatEuro(item.unit_price_cents) }}</td>
            <td>
              <input v-if="canEditItems" v-model="qty[item.id]" class="qty" type="number" min="1" />
              <span v-else>{{ item.quantity }}</span>
            </td>
            <td class="num">{{ formatEuro(item.line_total_cents) }}</td>
            <td v-if="canEditItems" class="num">
              <div class="actions">
                <button class="btn btn-small" :disabled="busy" @click="saveItem(item)">Spremi</button>
                <button class="btn btn-small btn-danger" :disabled="busy" @click="removeItem(item)">Ukloni</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="row" style="margin-top: 1rem">
        <div class="actions">
          <button v-if="canPay" class="btn btn-primary" :disabled="busy" @click="pay">Plati</button>
          <button v-if="canShip" class="btn btn-primary" :disabled="busy" @click="ship">Označi kao poslano</button>
          <button v-if="canDeliver" class="btn btn-primary" :disabled="busy" @click="deliver">Označi kao dostavljeno</button>
          <button v-if="canCancel" class="btn btn-danger" :disabled="busy" @click="cancel">Otkaži narudžbu</button>
        </div>
        <span class="total">Ukupno: {{ formatEuro(order.total_cents) }}</span>
      </div>
    </template>
  </StateBlock>
</template>
