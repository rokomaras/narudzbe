<script setup>
import { productsApi } from '../api/products'
import StateBlock from '../components/StateBlock.vue'
import { useLoader } from '../composables/useLoader'
import { useCartStore } from '../stores/cart'
import { formatEuro } from '../utils/format'

const cart = useCartStore()
const { data: products, loading, error, load } = useLoader(() => productsApi.list())
load()

function inCart(product) {
  return cart.items.find((i) => i.productId === product.id)?.quantity ?? 0
}
</script>

<template>
  <h1>Katalog</h1>
  <StateBlock
    :loading="loading"
    :error="error"
    :empty="!products || products.length === 0"
    empty-text="Trenutno nema proizvoda u katalogu."
    @retry="load"
  >
    <div class="grid">
      <article v-for="p in products" :key="p.id" class="card product">
        <h3>{{ p.name }}</h3>
        <p class="muted">{{ p.description }}</p>
        <span v-if="p.stock === 0" class="stock-out">Nema na zalihi</span>
        <span v-else-if="p.stock <= 5" class="stock-low">Još samo {{ p.stock }} kom</span>
        <span v-else class="muted">Na zalihi: {{ p.stock }}</span>
        <div class="price">{{ formatEuro(p.price_cents) }}</div>
        <button
          class="btn btn-primary"
          :disabled="p.stock === 0 || inCart(p) >= p.stock"
          @click="cart.add(p)"
        >
          Dodaj u košaricu<template v-if="inCart(p)"> ({{ inCart(p) }})</template>
        </button>
      </article>
    </div>
  </StateBlock>
</template>
