<script setup lang="ts">
import type { ShortLink } from '../types'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, errorMessage } from '../api'
import ErrorMessage from '../components/ErrorMessage.vue'
import VisitsChart from '../components/VisitsChart.vue'
const links = ref<ShortLink[]>([]), loading = ref(true), error = ref(''), deleting = ref<string | null>(null), deleteErrors = ref<Record<string, string>>({})
const totalVisits = computed(() => links.value.reduce((total, link) => total + link.visits, 0))
async function load() {
  loading.value = true; error.value = ''
  try { links.value = await api<ShortLink[]>('/links') }
  catch (failure) { error.value = errorMessage(failure) }
  finally { loading.value = false }
}
async function remove(link: ShortLink) {
  deleting.value = link.id; deleteErrors.value[link.id] = ''
  try { await api(`/links/${encodeURIComponent(link.id)}`, { method: 'DELETE' }); links.value = links.value.filter(item => item.id !== link.id) }
  catch (failure) { deleteErrors.value[link.id] = errorMessage(failure) }
  finally { deleting.value = null }
}
onMounted(load)
</script>
<template>
  <div class="dashboard-page">
    <section class="page-heading"><span class="eyebrow">Your link collection</span><h1>A little overview.</h1><p class="muted">All your links and the clicks they collect, in one place.</p><RouterLink class="btn btn-dark" to="/">Create a link ↗</RouterLink></section>
    <div class="dashboard dashboard-grid">
      <section aria-label="Your links"><div class="section-heading"><h2>Your links</h2><span class="eyebrow">{{ links.length }} links · {{ totalVisits }} visits</span></div>
        <p v-if="loading" class="empty-state" role="status">Loading your links…</p><ErrorMessage :message="error" /><button v-if="error" class="btn btn-outline-dark" @click="load">Try again</button><p v-if="!loading && !error && !links.length" class="empty-state">No links yet. Create your first short link to get started.</p>
        <div id="urlsContainer"><article v-for="link in links" :key="link.id" class="card"><div class="card-body"><div class="mt-2"><b>Short link:</b> <a :href="link.shortUrl" target="_blank" rel="noopener noreferrer">{{ link.shortUrl }}</a></div><div class="mt-2"><b>Destination:</b> {{ link.fullUrl }}</div><div class="mt-2 mb-4"><b>Visits:</b> {{ link.visits }}</div><ErrorMessage :message="deleteErrors[link.id]" /><button class="btn btn-danger" :disabled="deleting !== null" @click="remove(link)">{{ deleting === link.id ? 'Removing…' : 'Remove link' }}</button></div></article></div>
      </section>
      <section class="card chart-panel"><div class="card-body"><span class="eyebrow">The bigger picture</span><h2>Clicks at a glance</h2><p class="muted">How visits are shared across your links.</p><VisitsChart v-if="!loading && !error" :links="links" /><p v-if="loading" class="small-note">Loading statistics…</p><ErrorMessage v-if="error" message="Statistics are temporarily unavailable." /></div></section>
    </div>
  </div>
</template>
