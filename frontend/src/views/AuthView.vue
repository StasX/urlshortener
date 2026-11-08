<script setup lang="ts">
import { errorMessage } from '../api'
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { signIn } from '../auth'
import ErrorMessage from '../components/ErrorMessage.vue'

const props = defineProps({ mode: { type: String as () => 'login' | 'register', required: true } })
const register = computed(() => props.mode === 'register')
const form = reactive({ firstName: '', lastName: '', email: '', password: '', repeatPassword: '' })
const error = ref(''), busy = ref(false)
const router = useRouter(), route = useRoute()
watch(() => props.mode, () => { error.value = ''; form.password = ''; form.repeatPassword = '' })
async function submit() {
  error.value = ''
  if (register.value && form.password !== form.repeatPassword) { error.value = 'Passwords must match.'; return }
  busy.value = true
  try { await signIn(props.mode, { ...form }); await router.push(route.query.next === '/dashboard' ? '/dashboard' : '/') }
  catch (failure) { error.value = errorMessage(failure) }
  finally { form.password = ''; form.repeatPassword = ''; busy.value = false }
}
</script>
<template>
  <form :class="register ? 'register-form' : 'login-form'" @submit.prevent="submit">
    <span class="eyebrow">{{ register ? 'Join Shorty' : 'Good to see you' }}</span><h1>{{ register ? 'Start something short.' : 'Welcome back.' }}</h1><p class="muted">{{ register ? 'Create your free account. Make room for better links.' : 'Your links are right where you left them.' }}</p>
    <template v-if="register"><label for="firstName">First name</label><input id="firstName" v-model="form.firstName" class="form-control" autocomplete="given-name" required minlength="2" maxlength="30"><label for="lastName">Last name</label><input id="lastName" v-model="form.lastName" class="form-control" autocomplete="family-name" required minlength="2" maxlength="30"></template>
    <label for="email">Email address</label><input id="email" v-model="form.email" class="form-control" type="email" autocomplete="username" placeholder="you@example.com" required minlength="5" maxlength="64">
    <label for="password">Password</label><input id="password" v-model="form.password" class="form-control" type="password" :autocomplete="register ? 'new-password' : 'current-password'" required>
    <template v-if="register"><label for="repeatPassword">Repeat password</label><input id="repeatPassword" v-model="form.repeatPassword" class="form-control" type="password" autocomplete="new-password" required></template>
    <ErrorMessage :message="error" /><button class="btn btn-dark auth-submit" :disabled="busy">{{ busy ? 'Please wait…' : register ? 'Create account' : 'Sign in' }}</button>
    <p class="small-note">{{ register ? 'Already have an account?' : 'New to Shorty?' }} <RouterLink :to="register ? '/login' : '/register'">{{ register ? 'Sign in' : 'Create an account' }}</RouterLink></p>
  </form>
</template>
