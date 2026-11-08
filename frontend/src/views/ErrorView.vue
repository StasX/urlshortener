<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template><section class="error-page"><div class="card error-card"><div class="card-body"><span class="eyebrow">A small detour</span><div class="error-code" aria-hidden="true">404</div><h1>This link took a wrong turn.</h1><p class="muted">We couldn't find that page. Check the address, or head back to create something new.</p><RouterLink class="btn btn-dark" to="/">Back to link tools ↗</RouterLink></div></div></section></template>
