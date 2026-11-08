<script setup lang="ts">
import type { LinkResponse } from '../types'
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, errorMessage } from '../api'
import { user } from '../auth'
import ErrorMessage from '../components/ErrorMessage.vue'

const destination = ref(''), shortInput = ref('')
const shortResult = ref(''), resolved = ref('')
const createError = ref(''), resolveError = ref('')
const creating = ref(false), resolving = ref(false)
async function shorten() {
  creating.value = true; createError.value = ''; shortResult.value = ''
  try { shortResult.value = (await api<LinkResponse>('/links', { method: 'POST', body: { url: destination.value.trim() } })).url }
  catch (error) { createError.value = errorMessage(error) }
  finally { creating.value = false }
}
async function resolve() {
  resolving.value = true; resolveError.value = ''; resolved.value = ''
  try { resolved.value = (await api<LinkResponse>('/resolve', { method: 'POST', body: { url: shortInput.value.trim() } })).url }
  catch (error) { resolveError.value = errorMessage(error) }
  finally { resolving.value = false }
}
</script>
<template>
  <div class="home-page">
    <section class="hero"><span class="eyebrow"><span class="status-dot"></span> A little link goes a long way</span><h1>Long links.<br><span>Short stories.</span></h1><p>Make your next link easier to share. Shorten a URL, uncover its destination, and keep track of the clicks that follow.</p><div class="hero-note">↗ Small links. A smoother way to share.</div></section>
    <div class="home tool-grid">
      <section class="card tool-card"><div class="card-body">
        <div class="tool-heading"><span class="tool-icon" aria-hidden="true">↗</span><span class="eyebrow">01 / Create</span></div><h2>Less link, more impact.</h2><p class="muted">Turn a lengthy URL into something worth sharing.</p>
        <form @submit.prevent="shorten"><label for="fullUrl">Your destination URL</label><input id="fullUrl" v-model="destination" type="url" class="form-control" placeholder="https://example.com/your-next-big-idea" required maxlength="4096"><button class="btn btn-dark tool-submit" :disabled="creating">{{ creating ? 'Creating your link…' : 'Create short link' }} <span aria-hidden="true">↗</span></button></form>
        <ErrorMessage :message="createError" /><output v-if="shortResult" class="form-control result-box" aria-live="polite"><a :href="shortResult" target="_blank" rel="noopener noreferrer">{{ shortResult }}</a></output>
        <p v-if="!user" class="small-note">Guest links expire after 24 hours and cannot be managed. <RouterLink to="/login">Sign in</RouterLink> or <RouterLink to="/register">create an account</RouterLink> before shortening to keep your links and track visits.</p>
      </div></section>
      <section class="card tool-card resolve-card"><div class="card-body"><div class="tool-heading"><span class="tool-icon" aria-hidden="true">⌕</span><span class="eyebrow">02 / Explore</span></div><h2>Know where it goes.</h2><p class="muted">Reveal the next destination behind a shortened link.</p>
        <form @submit.prevent="resolve"><label for="url">Shortened URL</label><input id="url" v-model="shortInput" type="url" class="form-control" placeholder="https://short.example/aBc123" required maxlength="4096"><button class="btn btn-outline-dark tool-submit" :disabled="resolving">{{ resolving ? 'Looking up destination…' : 'Reveal destination' }} <span aria-hidden="true">→</span></button></form>
        <ErrorMessage :message="resolveError" /><output v-if="resolved" class="form-control result-box" aria-live="polite">{{ resolved }}</output><p class="small-note">No account needed. Just paste a link and take a look.</p>
      </div></section>
    </div>
    <div class="benefit-strip"><span>01 <strong>Share with ease</strong></span><span>02 <strong>See the destination</strong></span><span>03 <strong>Track your clicks</strong></span></div>
  </div>
</template>
