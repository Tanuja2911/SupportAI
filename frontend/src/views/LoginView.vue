<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-blue-50 p-4">
    <div class="pointer-events-none absolute -left-24 top-0 h-72 w-72 rounded-full bg-blue-200/50 blur-3xl"></div><div class="pointer-events-none absolute -bottom-24 -right-20 h-80 w-80 rounded-full bg-indigo-100 blur-3xl"></div>
    <div class="relative w-full max-w-md rounded-2xl border border-stone-200 bg-white p-6 shadow-xl shadow-blue-950/5 sm:p-8">
      <router-link to="/" class="mb-6 inline-flex items-center gap-1 text-sm text-stone-500 transition hover:text-blue-700">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" /></svg>
        Back to home
      </router-link>
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold tracking-tight text-stone-900">Support<span class="text-blue-600">AI</span></h1>
        <p class="mt-2 text-stone-500">Sign in to your workspace</p>
      </div>

      <div v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-stone-700">Email</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="w-full rounded-xl border border-stone-200 px-4 py-2.5 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-stone-700">Password</label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full rounded-xl border border-stone-200 px-4 py-2.5 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="Your password"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-xl bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-stone-500">
        Don't have an account?
        <router-link to="/register" class="text-blue-600 font-medium hover:underline">Sign up</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useBusinessStore } from '../stores/business.js'

const router = useRouter()
const auth = useAuthStore()
const businessStore = useBusinessStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    const businesses = await businessStore.fetchMyBusinesses()
    if (businesses.length > 0) {
      router.push('/app')
    } else {
      router.push('/setup')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
