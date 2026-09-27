<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-4xl space-y-6">
      <header><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Assistant setup</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">AI Settings</h1><p class="mt-1 text-sm text-stone-500">Choose the model provider and connect its API key.</p></header>
      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <div class="border-b border-stone-100 p-5 sm:p-6"><h2 class="text-base font-semibold text-stone-900">Model provider</h2><p class="mt-1 text-sm text-stone-500">Your key is stored for this workspace and used for assistant responses.</p></div>
        <div class="space-y-6 p-5 sm:p-6">
          <div><p class="mb-2 text-sm font-medium text-stone-700">Choose a provider</p><div class="grid grid-cols-1 gap-3 sm:grid-cols-3"><button v-for="p in providers" :key="p.value" @click="provider = p.value" :aria-pressed="provider === p.value" class="rounded-xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-blue-500" :class="provider === p.value ? 'border-blue-300 bg-blue-50 ring-1 ring-blue-200' : 'border-stone-200 hover:border-blue-200 hover:bg-stone-50'"><span class="flex items-center justify-between"><span class="text-sm font-semibold" :class="provider === p.value ? 'text-blue-800' : 'text-stone-800'">{{ p.name }}</span><span class="h-4 w-4 rounded-full border flex items-center justify-center" :class="provider === p.value ? 'border-blue-600' : 'border-stone-300'"><span v-if="provider === p.value" class="h-2 w-2 rounded-full bg-blue-600"></span></span></span><span class="mt-1 block text-xs text-stone-500">{{ p.model }}</span></button></div></div>
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">{{ provider }} API key</span><span class="flex gap-2"><input v-model="apiKey" :type="showKey ? 'text' : 'password'" :placeholder="keyPlaceholder" autocomplete="new-password" class="min-w-0 flex-1 rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"/><button type="button" @click="showKey = !showKey" class="rounded-xl border border-stone-200 px-3 text-sm font-medium text-stone-600 hover:bg-stone-50">{{ showKey ? 'Hide' : 'Show' }}</button></span><span class="mt-1.5 block text-xs text-stone-500">{{ keyHelp }}. Existing key: {{ hasKey ? 'configured' : 'not configured' }}.</span></label>
          <div v-if="currentProvider" class="flex items-center gap-3 rounded-xl border border-stone-200 bg-stone-50 p-4"><span class="h-2.5 w-2.5 rounded-full" :class="hasKey ? 'bg-emerald-500' : 'bg-amber-500'"></span><p class="text-sm text-stone-600">Current provider: <span class="font-semibold text-stone-900">{{ currentProviderName }}</span></p><span class="ml-auto text-xs font-semibold" :class="hasKey ? 'text-emerald-700' : 'text-amber-700'">{{ hasKey ? 'Connected' : 'Needs a key' }}</span></div>
          <div class="flex flex-col gap-3 border-t border-stone-100 pt-5 sm:flex-row sm:items-center"><button @click="save" :disabled="saving || !apiKey.trim()" class="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">{{ saving ? 'Saving…' : 'Save settings' }}</button><p v-if="success" class="text-sm text-emerald-700" role="status">Settings saved successfully.</p><p v-if="error" class="text-sm text-rose-600" role="alert">{{ error }}</p></div>
        </div>
      </section>
      <section class="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-6"><h2 class="text-base font-semibold text-stone-900">Get an API key</h2><p class="mt-1 text-sm text-stone-500">Create a key with your provider, then paste it above.</p><div class="mt-4 grid gap-3 sm:grid-cols-3"><a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" class="rounded-xl border border-stone-200 p-4 text-sm font-semibold text-stone-800 transition hover:border-blue-200 hover:bg-blue-50">Google AI Studio<span class="mt-1 block text-xs font-normal text-stone-500">Create a Gemini key ↗</span></a><a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" class="rounded-xl border border-stone-200 p-4 text-sm font-semibold text-stone-800 transition hover:border-blue-200 hover:bg-blue-50">OpenAI Platform<span class="mt-1 block text-xs font-normal text-stone-500">Create an API key ↗</span></a><a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" class="rounded-xl border border-stone-200 p-4 text-sm font-semibold text-stone-800 transition hover:border-blue-200 hover:bg-blue-50">Anthropic Console<span class="mt-1 block text-xs font-normal text-stone-500">Create an API key ↗</span></a></div></section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()

const providers = [
  { value: 'gemini', name: 'Google Gemini', model: 'gemini-2.0-flash' },
  { value: 'openai', name: 'OpenAI', model: 'gpt-4o-mini' },
  { value: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-4' },
]

const provider = ref('gemini')
const apiKey = ref('')
const showKey = ref(false)
const saving = ref(false)
const success = ref(false)
const error = ref('')
const currentProvider = ref(null)
const hasKey = ref(false)

const currentProviderName = computed(() => {
  const p = providers.find(p => p.value === currentProvider.value)
  return p ? p.name : currentProvider.value
})

const keyPlaceholder = computed(() => {
  if (provider.value === 'gemini') return 'AIza...'
  if (provider.value === 'openai') return 'sk-...'
  if (provider.value === 'anthropic') return 'sk-ant-...'
  return 'Enter API key'
})

const keyHelp = computed(() => {
  if (provider.value === 'gemini') return 'Your Google Gemini API key from AI Studio'
  if (provider.value === 'openai') return 'Your OpenAI API key from platform.openai.com'
  if (provider.value === 'anthropic') return 'Your Anthropic API key from console.anthropic.com'
  return ''
})

async function save() {
  saving.value = true
  success.value = false
  error.value = ''
  try {
    const bid = businessStore.currentBusiness?.id
    await api.put(`/ai-settings/${bid}`, {
      llm_provider: provider.value,
      llm_api_key: apiKey.value,
    })
    currentProvider.value = provider.value
    hasKey.value = true
    apiKey.value = ''
    success.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save settings'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const bid = businessStore.currentBusiness?.id
    if (bid) {
      const { data } = await api.get(`/ai-settings/${bid}`)
      currentProvider.value = data.llm_provider
      hasKey.value = data.has_api_key
      if (data.llm_provider) provider.value = data.llm_provider
    }
  } catch (err) {
    console.error('Failed to load AI settings', err)
  }
})
</script>
