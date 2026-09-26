<template>
  <main class="min-h-screen bg-blue-50 px-6 py-12 text-stone-800">
    <section class="mx-auto max-w-2xl rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
      <h1 class="text-2xl font-bold">Test your SupportAI chat widget</h1>
      <p class="mt-3 text-stone-600">
        Paste your business API key from the SupportAI Dashboard, select Start test, then use the chat button at the bottom of the page.
      </p>
      <label for="api-key" class="mt-6 block text-sm font-semibold">Business API key</label>
      <input
        id="api-key"
        v-model="apiKey"
        type="password"
        autocomplete="off"
        placeholder="Paste your API key"
        class="mt-2 w-full rounded-lg border border-stone-300 px-3 py-2"
      />
      <button
        type="button"
        :disabled="loading"
        class="mt-3 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white disabled:opacity-60"
        @click="startTest"
      >
        {{ loading ? 'Loading…' : 'Start test' }}
      </button>
      <p class="mt-4 min-h-6 text-sm text-stone-600" role="status">{{ status }}</p>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'

const apiKey = ref('')
const loading = ref(false)
const status = ref('')

function startTest() {
  const key = apiKey.value.trim()
  if (!key) {
    status.value = 'Paste your business API key first.'
    return
  }

  loading.value = true
  status.value = 'Loading the chat widget…'
  const script = document.createElement('script')
  script.src = `${window.location.origin}/widget/widget.js`
  script.onload = () => {
    window.SupportAI.init({ apiKey: key, serverUrl: window.location.origin })
    apiKey.value = ''
    status.value = 'Widget loaded. Use the chat button in the bottom corner.'
  }
  script.onerror = () => {
    status.value = 'Could not load the widget. Please try again.'
    loading.value = false
  }
  document.body.appendChild(script)
}
</script>
