<script setup>
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'

const auth = useAuthStore()
const cart = useCartStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="nav">
    <div class="nav-inner">
      <strong class="brand">Narudžbe</strong>

      <nav class="nav-links">
        <template v-if="auth.isAdmin">
          <RouterLink to="/admin/orders">Narudžbe</RouterLink>
          <RouterLink to="/admin/products">Proizvodi</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/products">Katalog</RouterLink>
          <RouterLink to="/cart">Košarica<span v-if="cart.count" class="pill">{{ cart.count }}</span></RouterLink>
          <RouterLink to="/orders">Moje narudžbe</RouterLink>
        </template>
      </nav>

      <div class="nav-user">
        <span>{{ auth.user.full_name }} <small>({{ auth.isAdmin ? 'admin' : 'kupac' }})</small></span>
        <button class="btn btn-small" @click="logout">Odjava</button>
      </div>
    </div>
  </header>
</template>
