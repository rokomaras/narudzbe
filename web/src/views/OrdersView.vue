<script setup>
// Isti view služi za /orders (kupac: "Moje narudžbe") i /admin/orders (admin: sve).
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import StateBlock from '../components/StateBlock.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useOrdersStore } from '../stores/orders'
import { formatDate, formatEuro, STATUS_LABELS } from '../utils/format'

const route = useRoute()
const store = useOrdersStore()
const isAdminView = computed(() => route.meta.role === 'admin')

const statusFilter = ref('')
const actionError = ref('')

function load() {
  return store.fetchOrders(statusFilter.value)
}
load()
watch(statusFilter, load)

async function run(kind, order) {
  actionError.value = ''
  try {
    await store.act(kind, order.id)
  } catch (e) {
    actionError.value = `Narudžba #${order.id}: ${e.message}`
  }
}
</script>

<template>
  <h1>{{ isAdminView ? 'Sve narudžbe' : 'Moje narudžbe' }}</h1>

  <div class="filters">
    <button class="btn" :class="{ active: statusFilter === '' }" @click="statusFilter = ''">Sve</button>
    <button
      v-for="(label, value) in STATUS_LABELS" :key="value"
      class="btn" :class="{ active: statusFilter === value }" @click="statusFilter = value"
    >
      {{ label }}
    </button>
  </div>

  <p v-if="actionError" class="alert alert-error">{{ actionError }}</p>

  <StateBlock
    :loading="store.loading"
    :error="store.error"
    :empty="store.orders.length === 0"
    :empty-text="statusFilter ? 'Nema narudžbi s tim statusom.' : 'Još nema narudžbi.'"
    @retry="load"
  >
    <table class="table">
      <thead>
        <tr>
          <th>#</th><th>Datum</th><th v-if="isAdminView">Kupac</th><th>Status</th>
          <th class="num">Iznos</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="o in store.orders" :key="o.id">
          <td>{{ o.id }}</td>
          <td>{{ formatDate(o.created_at) }}</td>
          <td v-if="isAdminView">{{ o.customer_username }}</td>
          <td><StatusBadge :status="o.status" /></td>
          <td class="num">{{ formatEuro(o.total_cents) }}</td>
          <td class="num">
            <div class="actions">
              <button v-if="isAdminView && o.status === 'paid'" class="btn btn-small" @click="run('ship', o)">Pošalji</button>
              <button v-if="isAdminView && o.status === 'shipped'" class="btn btn-small" @click="run('deliver', o)">Dostavljeno</button>
              <RouterLink class="btn btn-small" :to="`/orders/${o.id}`">Detalji</RouterLink>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </StateBlock>
</template>
