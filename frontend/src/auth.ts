import type { User, AuthResponse, AuthForm } from './types'
import { readonly, ref } from 'vue'
import { api, ApiError } from './api'

const currentUser = ref<User | null>(null)
const ready = ref(false)
let initialization: Promise<void> | undefined
export const user = readonly(currentUser)
export const authReady = readonly(ready)
export const authError = ref('')

window.addEventListener('auth-expired', () => { currentUser.value = null })

export function initializeAuth() {
  if (!initialization) initialization = api<AuthResponse>('/auth/me')
    .then(data => { currentUser.value = data.user })
    .catch(error => { if (error.status !== 401) authError.value = error.message })
    .finally(() => { ready.value = true })
  return initialization
}

export async function signIn(mode: 'login' | 'register', form: AuthForm) {
  const data = await api<AuthResponse>(`/auth/${mode}`, { method: 'POST', body: form })
  currentUser.value = data.user
  authError.value = ''
}

export async function signOut() {
  try {
    await api('/auth/logout', { method: 'POST' })
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error
  }
  currentUser.value = null
}
