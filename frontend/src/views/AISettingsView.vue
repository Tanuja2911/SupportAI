<template>
  <div class="p-8 max-w-3xl">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">AI Settings</h2>
      <p class="text-gray-500 text-sm mt-1">
        Configure your LLM provider and credentials. Use SupportAI's platform default key or bring your own API key (BYOK).
      </p>
    </div>

    <!-- Status Overview Card -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 mb-6 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-1">Current Active Configuration</h3>
          <p class="text-sm text-gray-600">
            Active Provider:
            <span class="font-semibold text-gray-900">{{ currentProviderName }}</span>
          </p>
          <p class="text-xs text-gray-500 mt-1">
            <span v-if="hasKey">
              Your AI agent is using your custom organization key, overriding the platform default.
            </span>
            <span v-else-if="isUsingPlatformDefault">
              Using the SupportAI default Google Gemini key.
            </span>
            <span v-else class="text-amber-600 font-medium">
              No API key is currently configured. Please enter a key below to enable AI chat responses.
            </span>
          </p>
        </div>

        <!-- Platform Fallback Status Badge -->
        <div class="flex-shrink-0">
          <!-- Custom Key Active (BYOK) -->
          <div
            v-if="hasKey"
            class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm"
          >
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Custom Key Active (BYOK)
          </div>

          <!-- Platform Default Active -->
          <div
            v-else-if="isUsingPlatformDefault"
            class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 shadow-sm"
          >
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
            Platform Default Active
          </div>

          <!-- No Key Configured -->
          <div
            v-else
            class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 shadow-sm"
          >
            <span class="w-2 h-2 rounded-full bg-amber-500"></span>
            No Key Configured
          </div>
        </div>
      </div>
    </div>

    <!-- Configuration Form -->
    <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-6 shadow-sm">
      <!-- Provider Selection -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-sm font-medium text-gray-700">Select LLM Provider</label>
          <span class="text-xs text-gray-400">Choose model for customer interactions</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <button
            type="button"
            v-for="p in providers"
            :key="p.value"
            @click="provider = p.value"
            class="p-4 rounded-xl border-2 text-left transition relative"
            :class="provider === p.value ? 'border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-500' : 'border-gray-200 hover:border-gray-300 bg-white'"
          >
            <div class="flex items-center justify-between">
              <p class="font-semibold text-sm" :class="provider === p.value ? 'text-indigo-700' : 'text-gray-800'">{{ p.name }}</p>
              <span v-if="p.value === 'gemini'" class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">Default</span>
            </div>
            <p class="text-xs text-gray-400 mt-1 font-mono">{{ p.model }}</p>
          </button>
        </div>
      </div>

      <!-- API Key Input -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          <span>API Key</span>
          <span v-if="hasKey" class="ml-2 text-xs font-normal text-emerald-600">
            (Custom key currently active)
          </span>
        </label>
        <p class="text-xs text-gray-500 mb-2">
          {{ hasKey ? 'A custom key is already saved. Enter a replacement key, or reset to the platform default to remove it.' : 'Enter your provider API key below.' }}
        </p>

        <div class="flex gap-2">
          <input
            v-model="apiKey"
            :type="showKey ? 'text' : 'password'"
            :placeholder="keyPlaceholder"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-mono outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          />
          <button
            type="button"
            @click="showKey = !showKey"
            class="px-3.5 py-2 text-xs font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            {{ showKey ? 'Hide' : 'Show' }}
          </button>
        </div>
        <p class="text-xs text-gray-400 mt-2">{{ keyHelp }}</p>
      </div>

      <div class="flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 bg-gray-50 p-4">
        <button
          type="button"
          @click="testConnection"
          :disabled="testing || saving || resetting"
          class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition hover:border-indigo-400 hover:text-indigo-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span v-if="testing" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></span>
          {{ testing ? 'Testing connection…' : 'Test connection' }}
        </button>
        <span class="text-xs text-gray-500">Runs a tiny live completion to verify key, model access, and generation. It uses a small output budget (up to 16 tokens for reasoning models) and may count toward provider usage. Blank tests the active saved/platform key.</span>
        <div v-if="connectionResult" class="w-full rounded-lg border p-3 text-sm" :class="connectionResult.status === 'connected' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-rose-200 bg-rose-50 text-rose-800'" role="status" aria-live="polite">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <strong>{{ connectionResult.status === 'connected' ? 'Connected & verified' : 'Connection needs attention' }}</strong>
            <span v-if="connectionResult.latency_ms" class="text-xs opacity-75">{{ connectionResult.latency_ms }} ms · {{ connectionResult.provider }}</span>
          </div>
          <p class="mt-1">{{ connectionResult.message }}</p>
          <p v-if="connectionResult.diagnostic" class="mt-1 text-xs opacity-80">{{ connectionResult.diagnostic }}</p>
          <p v-if="connectionResult.action_hint" class="mt-1 text-xs">{{ connectionResult.action_hint }}</p>
        </div>
      </div>

      <!-- Feedback Messages -->
      <div v-if="success" class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-sm text-emerald-700">
        <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <span>{{ success }}</span>
      </div>

      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-600">
        <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-gray-100">
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="save"
            :disabled="saving || resetting || !apiKey.trim()"
            class="px-6 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {{ saving ? 'Saving...' : 'Save Custom Key' }}
          </button>
        </div>

        <!-- Reset to Platform Default Button (visible when custom key exists) -->
        <button
          v-if="hasKey"
          type="button"
          @click="resetToPlatformDefault"
          :disabled="saving || resetting"
          class="px-4 py-2.5 border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 rounded-lg text-sm font-medium transition disabled:opacity-50 flex items-center gap-1.5"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          {{ resetting ? 'Resetting...' : 'Reset to Platform Default' }}
        </button>
      </div>
    </div>

    <!-- API Keys Reference Information -->
    <div class="mt-6 bg-gray-50 rounded-xl border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Where to get API keys</h3>
      <div class="space-y-3 text-sm text-gray-600">
        <div class="flex items-start gap-2">
          <span class="font-medium text-gray-800 min-w-28">Google Gemini:</span>
          <span>Get a key from <a href="https://aistudio.google.com" target="_blank" rel="noopener" class="text-indigo-600 hover:underline">Google AI Studio</a>. (Recommended default)</span>
        </div>
        <div class="flex items-start gap-2">
          <span class="font-medium text-gray-800 min-w-28">OpenAI:</span>
          <span>Generate a key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener" class="text-indigo-600 hover:underline">platform.openai.com/api-keys</a>.</span>
        </div>
        <div class="flex items-start gap-2">
          <span class="font-medium text-gray-800 min-w-28">Anthropic:</span>
          <span>Create a key at <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener" class="text-indigo-600 hover:underline">console.anthropic.com</a>.</span>
        </div>
        <div class="flex items-start gap-2">
          <span class="font-medium text-gray-800 min-w-28">NVIDIA NIM:</span>
          <span>Create an API key at <a href="https://build.nvidia.com" target="_blank" rel="noopener" class="text-indigo-600 hover:underline">build.nvidia.com</a>. Runs NVIDIA's hosted openai/gpt-oss-20b model.</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()

const providers = [
  { value: 'gemini', name: 'Google Gemini', model: 'gemini-3.8-flash' },
  { value: 'openai', name: 'OpenAI', model: 'gpt-6-luna' },
  { value: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-5' },
  { value: 'nvidia_nim', name: 'NVIDIA NIM', model: 'OpenAI gpt-oss-20b · hosted NIM' }
]

const provider = ref('gemini')
const apiKey = ref('')
const showKey = ref(false)
const saving = ref(false)
const resetting = ref(false)
const testing = ref(false)
const connectionResult = ref(null)
const success = ref('')
const error = ref('')

const currentProvider = ref('gemini')
const hasKey = ref(false)
const isUsingPlatformDefault = ref(false)

const currentProviderName = computed(() => {
  const p = providers.find(item => item.value === currentProvider.value)
  return p ? p.name : (currentProvider.value || 'Google Gemini')
})

const keyPlaceholder = computed(() => {
  if (hasKey.value) return 'Enter a replacement provider key'
  if (provider.value === 'gemini') return 'AIza...'
  if (provider.value === 'openai') return 'sk-...'
  if (provider.value === 'anthropic') return 'sk-ant-...'
  if (provider.value === 'nvidia_nim') return 'nvapi-...'
  return 'Enter API key'
})

const keyHelp = computed(() => {
  if (provider.value === 'gemini') return 'Use an AI Studio authorization key. Google is rejecting standard Gemini keys from September 2026.'
  if (provider.value === 'openai') return 'Your OpenAI API key from platform.openai.com'
  if (provider.value === 'anthropic') return 'Your Anthropic API key from console.anthropic.com'
  if (provider.value === 'nvidia_nim') return 'Your NVIDIA API key from build.nvidia.com. Uses NVIDIA-hosted NIM inference.'
  return ''
})

async function loadSettings() {
  try {
    const bid = businessStore.currentBusiness?.id
    if (!bid) return

    const { data } = await api.get(`/ai-settings/${bid}`)
    currentProvider.value = data.llm_provider || 'gemini'
    hasKey.value = !!data.has_api_key
    isUsingPlatformDefault.value = !!data.is_using_platform_default
    if (data.llm_provider) {
      provider.value = data.llm_provider
    }
  } catch (err) {
    console.error('Failed to load AI settings', err)
  }
}

async function testConnection() {
  testing.value = true
  connectionResult.value = null
  error.value = ''
  try {
    const bid = businessStore.currentBusiness?.id
    if (!bid) throw new Error('No active business found')
    const payload = { provider: provider.value }
    if (apiKey.value.trim()) payload.api_key = apiKey.value.trim()
    const { data } = await api.post(`/ai-settings/${bid}/test-connection`, payload)
    connectionResult.value = data
  } catch (err) {
    connectionResult.value = {
      status: 'error',
      message: err.response?.data?.detail || err.message || 'Unable to test the LLM connection.',
      action_hint: 'Check the provider credentials and try again.',
    }
  } finally {
    testing.value = false
  }
}

async function save() {
  saving.value = true
  connectionResult.value = null
  success.value = ''
  error.value = ''
  try {
    const bid = businessStore.currentBusiness?.id
    if (!bid) throw new Error('No active business found')

    const { data } = await api.put(`/ai-settings/${bid}`, {
      llm_provider: provider.value,
      llm_api_key: apiKey.value.trim(),
    })

    currentProvider.value = data.llm_provider
    hasKey.value = !!data.has_api_key
    isUsingPlatformDefault.value = !!data.is_using_platform_default
    apiKey.value = ''
    showKey.value = false
    success.value = 'Settings saved successfully. Custom key is now active.'
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to save settings'
  } finally {
    saving.value = false
  }
}

async function resetToPlatformDefault() {
  resetting.value = true
  success.value = ''
  error.value = ''
  try {
    const bid = businessStore.currentBusiness?.id
    if (!bid) throw new Error('No active business found')

    const { data } = await api.put(`/ai-settings/${bid}`, {
      llm_provider: 'gemini',
      llm_api_key: '',
    })

    currentProvider.value = data.llm_provider || 'gemini'
    provider.value = data.llm_provider || 'gemini'
    hasKey.value = !!data.has_api_key
    isUsingPlatformDefault.value = !!data.is_using_platform_default
    apiKey.value = ''
    showKey.value = false
    success.value = 'Custom key removed. Successfully reverted to Platform Default (Gemini).'
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to reset settings'
  } finally {
    resetting.value = false
  }
}

watch([provider, apiKey], () => {
  connectionResult.value = null
})

watch(() => businessStore.currentBusiness?.id, (newId) => {
  if (newId) {
    loadSettings()
  }
})

onMounted(async () => {
  if (!businessStore.currentBusiness?.id) {
    await businessStore.fetchMyBusinesses()
  }
  await loadSettings()
})
</script>
