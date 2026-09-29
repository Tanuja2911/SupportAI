<template>
  <div class="p-8 max-w-5xl">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Widget Configuration</h2>
      <p class="text-sm text-gray-500 mt-1">Customize your chat widget's appearance, domain security whitelist, and embed snippet.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-2"></div>
      <p class="text-sm">Loading widget configuration...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
      <div class="flex items-center justify-between">
        <div>
          <p class="font-medium">Failed to load configuration</p>
          <p class="text-sm mt-1">{{ loadError }}</p>
        </div>
        <button @click="loadConfig" class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition">
          Retry
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else-if="config" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Form & Security Controls -->
      <div class="lg:col-span-2 space-y-6">

        <!-- 1. Security & Allowed Domains Card -->
        <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
          <div class="flex items-center justify-between border-b border-gray-100 pb-3">
            <div>
              <h3 class="text-base font-semibold text-gray-900">Domain Whitelisting & Origin Security</h3>
              <p class="text-xs text-gray-500 mt-0.5">Control which websites are authorized to embed and run your AI chat widget.</p>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
              Origin Guard
            </span>
          </div>

          <!-- Localhost / Dev Mode Toggle -->
          <div class="flex items-start justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
            <div class="pr-4">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900">Localhost / Dev Mode</span>
                <span
                  :class="config.allow_localhost ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium transition"
                >
                  {{ config.allow_localhost ? 'Active' : 'Disabled' }}
                </span>
              </div>
              <p class="text-xs text-gray-500 mt-1">
                Allow widget requests from localhost and 127.0.0.1 for local testing.
              </p>
              <p class="text-xs text-gray-400 mt-0.5">
                Disable in production to strictly reject all unlisted development origins.
              </p>
            </div>
            <button
              type="button"
              @click="config.allow_localhost = !config.allow_localhost"
              :class="config.allow_localhost ? 'bg-indigo-600' : 'bg-gray-300'"
              class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              role="switch"
              :aria-checked="config.allow_localhost"
            >
              <span
                aria-hidden="true"
                :class="config.allow_localhost ? 'translate-x-5' : 'translate-x-0'"
                class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
              />
            </button>
          </div>

          <!-- Allowed Domains Management -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Whitelisted Domains
              <span class="text-xs text-gray-400 font-normal">({{ config.allowed_domains.length }} configured)</span>
            </label>
            <p class="text-xs text-gray-500 mb-3">
              Requests with Origin or Referer matching these domains will be accepted. Root domains automatically permit subdomains (e.g. <code class="text-indigo-600">example.com</code> permits <code class="text-indigo-600">shop.example.com</code>).
            </p>

            <!-- Add Domain Input -->
            <div class="flex gap-2">
              <input
                v-model="domainInput"
                @keydown.enter.prevent="addDomain"
                type="text"
                placeholder="e.g. example.com or app.mysite.com"
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
              />
              <button
                type="button"
                @click="addDomain"
                :disabled="!domainInput.trim()"
                class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50"
              >
                Add Domain
              </button>
            </div>
            <p v-if="domainError" class="text-xs text-red-600 mt-1">{{ domainError }}</p>

            <!-- Domain Chips Container -->
            <div class="mt-3">
              <div v-if="config.allowed_domains.length > 0" class="flex flex-wrap gap-2">
                <span
                  v-for="(domain, idx) in config.allowed_domains"
                  :key="domain"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-medium bg-indigo-50 text-indigo-700 border border-indigo-200"
                >
                  <svg class="w-3.5 h-3.5 text-indigo-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                  <span>{{ domain }}</span>
                  <button
                    type="button"
                    @click="removeDomain(idx)"
                    class="text-indigo-400 hover:text-indigo-700 hover:bg-indigo-200 rounded-full p-0.5 transition"
                    title="Remove domain"
                  >
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              </div>
              <div v-else-if="!config.allow_localhost" class="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800">
                <span class="font-semibold">Warning:</span> No domains are whitelisted and Localhost / Dev Mode is disabled. All external embed and chat requests will be rejected with HTTP 403 Forbidden.
              </div>
              <div v-else class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                No production domains whitelisted yet. External websites will receive HTTP 403 Forbidden unless Localhost / Dev Mode is active.
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Pure 1-Line Embed Code Card -->
        <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div class="flex items-center justify-between border-b border-gray-100 pb-3">
            <div>
              <h3 class="text-base font-semibold text-gray-900">1-Line Embed Code</h3>
              <p class="text-xs text-gray-500 mt-0.5">Copy and paste this single script tag into your website's HTML before the closing <code class="text-gray-700">&lt;/body&gt;</code> tag.</p>
            </div>
            <button
              type="button"
              @click="copyEmbedSnippet"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 border border-indigo-600 text-indigo-600 rounded-lg text-xs font-medium hover:bg-indigo-50 transition"
            >
              <svg v-if="!copied" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
              </svg>
              <svg v-else class="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span :class="copied ? 'text-green-600 font-semibold' : ''">{{ copied ? 'Copied!' : 'Copy Script' }}</span>
            </button>
          </div>

          <pre class="bg-gray-900 text-green-400 p-4 rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap break-all select-all">{{ embedSnippet }}</pre>

          <div class="flex items-center gap-2 text-xs text-gray-500">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100 text-gray-700 font-mono">
              Public Key (Safe to expose)
            </span>
            <span>Self-initializes automatically using origin inference. No secondary config script required.</span>
          </div>
        </div>

        <!-- 3. Widget Appearance Card -->
        <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div class="border-b border-gray-100 pb-3">
            <h3 class="text-base font-semibold text-gray-900">Appearance & Behavior</h3>
            <p class="text-xs text-gray-500 mt-0.5">Customize how the chat widget looks and feels to your visitors.</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Bot Name</label>
            <input
              v-model="config.bot_name"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Welcome Message</label>
            <textarea
              v-model="config.welcome_message"
              rows="2"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 text-sm resize-none"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
            <div class="flex items-center gap-3">
              <input v-model="config.primary_color" type="color" class="w-10 h-10 rounded cursor-pointer border border-gray-300" />
              <input v-model="config.primary_color" class="px-4 py-2 border border-gray-300 rounded-lg outline-none w-32 text-sm font-mono" />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Position</label>
            <select v-model="config.position" class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none text-sm bg-white">
              <option value="bottom-right">Bottom Right</option>
              <option value="bottom-left">Bottom Left</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Placeholder Text</label>
            <input
              v-model="config.placeholder_text"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Auto Open Delay</label>
            <input
              v-model="config.auto_open_delay"
              type="text"
              inputmode="decimal"
              placeholder="e.g. 5s or leave empty to disable"
              aria-describedby="auto-open-help"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
            <p id="auto-open-help" class="mt-1 text-xs text-gray-500">Opens the chat automatically after the visitor arrives. Use seconds (for example, 5s) or leave empty to disable.</p>
          </div>

          <div class="flex items-center gap-2 pt-1">
            <input type="checkbox" v-model="config.show_branding" id="branding" class="rounded text-indigo-600 focus:ring-indigo-500" />
            <label for="branding" class="text-sm text-gray-700 select-none">Show SupportAI branding badge</label>
          </div>
        </div>

        <!-- Save Button & Feedback -->
        <div class="space-y-3 pt-2">
          <div v-if="saveSuccess" class="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-center gap-2">
            <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Widget configuration saved successfully!
          </div>

          <div v-if="saveError" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {{ saveError }}
          </div>

          <button
            @click="saveConfig"
            :disabled="saving"
            class="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
          >
            <span v-if="saving" class="inline-block animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
            {{ saving ? 'Saving Changes...' : 'Save Configuration' }}
          </button>
        </div>
      </div>

      <!-- Right Column: Live Appearance Preview -->
      <div class="lg:col-span-1">
        <div class="sticky top-8 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="mb-4 flex items-center justify-between border-b border-gray-100 pb-3">
            <div>
              <h3 class="text-sm font-semibold text-gray-800">Live widget simulator</h3>
              <p class="mt-0.5 text-[11px] text-gray-500">Updates as you edit · no save required</p>
            </div>
            <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-medium text-emerald-700"><span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>Live</span>
          </div>

          <div class="widget-preview-stage relative min-h-[390px] overflow-hidden rounded-xl border border-gray-200 p-4">
            <div class="mb-5 flex items-center gap-1.5" aria-hidden="true">
              <span class="h-2 w-2 rounded-full bg-red-400"></span><span class="h-2 w-2 rounded-full bg-amber-400"></span><span class="h-2 w-2 rounded-full bg-emerald-400"></span>
              <span class="ml-2 h-5 flex-1 rounded-md border border-gray-200 bg-white/70"></span>
            </div>
            <div class="space-y-3 opacity-70" aria-hidden="true">
              <div class="h-3 w-2/5 rounded bg-gray-200"></div>
              <div class="h-2 w-full rounded bg-gray-200"></div>
              <div class="h-2 w-4/5 rounded bg-gray-200"></div>
              <div class="mt-5 grid grid-cols-2 gap-2"><div class="h-16 rounded-lg border border-gray-200 bg-white/70"></div><div class="h-16 rounded-lg border border-gray-200 bg-white/70"></div></div>
            </div>

            <div v-if="previewOpen" class="absolute bottom-[76px] w-[calc(100%-32px)] overflow-hidden rounded-2xl border border-gray-200 shadow-2xl" :class="config.position === 'bottom-left' ? 'left-4' : 'right-4'">
              <div class="flex items-center justify-between p-3.5 text-white" :style="{ backgroundColor: config.primary_color }">
                <div class="flex items-center gap-2.5">
                  <span class="flex h-8 w-8 items-center justify-center rounded-full bg-white/20 text-sm font-semibold">{{ (config.bot_name || 'S').charAt(0).toUpperCase() }}</span>
                  <div><div class="text-xs font-semibold">{{ config.bot_name || 'Support Assistant' }}</div><div class="mt-0.5 flex items-center gap-1.5 text-[10px] opacity-80"><span class="h-1.5 w-1.5 rounded-full bg-emerald-300"></span>Active now</div></div>
                </div>
                <button type="button" @click="previewOpen = false" aria-label="Minimize widget preview" class="rounded-md p-1 text-white/80 transition hover:bg-white/15 hover:text-white">−</button>
              </div>
              <div class="flex min-h-[190px] flex-col justify-between bg-gray-50 p-3.5">
                <div class="max-w-[88%] rounded-xl rounded-tl-sm border border-gray-200 bg-white px-3 py-2.5 text-xs leading-relaxed text-gray-800 shadow-sm">{{ config.welcome_message || 'Hi! How can I help you today?' }}</div>
                <div v-if="config.show_branding" class="pt-3 text-center text-[10px] text-gray-400">Powered by SupportAI</div>
              </div>
              <div class="border-t border-gray-200 bg-white p-2.5"><div class="flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-2 text-[11px] text-gray-500"><span class="min-w-0 flex-1 truncate">{{ config.placeholder_text || 'Type your question...' }}</span><span class="flex h-6 w-6 items-center justify-center rounded-full text-white" :style="{ backgroundColor: config.primary_color }">↑</span></div></div>
            </div>

            <button v-else type="button" @click="previewOpen = true" aria-label="Open widget preview" class="absolute bottom-4 flex h-12 w-12 items-center justify-center rounded-full text-white shadow-xl transition hover:scale-105" :class="config.position === 'bottom-left' ? 'left-4' : 'right-4'" :style="{ backgroundColor: config.primary_color }">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M8 10h8M8 14h5m-9 7 1.6-4.3A8.5 8.5 0 1 1 12 20.5c-1.3 0-2.5-.3-3.6-.8L4 21Z" /></svg>
            </button>
          </div>

          <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
            <span>Launcher position</span>
            <span class="font-medium text-gray-700">{{ config.position === 'bottom-left' ? 'Bottom left' : 'Bottom right' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const config = ref(null)
const previewOpen = ref(true)
const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const saveSuccess = ref(false)
const saveError = ref('')
const domainInput = ref('')
const domainError = ref('')
const copied = ref(false)
let copyTimer = null

onUnmounted(() => {
  if (copyTimer) clearTimeout(copyTimer)
})

// 1. Safe business ID and credentials resolution
const business = computed(() => businessStore.currentBusiness)
const businessId = computed(() => business.value?.id)
const businessKey = computed(() => business.value?.public_key || business.value?.api_key || 'YOUR_BUSINESS_KEY')

// 2. Pure 1-Line Embed Snippet computation
const embedSnippet = computed(() => {
  let origin = (typeof window !== 'undefined' ? window.location.origin : '').replace(/\/+$/, '')
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    origin = `${window.location.protocol}//${window.location.hostname}:8000`
  }
  return `<script src="${origin}/widget/widget.js" data-business-key="${businessKey.value}" defer><\/script>`
})

// 3. Domain Normalization / Sanitization Function (matches origin_guard.clean_domain_entry)
function sanitizeDomain(input) {
  if (!input || typeof input !== 'string') return ''
  let d = input.trim().toLowerCase()
  if (!d) return ''
  if (d === '::1') return d

  if (d.includes('://')) {
    d = d.split('://')[1]
  }

  for (const sep of ['/', '?', '#']) {
    if (d.includes(sep)) {
      d = d.split(sep)[0]
    }
  }

  if (d.includes('@')) {
    d = d.split('@').pop()
  }

  if (d.startsWith('[') && d.includes(']')) {
    const closing = d.indexOf(']')
    d = d.substring(1, closing)
  } else if (d.includes(':')) {
    d = d.split(':')[0]
  }

  d = d.replace(/^\*\.?/, '').replace(/^\.+/, '')
  d = d.replace(/\.+$/, '')
  return d
}

// 4. Hostname validation
function isValidDomain(domain) {
  if (!domain) return false
  if (domain === 'localhost' || domain === '::1') return true
  const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/
  if (ipv4Pattern.test(domain)) {
    const parts = domain.split('.').map(Number)
    return parts.every(p => p >= 0 && p <= 255)
  }
  const domainPattern = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/
  return domainPattern.test(domain)
}

// 5. Add Domain Handler
function addDomain() {
  domainError.value = ''
  const clean = sanitizeDomain(domainInput.value)

  if (!clean) {
    domainError.value = 'Please enter a valid domain (e.g. example.com or app.mysite.com).'
    return
  }

  if (!isValidDomain(clean)) {
    domainError.value = `"${clean}" does not appear to be a valid domain or IP address.`
    return
  }

  if (!Array.isArray(config.value.allowed_domains)) {
    config.value.allowed_domains = []
  }

  if (config.value.allowed_domains.includes(clean)) {
    domainError.value = `Domain "${clean}" is already in the allowed list.`
    return
  }

  config.value.allowed_domains.push(clean)
  domainInput.value = ''
}

// 6. Remove Domain Handler
function removeDomain(index) {
  if (Array.isArray(config.value.allowed_domains)) {
    config.value.allowed_domains.splice(index, 1)
  }
}

// 7. 1-Click Copy Handler
async function copyEmbedSnippet() {
  try {
    await navigator.clipboard.writeText(embedSnippet.value)
    copied.value = true
    if (copyTimer) clearTimeout(copyTimer)
    copyTimer = setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy to clipboard', err)
  }
}

// 8. Load Config with resilient business fetching
async function loadConfig() {
  loading.value = true
  loadError.value = ''
  saveError.value = ''

  try {
    let bid = businessStore.currentBusiness?.id
    if (!bid) {
      await businessStore.fetchMyBusinesses()
      bid = businessStore.currentBusiness?.id
    }

    if (!bid) {
      loadError.value = 'No business found. Please create or select a business.'
      return
    }

    const { data } = await api.get(`/widget/${bid}/config`)
    config.value = {
      ...data,
      allowed_domains: Array.isArray(data.allowed_domains) ? data.allowed_domains : [],
      allow_localhost: typeof data.allow_localhost === 'boolean' ? data.allow_localhost : true,
    }
  } catch (err) {
    loadError.value = err.response?.data?.detail || 'Failed to load widget configuration.'
  } finally {
    loading.value = false
  }
}

// 9. Save Config Handler
async function saveConfig() {
  if (!config.value) return
  saving.value = true
  saveSuccess.value = false
  saveError.value = ''

  try {
    let bid = businessStore.currentBusiness?.id
    if (!bid) {
      throw new Error('Business ID not found.')
    }

    const payload = {
      bot_name: config.value.bot_name,
      welcome_message: config.value.welcome_message,
      primary_color: config.value.primary_color,
      position: config.value.position,
      show_branding: config.value.show_branding,
      placeholder_text: config.value.placeholder_text,
      auto_open_delay: config.value.auto_open_delay || null,
      allowed_domains: config.value.allowed_domains || [],
      allow_localhost: !!config.value.allow_localhost,
    }

    const { data } = await api.put(`/widget/${bid}/config`, payload)
    config.value = {
      ...config.value,
      ...data,
      allowed_domains: Array.isArray(data.allowed_domains) ? data.allowed_domains : [],
      allow_localhost: typeof data.allow_localhost === 'boolean' ? data.allow_localhost : true,
    }
    saveSuccess.value = true
    setTimeout(() => {
      saveSuccess.value = false
    }, 4000)
  } catch (err) {
    saveError.value = err.response?.data?.detail || err.message || 'Failed to save configuration.'
  } finally {
    saving.value = false
  }
}

// Re-fetch when active business switches
watch(() => businessStore.currentBusiness?.id, (newId) => {
  if (newId) {
    loadConfig()
  }
})

onMounted(loadConfig)
</script>
