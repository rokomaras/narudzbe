<script setup>
import { ref } from 'vue'
import { productsApi } from '../../api/products'
import StateBlock from '../../components/StateBlock.vue'
import { useLoader } from '../../composables/useLoader'
import { formatEuro } from '../../utils/format'

const { data: products, loading, error, load } = useLoader(() => productsApi.list())
load()

const actionError = ref('')

async function toggleActive(product) {
  actionError.value = ''
  try {
    const updated = await productsApi.update(product.id, { is_active: !product.is_active })
    Object.assign(product, updated)
  } catch (e) {
    actionError.value = e.message
  }
}

async function remove(product) {
  if (!confirm(`Obrisati proizvod "${product.name}"?`)) return
  actionError.value = ''
  try {
    await productsApi.remove(product.id)
    products.value = products.value.filter((p) => p.id !== product.id)
  } catch (e) {
    // npr. 409 "Proizvod je u narudžbama i ne može se obrisati. Deaktiviraj ga."
    actionError.value = e.message
  }
}
</script>

<template>
  <div class="row">
    <h1 style="margin: 0">Proizvodi</h1>
    <RouterLink class="btn btn-primary" to="/admin/products/new">+ Novi proizvod</RouterLink>
  </div>

  <p v-if="actionError" class="alert alert-error">{{ actionError }}</p>

  <StateBlock
    :loading="loading" :error="error"
    :empty="!products || products.length === 0"
    empty-text="Još nema proizvoda. Dodaj prvi."
    @retry="load"
  >
    <table class="table">
      <thead>
        <tr><th>Naziv</th><th class="num">Cijena</th><th class="num">Zaliha</th><th>Aktivan</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="p in products" :key="p.id">
          <td>{{ p.name }}</td>
          <td class="num">{{ formatEuro(p.price_cents) }}</td>
          <td class="num">{{ p.stock }}</td>
          <td>{{ p.is_active ? 'Da' : 'Ne' }}</td>
          <td class="num">
            <div class="actions">
              <RouterLink class="btn btn-small" :to="`/admin/products/${p.id}/edit`">Uredi</RouterLink>
              <button class="btn btn-small" @click="toggleActive(p)">{{ p.is_active ? 'Deaktiviraj' : 'Aktiviraj' }}</button>
              <button class="btn btn-small btn-danger" @click="remove(p)">Obriši</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </StateBlock>
</template>
