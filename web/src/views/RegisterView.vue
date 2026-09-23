<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { serverFieldErrors, validateRegister } from '../utils/validation'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ username: '', password: '', full_name: '', email: '' })
const errors = ref({})
const serverError = ref('')
const submitting = ref(false)

const fields = [
  { key: 'full_name', label: 'Ime i prezime', type: 'text', autocomplete: 'name' },
  { key: 'email', label: 'Email', type: 'email', autocomplete: 'email' },
  { key: 'username', label: 'Korisničko ime', type: 'text', autocomplete: 'username' },
  { key: 'password', label: 'Lozinka', type: 'password', autocomplete: 'new-password' },
]

async function submit() {
  serverError.value = ''
  errors.value = validateRegister(form)
  if (Object.keys(errors.value).length > 0) return
  submitting.value = true
  try {
    await auth.register({ ...form, username: form.username.trim(), email: form.email.trim() })
    router.push(auth.homeRoute)
  } catch (e) {
    // greške koje dolaze s backenda: po poljima (422) ili opća (409 "korisničko ime zauzeto")
    const fieldErrors = serverFieldErrors(e)
    if (Object.keys(fieldErrors).length > 0) errors.value = fieldErrors
    else serverError.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-box card">
    <h1>Registracija</h1>
    <form class="form" novalidate @submit.prevent="submit">
      <div v-for="f in fields" :key="f.key" class="field" :class="{ invalid: errors[f.key] }">
        <label :for="f.key">{{ f.label }}</label>
        <input :id="f.key" v-model="form[f.key]" :type="f.type" :autocomplete="f.autocomplete" />
        <span v-if="errors[f.key]" class="field-error">{{ errors[f.key] }}</span>
      </div>
      <p v-if="serverError" class="alert alert-error">{{ serverError }}</p>
      <button class="btn btn-primary" :disabled="submitting">
        {{ submitting ? 'Spremam…' : 'Registriraj se' }}
      </button>
    </form>
    <p class="muted">Već imaš račun? <RouterLink to="/login">Prijavi se</RouterLink></p>
  </div>
</template>
