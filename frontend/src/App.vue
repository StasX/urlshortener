<script setup lang="ts">
import { errorMessage } from './api'
import { ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { user, authReady, authError, signOut } from './auth'
import ErrorMessage from './components/ErrorMessage.vue'

const route = useRoute()
const router = useRouter()
const signingOut = ref(false)
async function logout() {
  signingOut.value = true
  authError.value = ''
  try { await signOut(); await router.push('/') }
  catch (error) { authError.value = errorMessage(error) }
  finally { signingOut.value = false }
}
watch(user, value => {
  if (!value && route.meta.protected) router.replace({ path: '/login', query: { next: '/dashboard' } })
})
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <nav class="site-nav" aria-label="Main navigation">
        <RouterLink to="/" class="brand"><span class="brand-icon" aria-hidden="true">↗</span> Shorty<span class="brand-dot">.</span></RouterLink>
        <div class="nav-links">
          <RouterLink to="/" :class="{ active: route.path === '/' }">Link tools</RouterLink>
          <RouterLink v-if="user" to="/dashboard" active-class="active">Dashboard</RouterLink>
        </div>
        <div v-if="authReady" class="nav-account">
          <template v-if="user"><span id="helloUser">Hi, {{ user.first_name }}</span><button class="nav-signout" :disabled="signingOut" @click="logout">{{ signingOut ? 'Signing out…' : 'Sign out' }}</button></template>
          <template v-else><RouterLink class="nav-login" to="/login">Sign in</RouterLink><RouterLink class="btn btn-dark btn-sm" to="/register">Get started ↗</RouterLink></template>
        </div>
      </nav>
    </header>
    <div v-if="authError" class="global-error"><ErrorMessage :message="authError" /></div>
    <main><RouterView v-if="authReady" /><p v-else class="empty-state" role="status">Getting your links ready…</p></main>
    <footer class="site-footer"><span><strong>Shorty.</strong> Less link. More possibility.</span><span>© Stanislav Mestechkin</span></footer>
  </div>
</template>
