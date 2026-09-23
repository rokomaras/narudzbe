<script setup>
import { STATUS_LABELS } from '../utils/format'
defineProps({ status: { type: String, required: true } })
</script>

<template>
  <span class="badge" :class="`badge-${status}`">{{ STATUS_LABELS[status] ?? status }}</span>
</template>
