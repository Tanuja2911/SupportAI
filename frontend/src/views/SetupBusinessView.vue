<template>
  <div class="auth-page">
    <div class="auth-card w-full max-w-lg">
      <div class="auth-heading">
        <span class="auth-mark" aria-hidden="true"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/></svg></span>
        <h1>Set up your workspace</h1>
        <p class="auth-subtitle">Add your business details to create your first support assistant.</p>
      </div>

      <div v-if="error" class="auth-error" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleSetup" class="auth-form">
        <div>
          <label class="auth-label" for="business-name">Business name</label>
          <input
            id="business-name"
            v-model="name"
            type="text"
            required
            class="auth-input"
            placeholder="Acme Corp"
          />
        </div>
        <div>
          <label class="auth-label" for="business-description">Description <span class="font-normal text-stone-400">(optional)</span></label>
          <textarea
            id="business-description"
            v-model="description"
            rows="3"
            class="auth-input resize-y"
            placeholder="What does your business do?"
          ></textarea>
        </div>
        <div>
          <label class="auth-label" for="business-website">Website <span class="font-normal text-stone-400">(optional)</span></label>
          <input
            id="business-website"
            v-model="website"
            type="url"
            class="auth-input"
            placeholder="https://acme.com"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="auth-submit"
        >
          {{ loading ? 'Creating...' : 'Create Business' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBusinessStore } from '../stores/business.js'

const router = useRouter()
const businessStore = useBusinessStore()

const name = ref('')
const description = ref('')
const website = ref('')
const loading = ref(false)
const error = ref('')

async function handleSetup() {
  loading.value = true
  error.value = ''
  try {
    await businessStore.createBusiness(name.value, description.value, website.value)
    router.push('/app')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create business'
  } finally {
    loading.value = false
  }
}
</script>
