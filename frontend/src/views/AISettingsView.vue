<template>
  <div class="p-8 max-w-2xl">
    <h2 class="text-2xl font-bold text-gray-800 mb-2">AI Settings</h2>
    <p class="text-gray-500 text-sm mb-6">Configure which LLM provider powers your AI agent.</p>

    <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-6">
      <!-- Provider Selection -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">LLM Provider</label>
        <div class="grid grid-cols-3 gap-3">
          <button
            v-for="p in providers"
            :key="p.value"
            @click="provider = p.value"
            class="p-4 rounded-lg border-2 text-center transition"
            :class="provider === p.value ? 'border-pink-600 bg-pink-50' : 'border-gray-200 hover:border-gray-300'"
          >
            <p class="font-semibold text-sm" :class="provider === p.value ? 'text-pink-700' : 'text-gray-800'">{{ p.name }}</p>
            <p class="text-xs text-gray-400 mt-1">{{ p.model }}</p>
          </button>
        </div>
      </div>

      <!-- API Key Input -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">API Key</label>
        <div class="flex gap-3">
          <input
            v-model="apiKey"
            :type="showKey ? 'text' : 'password'"
            :placeholder="keyPlaceholder"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-pink-500"
          />
          <button @click="showKey = !showKey" class="px-3 py-2 text-sm text-gray-500 border border-gray-300 rounded-lg hover:bg-pink-50">
            {{ showKey ? 'Hide' : 'Show' }}
          </button>
        </div>
        <p class="text-xs text-gray-400 mt-2">{{ keyHelp }}</p>
      </div>

      <!-- Status -->
      <div v-if="currentProvider" class="bg-pink-50 rounded-lg p-4">
        <p class="text-sm text-gray-600">
          Current: <span class="font-medium text-gray-800">{{ currentProviderName }}</span>
          <span v-if="hasKey" class="ml-2 text-green-600 text-xs font-medium">Key configured</span>
          <span v-else class="ml-2 text-red-500 text-xs font-medium">No key set</span>
        </p>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3">
        <button
          @click="save"
          :disabled="saving || !apiKey.trim()"
          class="px-6 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 transition disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : 'Save Settings' }}
        </button>
        <p v-if="success" class="text-sm text-green-600">Settings saved successfully.</p>
        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
      </div>
    </div>

    <!-- Info -->
    <div class="mt-6 bg-pink-50 rounded-xl border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Where to get API keys</h3>
      <div class="space-y-2 text-sm text-gray-500">
        <p><span class="font-medium text-gray-700">Google Gemini</span> — Get a free key from Google AI Studio (aistudio.google.com)</p>
        <p><span class="font-medium text-gray-700">OpenAI</span> — Create a key at platform.openai.com/api-keys</p>
        <p><span class="font-medium text-gray-700">Anthropic</span> — Create a key at console.anthropic.com/settings/keys</p>
      </div>
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
