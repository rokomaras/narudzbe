<script setup>
import { RouterView } from 'vue-router'
import AppNav from './components/AppNav.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
</script>

<template>
  <AppNav v-if="auth.isAuthenticated" />
  <main class="container">
    <RouterView />
  </main>
</template>
