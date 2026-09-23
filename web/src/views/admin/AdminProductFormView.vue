<script setup>
// Isti view za "novi proizvod" (/admin/products/new) i "uredi" (/admin/products/:id/edit).
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { productsApi } from '../../api/products'
import StateBlock from '../../components/StateBlock.vue'
import { useLoader } from '../../composables/useLoader'
import { eurosToCents } from '../../utils/format'
import { serverFieldErrors } from '../../utils/validation'

const props = defineProps({ id: { type: String, default: '' } })
const router = useRouter()
const isEdit = computed(() => props.id !== '')

const form = reactive({ name: '', description: '', price: '', stock: '0', is_active: true })
const errors = ref({})
const serverError = ref('')
const submitting = ref(false)

// U modu uređivanja prvo dohvati proizvod i popuni formu.
const { data: product, loading, error, load } = useLoader(() => productsApi.get(props.id))
if (isEdit.value) load()
watch(product, (p) => {
  if (!p) return
  form.name = p.name
  form.description = p.description ?? ''
  form.price = (p.price_cents / 100).toFixed(2)
  form.stock = String(p.stock)
  form.is_active = p.is_active
})

function validate() {
  const e = {}
  if (!form.name.trim()) e.name = 'Naziv je obavezan'
  else if (form.name.trim().length > 100) e.name = 'Naziv može imati najviše 100 znakova'
  const cents = eurosToCents(form.price)
  if (!Number.isFinite(cents) || cents <= 0) e.price = 'Cijena mora biti veća od 0 (npr. 19,99)'
  const stock = Number(form.stock)
  if (!Number.isInteger(stock) || stock < 0) e.stock = 'Zaliha mora biti cijeli broj ≥ 0'
  errors.value = e
  return Object.keys(e).length === 0
}

async function submit() {
  serverError.value = ''
  if (!validate()) return
  submitting.value = true
  const payload = {
    name: form.name.trim(),
    description: form.description.trim(),
    price_cents: eurosToCents(form.price),
    stock: Number(form.stock),
    is_active: form.is_active,
  }
  try {
    if (isEdit.value) await productsApi.update(props.id, payload)
    else await productsApi.create(payload)
    router.push('/admin/products')
  } catch (e) {
    const fe = serverFieldErrors(e)
    // backend polje se zove price_cents, u formi je "price"
    if (fe.price_cents) fe.price = fe.price_cents
    if (Object.keys(fe).length > 0) errors.value = fe
    else serverError.value = e.message // npr. 409 "Proizvod s tim imenom već postoji"
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <RouterLink to="/admin/products">← Natrag na proizvode</RouterLink>
  <h1 style="margin-top: 1rem">{{ isEdit ? 'Uredi proizvod' : 'Novi proizvod' }}</h1>

  <StateBlock :loading="isEdit && loading" :error="isEdit ? error : ''" @retry="load">
    <form class="card form" novalidate @submit.prevent="submit">
      <div class="field" :class="{ invalid: errors.name }">
        <label for="name">Naziv</label>
        <input id="name" v-model="form.name" />
        <span v-if="errors.name" class="field-error">{{ errors.name }}</span>
      </div>
      <div class="field" :class="{ invalid: errors.description }">
        <label for="description">Opis</label>
        <textarea id="description" v-model="form.description" rows="3"></textarea>
        <span v-if="errors.description" class="field-error">{{ errors.description }}</span>
      </div>
      <div class="field" :class="{ invalid: errors.price }">
        <label for="price">Cijena (€)</label>
        <input id="price" v-model="form.price" inputmode="decimal" placeholder="19,99" />
        <span v-if="errors.price" class="field-error">{{ errors.price }}</span>
      </div>
      <div class="field" :class="{ invalid: errors.stock }">
        <label for="stock">Zaliha (kom)</label>
        <input id="stock" v-model="form.stock" type="number" min="0" />
        <span v-if="errors.stock" class="field-error">{{ errors.stock }}</span>
      </div>
      <label><input v-model="form.is_active" type="checkbox" /> Aktivan (vidljiv kupcima)</label>

      <p v-if="serverError" class="alert alert-error">{{ serverError }}</p>
      <button class="btn btn-primary" :disabled="submitting">
        {{ submitting ? 'Spremam…' : 'Spremi' }}
      </button>
    </form>
  </StateBlock>
</template>
