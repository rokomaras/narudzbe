<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const errors = ref({})
const serverError = ref('')
const submitting = ref(false)

function validate() {
  const e = {}
  if (!username.value.trim()) e.username = 'Unesi korisničko ime'
  if (!password.value) e.password = 'Unesi lozinku'
  errors.value = e
  return Object.keys(e).length === 0
}

async function submit() {
  serverError.value = ''
  if (!validate()) return // klijentska validacija: ne šaljemo prazno na server
  submitting.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    const redirect = route.query.redirect
    router.push(typeof redirect === 'string' && redirect.startsWith('/') ? redirect : auth.homeRoute)
  } catch (e) {
    serverError.value = e.message // npr. "Pogrešno korisničko ime ili lozinka"
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-box card">
    <h1>Prijava</h1>
    <p v-if="route.query.expired" class="alert alert-info">Sesija je istekla. Prijavi se ponovno.</p>

    <form class="form" novalidate @submit.prevent="submit">
      <div class="field" :class="{ invalid: errors.username }">
        <label for="username">Korisničko ime</label>
        <input id="username" v-model="username" autocomplete="username" />
        <span v-if="errors.username" class="field-error">{{ errors.username }}</span>
      </div>
      <div class="field" :class="{ invalid: errors.password }">
        <label for="password">Lozinka</label>
        <input id="password" v-model="password" type="password" autocomplete="current-password" />
        <span v-if="errors.password" class="field-error">{{ errors.password }}</span>
      </div>
      <p v-if="serverError" class="alert alert-error">{{ serverError }}</p>
      <button class="btn btn-primary" :disabled="submitting">
        {{ submitting ? 'Prijava…' : 'Prijavi se' }}
      </button>
    </form>

    <p class="muted">Nemaš račun? <RouterLink to="/register">Registriraj se</RouterLink></p>
  </div>
</template>
