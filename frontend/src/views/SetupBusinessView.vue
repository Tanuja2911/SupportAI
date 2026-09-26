<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">Set Up Your Business</h1>
        <p class="text-gray-500 mt-2">Create your first AI support agent</p>
      </div>

      <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
        {{ error }}
      </div>

      <form @submit.prevent="handleSetup" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Business Name</label>
          <input
            v-model="name"
            type="text"
            required
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            placeholder="Acme Corp"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
          <textarea
            v-model="description"
            rows="3"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
            placeholder="What does your business do?"
          ></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Website (optional)</label>
          <input
            v-model="website"
            type="url"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            placeholder="https://acme.com"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50"
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
