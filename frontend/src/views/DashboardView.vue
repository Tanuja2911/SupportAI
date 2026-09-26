<template>
  <div class="p-8">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>

    <div v-if="loading" class="text-gray-500">Loading stats...</div>

    <div v-else class="space-y-6">
      <!-- Getting Started Guide -->
      <div v-if="showGuide" class="bg-indigo-50 border border-indigo-200 rounded-xl p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-indigo-800">Getting Started</h3>
          <button @click="dismissGuide" class="text-sm text-indigo-500 hover:text-indigo-700">Dismiss</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white rounded-lg p-4 border border-indigo-100">
            <div class="flex items-center gap-2 mb-2">
              <span class="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">1</span>
              <h4 class="font-medium text-gray-800 text-sm">Upload Documents</h4>
            </div>
            <p class="text-xs text-gray-500">Go to <router-link to="/app/knowledge" class="text-indigo-600 underline">Knowledge Base</router-link> and upload PDFs, DOCX files, or add URLs. These become your AI agent's knowledge.</p>
          </div>
          <div class="bg-white rounded-lg p-4 border border-indigo-100">
            <div class="flex items-center gap-2 mb-2">
              <span class="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">2</span>
              <h4 class="font-medium text-gray-800 text-sm">Test Your Agent</h4>
            </div>
            <p class="text-xs text-gray-500">Once documents show "Ready", go to <router-link to="/app/sandbox" class="text-indigo-600 underline">Test Chat</router-link> and ask questions to see how your AI responds.</p>
          </div>
          <div class="bg-white rounded-lg p-4 border border-indigo-100">
            <div class="flex items-center gap-2 mb-2">
              <span class="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">3</span>
              <h4 class="font-medium text-gray-800 text-sm">Add FAQs</h4>
            </div>
            <p class="text-xs text-gray-500">Add common questions in <router-link to="/app/faq" class="text-indigo-600 underline">FAQ Overrides</router-link> for instant, exact answers that bypass the AI.</p>
          </div>
          <div class="bg-white rounded-lg p-4 border border-indigo-100">
            <div class="flex items-center gap-2 mb-2">
              <span class="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">4</span>
              <h4 class="font-medium text-gray-800 text-sm">Go Live</h4>
            </div>
            <p class="text-xs text-gray-500">Copy the embed code below and paste it into your website's HTML. Customize the look in <router-link to="/app/widget" class="text-indigo-600 underline">Widget Config</router-link>.</p>
          </div>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label" class="bg-white rounded-xl border border-gray-200 p-5">
          <p class="text-sm text-gray-500">{{ stat.label }}</p>
          <p class="text-2xl font-bold mt-1" :class="stat.color">{{ stat.value }}</p>
        </div>
      </div>

      <!-- API Key -->
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <h3 class="text-sm font-medium text-gray-700 mb-2">Your API Key</h3>
        <div class="flex items-center gap-3">
          <code class="flex-1 bg-gray-100 px-4 py-2 rounded-lg text-sm font-mono text-gray-600 truncate">
            {{ showKey ? businessStore.currentBusiness?.api_key : '************************************' }}
          </code>
          <button @click="showKey = !showKey" class="text-sm text-indigo-600 hover:underline whitespace-nowrap">
            {{ showKey ? 'Hide' : 'Show' }}
          </button>
          <button @click="copyKey" class="text-sm text-indigo-600 hover:underline whitespace-nowrap">
            Copy
          </button>
        </div>
      </div>

      <!-- Embed Code -->
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <div class="flex items-center justify-between gap-4 mb-2">
          <h3 class="text-sm font-medium text-gray-700">Add the chat widget to your website</h3>
          <button @click="copyEmbedCode" class="text-sm text-indigo-600 hover:underline whitespace-nowrap">
            Copy embed code
          </button>
        </div>
        <ol class="mb-4 list-decimal space-y-1 pl-5 text-sm text-gray-600">
          <li>Copy the code below.</li>
          <li>Paste it into your website HTML just before the closing <code>&lt;/body&gt;</code> tag. In a website builder, use its footer or custom-code area.</li>
          <li>Save and publish your website, then open it and try the chat bubble.</li>
        </ol>
        <pre class="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-x-auto">{{ embedCode }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const loading = ref(true)
const dashboard = ref(null)
const showKey = ref(false)
const showGuide = ref(localStorage.getItem('supportiq_guide_dismissed') !== 'true')

function dismissGuide() {
  showGuide.value = false
  localStorage.setItem('supportiq_guide_dismissed', 'true')
}

const stats = computed(() => {
  if (!dashboard.value) return []
  const d = dashboard.value
  return [
    { label: 'Total Conversations', value: d.total_conversations, color: 'text-gray-800' },
    { label: 'Active', value: d.active_conversations, color: 'text-green-600' },
    { label: 'Escalated', value: d.escalated_conversations, color: 'text-red-600' },
    { label: 'Avg Confidence', value: (d.avg_confidence * 100).toFixed(1) + '%', color: 'text-indigo-600' },
    { label: 'Total Messages', value: d.total_messages, color: 'text-gray-800' },
    { label: 'AI Responses', value: d.ai_messages, color: 'text-blue-600' },
    { label: 'Documents', value: d.total_documents, color: 'text-gray-800' },
    { label: 'Ready Docs', value: d.ready_documents, color: 'text-green-600' },
  ]
})

const embedCode = computed(() => {
  const key = businessStore.currentBusiness?.api_key || 'YOUR_API_KEY'
  return `<script src="${window.location.origin}/widget/widget.js"><\/script>
<script>
  SupportAI.init({ apiKey: '${key}' });
<\/script>`
})

function copyKey() {
  navigator.clipboard.writeText(businessStore.currentBusiness?.api_key || '')
}

function copyEmbedCode() {
  navigator.clipboard.writeText(embedCode.value)
}

onMounted(async () => {
  try {
    const bid = businessStore.currentBusiness?.id
    if (bid) {
      const { data } = await api.get(`/analytics/${bid}/dashboard`)
      dashboard.value = data
    }
  } catch (err) {
    console.error('Failed to load dashboard', err)
  } finally {
    loading.value = false
  }
})
</script>
