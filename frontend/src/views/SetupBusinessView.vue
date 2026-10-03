<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-blue-50 p-4">
    <div class="pointer-events-none absolute -left-24 top-0 h-72 w-72 rounded-full bg-blue-200/50 blur-3xl"></div><div class="pointer-events-none absolute -bottom-24 -right-20 h-80 w-80 rounded-full bg-indigo-100 blur-3xl"></div>
    <div class="relative w-full max-w-lg rounded-2xl border border-stone-200 bg-white p-6 shadow-xl shadow-blue-950/5 sm:p-8">
      <div class="mb-8 text-center">
        <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-sm shadow-blue-200"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/></svg></span>
        <h1 class="mt-4 text-2xl font-bold tracking-tight text-stone-900">Set up your workspace</h1>
        <p class="mt-2 text-sm text-stone-500">Add your business details to create your first support assistant.</p>
      </div>

      <div v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleSetup" class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-stone-700">Business name</label>
          <input
            v-model="name"
            type="text"
            required
            class="w-full rounded-xl border border-stone-200 px-4 py-2.5 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="Acme Corp"
          />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-stone-700">Description <span class="font-normal text-stone-400">(optional)</span></label>
          <textarea
            v-model="description"
            rows="3"
            class="w-full resize-y rounded-xl border border-stone-200 px-4 py-2.5 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="What does your business do?"
          ></textarea>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-stone-700">Website <span class="font-normal text-stone-400">(optional)</span></label>
          <input
            v-model="website"
            type="url"
            class="w-full rounded-xl border border-stone-200 px-4 py-2.5 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            placeholder="https://acme.com"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-xl bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
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
