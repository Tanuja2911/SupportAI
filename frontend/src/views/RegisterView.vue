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
        <p class="auth-subtitle">Create your account</p>
      </div>

      <div v-if="error" class="auth-error" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div>
          <label for="register-name" class="auth-label">Full Name</label>
          <input
            v-model="fullName"
            id="register-name"
            type="text"
            autocomplete="name"
            required
            class="auth-input"
            placeholder="John Doe"
          />
        </div>
        <div>
          <label for="register-email" class="auth-label">Email</label>
          <input
            v-model="email"
            id="register-email"
            type="email"
            autocomplete="email"
            required
            class="auth-input"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label for="register-password" class="auth-label">Password</label>
          <input
            v-model="password"
            id="register-password"
            type="password"
            autocomplete="new-password"
            required
            minlength="6"
            class="auth-input"
            placeholder="Min. 6 characters"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="auth-submit"
        >
          {{ loading ? 'Creating account...' : 'Create Account' }}
        </button>
      </form>

      <p class="auth-footer">
        Already have an account?
        <router-link to="/login" class="auth-link">Sign in</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()

const fullName = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  loading.value = true
  error.value = ''
  try {
    await auth.register(email.value, fullName.value, password.value)
    router.push('/setup')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
