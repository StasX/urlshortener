<script setup lang="ts">
defineProps({ message: { type: String, default: '' } })
</script>
<template><div v-if="message" class="error-message" role="alert">{{ message }}</div></template>
