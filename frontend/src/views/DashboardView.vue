<template>
  <div class="dashboard-page">
    <section class="dashboard-intro">
      <div>
        <p class="dashboard-kicker">LIVE OPERATIONS</p>
        <h2>Support, at a glance.</h2>
        <p>One clear view of your AI agent, its knowledge, and every customer conversation.</p>
      </div>
      <div class="dashboard-intro-actions">
        <router-link to="/app/sandbox" class="dashboard-secondary-action">Open playground <span aria-hidden="true">↗</span></router-link>
        <router-link to="/app/widget" class="dashboard-primary-action">Configure widget <span aria-hidden="true">→</span></router-link>
      </div>
      <div class="dashboard-orb" aria-hidden="true"></div>
    </section>

    <div v-if="loading" class="dashboard-loading">Loading your support metrics…</div>

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
            <p class="text-xs text-gray-500">Copy the 1-line embed script below and paste it into your website. Configure allowed domains in <router-link to="/app/widget" class="text-indigo-600 underline">Widget Config</router-link>.</p>
          </div>
        </div>
        <router-link to="/app/sandbox" class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M8 10h8M8 14h5m-8 6 3.5-3H18a3 3 0 0 0 3-3V6a3 3 0 0 0-3-3H6a3 3 0 0 0-3 3v14Z"/></svg>
          Test your assistant
        </router-link>
      </header>

      <div v-if="loading" class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Loading dashboard" aria-live="polite">
        <div v-for="n in 8" :key="n" class="h-28 animate-pulse rounded-2xl border border-stone-200 bg-white"></div>
      </div>

      <!-- Stats Grid -->
      <section class="dashboard-metrics" aria-label="Support metrics">
        <div v-for="(stat, index) in stats" :key="stat.label" class="dashboard-stat bg-white rounded-xl border border-gray-200 p-5" :style="{ '--stat-index': index }">
          <div class="dashboard-stat-heading">
            <span class="dashboard-stat-dot" :class="stat.color"></span>
            <p>{{ stat.label }}</p>
            <span class="dashboard-stat-index">{{ String(index + 1).padStart(2, '0') }}</span>
          </div>
          <p class="dashboard-stat-value" :class="stat.color">{{ stat.value }}</p>
          <div class="dashboard-stat-footer"><span>WORKSPACE METRIC</span><span aria-hidden="true">↗</span></div>
        </div>
      </section>

      <!-- Business Credentials: Public Key vs Secret API Key -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Public Key (Client-Safe) -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-sm font-semibold text-gray-800">Public Key (Widget Token)</h3>
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                Public / Safe for Web
              </span>
            </div>
            <p class="mb-3 text-xs text-gray-500">
              Safe client-facing key for your website's chat widget embed script. Cannot be used to access private APIs or modify settings.
            </p>
          </div>
          <div class="flex items-center gap-3">
            <code class="flex-1 bg-gray-50 px-3 py-2 rounded-lg text-xs font-mono text-gray-700 truncate border border-gray-200">
              {{ businessStore.currentBusiness?.public_key || 'Loading public key...' }}
            </code>
            <button
              @click="copyPublicKey"
              class="px-3 py-1.5 text-xs font-medium rounded-md transition whitespace-nowrap"
              :class="copiedPublicKey ? 'bg-green-600 text-white font-semibold' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              {{ copiedPublicKey ? 'Copied!' : 'Copy' }}
            </button>
          </div>
        </div>

        <!-- Secret API Key (Confidential) -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-sm font-semibold text-gray-800">Secret API Key</h3>
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                Confidential / Secret
              </span>
            </div>
            <p class="mb-3 text-xs text-gray-500">
              Administrative secret for backend server-to-server API integrations. Never expose this key in public client-side JavaScript or HTML.
            </p>
          </div>
          <div class="flex items-center gap-3">
            <code class="flex-1 bg-gray-50 px-3 py-2 rounded-lg text-xs font-mono text-gray-700 truncate border border-gray-200">
              {{ showSecretKey ? (businessStore.currentBusiness?.api_key || 'Loading secret key...') : '••••••••••••••••••••••••••••••••' }}
            </code>
            <button
              @click="showSecretKey = !showSecretKey"
              class="text-xs text-gray-500 hover:text-gray-700 whitespace-nowrap"
            >
              {{ showSecretKey ? 'Hide' : 'Show' }}
            </button>
            <button
              @click="copySecretKey"
              class="px-3 py-1.5 text-xs font-medium rounded-md transition whitespace-nowrap"
              :class="copiedSecretKey ? 'bg-green-600 text-white font-semibold' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              {{ copiedSecretKey ? 'Copied!' : 'Copy' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Pure 1-Line Embed Code -->
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <div class="flex items-center justify-between gap-4 mb-2">
          <div>
            <h3 class="text-sm font-semibold text-gray-800">Add the chat widget to your website</h3>
            <p class="text-xs text-gray-500 mt-0.5">Single self-initializing script tag with automatic origin detection.</p>
          </div>
          <button
            @click="copyEmbedCode"
            class="px-3 py-1.5 text-xs font-medium rounded-md transition whitespace-nowrap flex items-center gap-1.5"
            :class="copiedEmbed ? 'bg-green-600 text-white font-semibold' : 'bg-indigo-600 text-white hover:bg-indigo-700'"
          >
            <span v-if="copiedEmbed">✓ Copied!</span>
            <span v-else>Copy embed code</span>
          </button>
        </div>
        <ol class="mb-4 list-decimal space-y-1 pl-5 text-xs text-gray-600">
          <li>Copy the 1-line script tag below.</li>
          <li>Paste it into your website HTML just before the closing <code>&lt;/body&gt;</code> tag (or inside the header).</li>
          <li>Save and publish your site. The widget automatically initializes without secondary scripts.</li>
        </ol>
        <div class="relative">
          <pre class="bg-gray-900 text-green-400 p-4 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all select-all">{{ embedCode }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const loading = ref(true)
const dashboard = ref(null)
const showSecretKey = ref(false)
const copiedPublicKey = ref(false)
const copiedSecretKey = ref(false)
const copiedEmbed = ref(false)
const showGuide = ref(localStorage.getItem('supportiq_guide_dismissed') !== 'true')
const copiedKey = ref(false)
const copiedEmbed = ref(false)
let copiedKeyTimeout
let copiedEmbedTimeout

const guideSteps = [
  { number: '01', title: 'Add knowledge', before: 'Upload PDFs, DOCX files, or URLs in ', link: 'Knowledge Base', to: '/app/knowledge', after: ' so the assistant can answer from your content.' },
  { number: '02', title: 'Try a question', before: 'Use ', link: 'Test Chat', to: '/app/sandbox', after: ' to check answers from your assistant.' },
  { number: '03', title: 'Add quick answers', before: 'Set up common questions in ', link: 'FAQ Overrides', to: '/app/faq', after: ' for exact responses.' },
  { number: '04', title: 'Add it to your site', before: 'Copy the widget code below. Change its appearance in ', link: 'Widget Config', to: '/app/widget', after: '.' },
]

let pubKeyTimer = null
let secKeyTimer = null
let embedTimer = null

onUnmounted(() => {
  if (pubKeyTimer) clearTimeout(pubKeyTimer)
  if (secKeyTimer) clearTimeout(secKeyTimer)
  if (embedTimer) clearTimeout(embedTimer)
})

function dismissGuide() {
  showGuide.value = false
  localStorage.setItem('supportiq_guide_dismissed', 'true')
}

const stats = computed(() => {
  if (!dashboard.value) return []
  const d = dashboard.value
  return [
    { label: 'Total conversations', value: d.total_conversations, icon: 'chat' },
    { label: 'Active conversations', value: d.active_conversations, icon: 'sparkle' },
    { label: 'Escalated', value: d.escalated_conversations, icon: 'alert' },
    { label: 'Average confidence', value: (d.avg_confidence * 100).toFixed(1) + '%', icon: 'confidence' },
    { label: 'Total messages', value: d.total_messages },
    { label: 'AI responses', value: d.ai_messages },
    { label: 'Knowledge documents', value: d.total_documents },
    { label: 'Ready documents', value: d.ready_documents },
  ]
})

const embedCode = computed(() => {
  let backendOrigin = (typeof window !== 'undefined' ? window.location.origin : '').replace(/\/+$/, '')
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    backendOrigin = `${window.location.protocol}//${window.location.hostname}:8000`
  }
  const key = businessStore.currentBusiness?.public_key || 'YOUR_PUBLIC_KEY'
  return `<script src="${backendOrigin}/widget/widget.js" data-business-key="${key}" defer><\/script>`
})

function copyPublicKey() {
  const key = businessStore.currentBusiness?.public_key || ''
  if (!key) return
  navigator.clipboard.writeText(key)
  copiedPublicKey.value = true
  if (pubKeyTimer) clearTimeout(pubKeyTimer)
  pubKeyTimer = setTimeout(() => {
    copiedPublicKey.value = false
  }, 2000)
}

function copySecretKey() {
  const key = businessStore.currentBusiness?.api_key || ''
  if (!key) return
  navigator.clipboard.writeText(key)
  copiedSecretKey.value = true
  if (secKeyTimer) clearTimeout(secKeyTimer)
  secKeyTimer = setTimeout(() => {
    copiedSecretKey.value = false
  }, 2000)
}

function copyEmbedCode() {
  navigator.clipboard.writeText(embedCode.value)
  copiedEmbed.value = true
  if (embedTimer) clearTimeout(embedTimer)
  embedTimer = setTimeout(() => {
    copiedEmbed.value = false
  }, 2000)
}

onMounted(async () => {
  try {
    if (!businessStore.currentBusiness?.public_key) {
      await businessStore.fetchMyBusinesses()
    }
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
