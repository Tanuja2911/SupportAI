<template>
  <div class="auth-page">
    <div class="auth-card">
      <router-link to="/" class="auth-back-link">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" /></svg>
        Back to home
      </router-link>
      <div class="auth-heading">
        <span class="auth-mark" aria-hidden="true">S</span>
        <p class="auth-eyebrow">SUPPORT WORKSPACE</p>
        <h1>SupportAI</h1>
        <p class="auth-subtitle">Sign in to your account</p>
      </div>

      <div v-if="error" class="auth-error" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div>
          <label for="login-email" class="auth-label">Email</label>
          <input
            v-model="email"
            id="login-email"
            type="email"
            autocomplete="email"
            required
            class="auth-input"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label for="login-password" class="auth-label">Password</label>
          <input
            v-model="password"
            id="login-password"
            type="password"
            autocomplete="current-password"
            required
            class="auth-input"
            placeholder="Your password"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="auth-submit"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <p class="auth-footer">
        Don't have an account?
        <router-link to="/register" class="auth-link">Sign up</router-link>
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
