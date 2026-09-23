<script setup>
// Jedno mjesto koje osigurava SVA TRI UX stanja za svaki view koji dohvaća podatke:
//   loading -> spinner,  error -> poruka + "pokušaj ponovno",  empty -> poruka
// Kad nijedno nije aktivno, prikazuje se sadržaj (slot).
defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: 'Nema podataka.' },
})
defineEmits(['retry'])
</script>

<template>
  <div v-if="loading" class="state"><span class="spinner"></span> Učitavanje…</div>
  <div v-else-if="error" class="state state-error">
    <p>{{ error }}</p>
    <button class="btn" @click="$emit('retry')">Pokušaj ponovno</button>
  </div>
  <div v-else-if="empty" class="state">{{ emptyText }}</div>
  <slot v-else />
</template>
