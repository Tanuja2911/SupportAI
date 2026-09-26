<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-7xl space-y-7">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">SupportAI workspace</p>
          <h2 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Dashboard</h2>
          <p class="mt-1 text-sm text-stone-500">See how your support assistant is doing and manage its setup.</p>
        </div>
        <router-link to="/app/sandbox" class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M8 10h8M8 14h5m-8 6 3.5-3H18a3 3 0 0 0 3-3V6a3 3 0 0 0-3-3H6a3 3 0 0 0-3 3v14Z"/></svg>
          Test your assistant
        </router-link>
      </header>

      <div v-if="loading" class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Loading dashboard" aria-live="polite">
        <div v-for="n in 8" :key="n" class="h-28 animate-pulse rounded-2xl border border-stone-200 bg-white"></div>
      </div>

      <div v-else class="space-y-7">
        <section v-if="showGuide" class="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <div class="flex flex-col gap-3 border-b border-blue-100 bg-gradient-to-r from-blue-50 via-white to-blue-50 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">Quick setup</p>
              <h3 class="mt-1 text-lg font-bold text-stone-900">Get your assistant ready</h3>
            </div>
            <button @click="dismissGuide" class="self-start rounded-lg px-3 py-2 text-sm font-medium text-stone-500 transition hover:bg-white hover:text-stone-800 sm:self-auto">Dismiss</button>
          </div>
          <div class="grid grid-cols-1 gap-px bg-stone-100 sm:grid-cols-2 xl:grid-cols-4">
            <div v-for="step in guideSteps" :key="step.number" class="bg-white p-5">
              <div class="flex items-center gap-3">
                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-sm font-bold text-blue-700">{{ step.number }}</span>
                <h4 class="text-sm font-semibold text-stone-900">{{ step.title }}</h4>
              </div>
              <p class="mt-3 text-sm leading-6 text-stone-500">{{ step.before }}<router-link :to="step.to" class="font-medium text-blue-600 hover:text-blue-800">{{ step.link }}</router-link>{{ step.after }}</p>
            </div>
          </div>
        </section>

        <section aria-label="Support activity">
          <div class="mb-3"><h3 class="text-sm font-semibold text-stone-800">Key metrics</h3></div>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <article v-for="stat in stats.slice(0, 4)" :key="stat.label" class="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-sm font-medium text-stone-500">{{ stat.label }}</p>
                  <p class="mt-3 text-3xl font-bold tracking-tight text-stone-900">{{ stat.value }}</p>
                </div>
                <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true">
                    <path v-if="stat.icon === 'chat'" stroke-linecap="round" stroke-linejoin="round" d="M7 8h10M7 12h6m-9 8 3.2-3H18a3 3 0 0 0 3-3V6a3 3 0 0 0-3-3H6a3 3 0 0 0-3 3v14Z" />
                    <path v-else-if="stat.icon === 'alert'" stroke-linecap="round" stroke-linejoin="round" d="M12 9v3m0 4h.01M10.3 4.5 2.9 17.3A1.8 1.8 0 0 0 4.5 20h15a1.8 1.8 0 0 0 1.6-2.7L13.7 4.5a2 2 0 0 0-3.4 0Z" />
                    <path v-else-if="stat.icon === 'confidence'" stroke-linecap="round" stroke-linejoin="round" d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z" />
                    <path v-else-if="stat.icon === 'message'" stroke-linecap="round" stroke-linejoin="round" d="M7 8h10M7 12h10m-9 8-4 1 1-4V6a3 3 0 0 1 3-3h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H8Z" />
                    <path v-else-if="stat.icon === 'sparkle'" stroke-linecap="round" stroke-linejoin="round" d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Zm7 12 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z" />
                    <path v-else-if="stat.icon === 'document'" stroke-linecap="round" stroke-linejoin="round" d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm7 0v5h5M9 13h6m-6 4h6" />
                    <path v-else-if="stat.icon === 'ready'" stroke-linecap="round" stroke-linejoin="round" d="m5 12 4 4L19 6" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" d="M7 7h10v14H7zM9 3h6v4H9zM10 12h4m-4 4h4" />
                  </svg>
                </span>
              </div>
            </article>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-3 rounded-2xl border border-stone-200 bg-white px-4 py-3 sm:grid-cols-4">
            <div v-for="stat in stats.slice(4)" :key="stat.label" class="flex items-center justify-between gap-2 px-1 py-1 sm:px-3">
              <span class="text-xs font-medium text-stone-500 sm:text-sm">{{ stat.label }}</span>
              <span class="text-base font-semibold text-stone-800">{{ stat.value }}</span>
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 gap-5 xl:grid-cols-5">
          <article class="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-6 xl:col-span-2">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Business connection</p>
                <h3 class="mt-1 text-lg font-bold text-stone-900">Your API key</h3>
              </div>
              <span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">Widget ID</span>
            </div>
            <p class="mt-2 text-sm leading-6 text-stone-500">Identifies which business your website’s SupportAI widget connects to.</p>
            <div class="mt-4 flex min-w-0 items-center gap-2 rounded-xl border border-stone-200 bg-blue-50 p-2">
              <code class="min-w-0 flex-1 truncate px-2 text-xs text-stone-600 sm:text-sm">{{ showKey ? businessStore.currentBusiness?.api_key : '••••••••••••••••••••••••••••••••' }}</code>
              <button @click="showKey = !showKey" class="rounded-lg px-2.5 py-2 text-xs font-semibold text-stone-600 transition hover:bg-white hover:text-blue-700">{{ showKey ? 'Hide' : 'Show' }}</button>
              <button @click="copyKey" class="rounded-lg bg-white px-3 py-2 text-xs font-semibold text-blue-700 shadow-sm ring-1 ring-stone-200 transition hover:bg-blue-50">{{ copiedKey ? 'Copied' : 'Copy' }}</button>
            </div>
          </article>

          <article class="min-w-0 rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-6 xl:col-span-3">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.14em] text-stone-400">Installation</p>
                <h3 class="mt-1 text-lg font-bold text-stone-900">Add the chat widget to your website</h3>
              </div>
              <button @click="copyEmbedCode" class="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-3.5 py-2.5 text-sm font-semibold text-blue-700 transition hover:bg-blue-100">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2"/><path stroke-linecap="round" stroke-linejoin="round" d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></svg>
                {{ copiedEmbed ? 'Copied!' : 'Copy embed code' }}
              </button>
            </div>
            <ol class="mt-4 grid grid-cols-1 gap-2 text-sm text-stone-600 sm:grid-cols-3">
              <li class="flex gap-2"><span class="font-bold text-blue-600">1.</span><span>Copy the code below.</span></li>
              <li class="flex gap-2"><span class="font-bold text-blue-600">2.</span><span>Paste before <code class="rounded bg-stone-100 px-1 py-0.5 text-xs">&lt;/body&gt;</code> or into your site builder’s custom code area.</span></li>
              <li class="flex gap-2"><span class="font-bold text-blue-600">3.</span><span>Publish your site and try the chat bubble.</span></li>
            </ol>
            <pre class="mt-4 max-h-44 overflow-auto rounded-xl bg-stone-950 p-4 text-xs leading-6 text-blue-300"><code>{{ embedCode }}</code></pre>
          </article>
        </section>
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
  const key = businessStore.currentBusiness?.api_key || 'YOUR_API_KEY'
  return `<script src="${window.location.origin}/widget/widget.js"><\/script>\n<script>\n  SupportAI.init({\n    apiKey: '${key}',\n    serverUrl: '${window.location.origin}'\n  });\n<\/script>`
})

async function copyKey() {
  await navigator.clipboard.writeText(businessStore.currentBusiness?.api_key || '')
  copiedKey.value = true
  clearTimeout(copiedKeyTimeout)
  copiedKeyTimeout = setTimeout(() => { copiedKey.value = false }, 1800)
}

async function copyEmbedCode() {
  await navigator.clipboard.writeText(embedCode.value)
  copiedEmbed.value = true
  clearTimeout(copiedEmbedTimeout)
  copiedEmbedTimeout = setTimeout(() => { copiedEmbed.value = false }, 1800)
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
