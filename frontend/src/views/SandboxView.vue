<template>
  <section class="sandbox-page">
    <header class="sandbox-heading">
      <div>
        <p class="sandbox-kicker">PLAYGROUND</p>
        <h2 class="text-2xl font-bold text-gray-800">Test your support agent</h2>
        <p class="text-gray-500 text-sm mt-1">Ask a question from your knowledge base and inspect the answer and sources.</p>
      </div>
      <button
        type="button"
        @click="newChat"
        :disabled="thinking"
        class="sandbox-secondary-button"
      >
        New conversation
      </button>
    </header>

    <div v-if="pageError" class="sandbox-alert sandbox-alert-error" role="alert">
      {{ pageError }}
      <button type="button" @click="initialize" :disabled="loadingBusiness">Try again</button>
    </div>

    <div class="sandbox-card">
      <div ref="chatContainer" class="sandbox-messages" aria-live="polite" aria-relevant="additions text">
        <div v-if="messages.length === 0" class="sandbox-empty">
          <span class="sandbox-empty-icon" aria-hidden="true">✳</span>
          <h3>Start a test conversation</h3>
          <p>Try a substantive question covered by your processed documents.</p>
        </div>

        <article
          v-for="(msg, i) in messages"
          :key="i"
          class="sandbox-message-row"
          :class="msg.role === 'user' ? 'is-user' : 'is-agent'"
        >
          <div class="sandbox-message" :class="msg.role === 'user' ? 'sandbox-message-user' : 'sandbox-message-agent'">
            <p class="sandbox-message-label">{{ msg.role === 'user' ? 'You' : 'Support agent' }}</p>
            <p class="whitespace-pre-wrap">{{ msg.content }}</p>
            <div v-if="msg.role === 'ai' && (msg.errorCode || msg.diagnostic || msg.actionHint)" class="sandbox-diagnostic" role="status">
              <p v-if="msg.errorCode" class="font-semibold">{{ formatErrorCode(msg.errorCode) }}</p>
              <p v-if="msg.diagnostic">{{ msg.diagnostic }}</p>
              <p v-if="msg.actionHint" class="sandbox-action-hint">{{ msg.actionHint }}</p>
            </div>
            <div v-if="msg.role === 'ai' && msg.confidence !== null && msg.confidence !== undefined" class="sandbox-meta">
              Confidence {{ (msg.confidence * 100).toFixed(0) }}%
            </div>
            <details v-if="msg.sources?.length" class="sandbox-sources">
              <summary>{{ msg.sources.length }} {{ msg.sources.length === 1 ? 'source' : 'sources' }}</summary>
              <ul>
                <li v-for="(source, sourceIndex) in msg.sources" :key="source.doc_id || source.question || sourceIndex">
                  <span v-if="source.question" class="sandbox-source-title">FAQ: {{ source.question }}</span>
                  <span v-else class="sandbox-source-title">Document {{ sourceIndex + 1 }}</span>
                  <span v-if="source.relevance !== undefined" class="sandbox-source-score">{{ Math.round(source.relevance * 100) }}% match</span>
                  <p v-if="source.preview">{{ source.preview }}</p>
                </li>
              </ul>
            </details>
          </div>
        </article>

        <div v-if="thinking" class="sandbox-pending" role="status" aria-live="polite">
          <span class="sandbox-spinner" aria-hidden="true"></span>
          <div>
            <p class="font-medium">{{ pendingMessage }}</p>
            <p class="text-xs">First searches may take longer while the knowledge index loads.</p>
          </div>
        </div>
      </div>

      <form class="sandbox-composer" @submit.prevent="sendMessage">
        <label class="sr-only" for="sandbox-message">Message</label>
        <input
          id="sandbox-message"
          v-model="input"
          autocomplete="off"
          placeholder="Ask a question about your business..."
          :disabled="thinking || !apiKey"
        />
        <button type="submit" :disabled="thinking || !input.trim() || !apiKey">
          {{ thinking ? 'Working…' : 'Send' }}
        </button>
      </form>
      <p class="sandbox-footnote">Messages here use your selected AI provider and knowledge base.</p>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const messages = ref([])
const input = ref('')
const thinking = ref(false)
const pendingMessage = ref('Searching your knowledge base…')
const conversationId = ref(null)
const chatContainer = ref(null)
const pageError = ref('')
const loadingBusiness = ref(false)
const apiKey = computed(() => businessStore.currentBusiness?.public_key || '')
let pendingTimer

function getErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  return detail?.message || detail?.diagnostic || error.message || 'The request could not be completed.'
}

async function initialize() {
  pageError.value = ''
  if (businessStore.currentBusiness?.public_key) return
  loadingBusiness.value = true
  try {
    const businesses = await businessStore.fetchMyBusinesses()
    if (!businesses.length) pageError.value = 'Create a workspace before testing your support agent.'
    else if (!businessStore.currentBusiness?.public_key) pageError.value = 'This workspace is missing its public chat key. Refresh the workspace or contact support.'
  } catch (error) {
    pageError.value = getErrorMessage(error)
  } finally {
    loadingBusiness.value = false
  }
}

function newChat() {
  if (thinking.value) return
  messages.value = []
  conversationId.value = null
  input.value = ''
}

function scrollToLatest() {
  if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

function formatErrorCode(code) {
  return String(code).toLowerCase().replaceAll('_', ' ')
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || thinking.value) return
  if (!apiKey.value) {
    pageError.value = 'Your workspace chat key is unavailable. Reload the workspace and try again.'
    return
  }

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  thinking.value = true
  pendingMessage.value = 'Searching your knowledge base…'
  pendingTimer = setTimeout(() => {
    pendingMessage.value = 'Generating a response…'
  }, 1800)

  try {
    await nextTick()
    scrollToLatest()
    const { data } = await api.post(`/chat/${encodeURIComponent(apiKey.value)}`, {
      message: text,
      conversation_id: conversationId.value,
      customer_name: 'Sandbox User',
    }, { timeout: 120000 })

    conversationId.value = data.conversation_id
    messages.value.push({
      role: 'ai',
      content: data.message,
      confidence: data.confidence_score,
      sources: Array.isArray(data.sources) ? data.sources : [],
      errorCode: data.error_code,
      diagnostic: data.diagnostic,
      actionHint: data.action_hint,
    })
  } catch (error) {
    messages.value.push({
      role: 'ai',
      content: getErrorMessage(error),
      errorCode: error.code === 'ECONNABORTED' ? 'REQUEST_TIMEOUT' : 'REQUEST_FAILED',
      diagnostic: error.code === 'ECONNABORTED'
        ? 'The request exceeded the two-minute client limit. The server may still be loading the knowledge index or contacting the provider.'
        : '',
      actionHint: 'Check the AI provider connection and document processing status, then try again.',
    })
  } finally {
    clearTimeout(pendingTimer)
    thinking.value = false
    await nextTick()
    scrollToLatest()
  }
}

onMounted(initialize)
</script>

<style scoped>
.sandbox-page { max-width: 1040px; margin: 0 auto; }
.sandbox-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 24px; }
.sandbox-kicker { color: #918ba0; font-size: .66rem; font-weight: 700; letter-spacing: .14em; margin-bottom: 7px; }
.sandbox-secondary-button { flex: 0 0 auto; border: 1px solid rgba(173,190,220,.16); border-radius: .7rem; background: rgba(255,255,255,.035); padding: .68rem .9rem; color: #d1cdda; font-size: .8rem; }
.sandbox-secondary-button:hover:not(:disabled) { border-color: rgba(184,165,255,.35); background: rgba(167,139,250,.1); color: #e8dfff; }
.sandbox-secondary-button:disabled { cursor: not-allowed; opacity: .55; }
.sandbox-alert { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 16px; border: 1px solid rgba(248,113,113,.23); border-radius: .8rem; background: rgba(127,29,29,.16); padding: .8rem 1rem; color: #fecaca; font-size: .84rem; }
.sandbox-alert button { border: 1px solid rgba(248,113,113,.25); border-radius: .55rem; background: rgba(248,113,113,.09); padding: .45rem .65rem; color: #fecaca; font-size: .75rem; }
.sandbox-alert button:disabled { cursor: wait; opacity: .6; }
.sandbox-card { overflow: hidden; border: 1px solid rgba(173,190,220,.13); border-radius: 1rem; background: rgba(19,20,28,.88); box-shadow: 0 22px 70px rgba(0,0,0,.2); }
.sandbox-messages { display: flex; min-height: 430px; max-height: min(62vh, 720px); flex-direction: column; gap: 18px; overflow-y: auto; padding: clamp(18px, 3vw, 30px); scroll-behavior: smooth; }
.sandbox-empty { display: grid; flex: 1; align-content: center; justify-items: center; padding: 40px 12px; text-align: center; }
.sandbox-empty-icon { display: grid; width: 46px; height: 46px; place-items: center; margin-bottom: 15px; border: 1px solid rgba(167,139,250,.22); border-radius: 15px; background: rgba(167,139,250,.1); color: #c9baff; font-size: 1.35rem; }
.sandbox-empty h3 { margin: 0; color: #e7e3ee; font-size: .96rem; font-weight: 650; }
.sandbox-empty p { margin: 6px 0 0; color: #9690a2; font-size: .8rem; }
.sandbox-message-row { display: flex; }
.sandbox-message-row.is-user { justify-content: flex-end; }
.sandbox-message-row.is-agent { justify-content: flex-start; }
.sandbox-message { max-width: min(78%, 680px); border: 1px solid rgba(173,190,220,.12); border-radius: 1rem; padding: .85rem 1rem; font-size: .88rem; line-height: 1.65; }
.sandbox-message-user { border-color: rgba(184,165,255,.2); border-bottom-right-radius: .28rem; background: linear-gradient(135deg, rgba(116,89,203,.32), rgba(88,67,166,.25)); color: #f3efff; }
.sandbox-message-agent { border-bottom-left-radius: .28rem; background: rgba(255,255,255,.035); color: #d9d5e2; }
.sandbox-message-label { margin-bottom: .28rem; color: #a69cbc; font-size: .67rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.sandbox-message-user .sandbox-message-label { color: #d5caff; }
.sandbox-diagnostic { margin-top: .8rem; border-top: 1px solid rgba(248,113,113,.18); padding-top: .65rem; color: #ffbcbc; font-size: .76rem; }
.sandbox-action-hint { margin-top: .35rem; color: #d4c6ff; }
.sandbox-meta { margin-top: .55rem; color: #9992a8; font-size: .7rem; }
.sandbox-sources { margin-top: .7rem; border-top: 1px solid rgba(173,190,220,.1); padding-top: .55rem; color: #bcb5ce; font-size: .75rem; }
.sandbox-sources summary { cursor: pointer; color: #c6b7ff; font-weight: 600; }
.sandbox-sources ul { display: grid; gap: .6rem; margin: .55rem 0 0; padding: 0; list-style: none; }
.sandbox-sources li { border-left: 2px solid rgba(167,139,250,.35); padding-left: .65rem; }
.sandbox-source-title { color: #d5cfdf; font-weight: 600; }
.sandbox-source-score { margin-left: .5rem; color: #958da4; font-size: .67rem; }
.sandbox-sources li p { margin-top: .25rem; color: #9690a2; font-size: .72rem; }
.sandbox-pending { display: flex; align-items: center; gap: 12px; align-self: flex-start; border: 1px solid rgba(167,139,250,.15); border-radius: .8rem; background: rgba(167,139,250,.055); padding: .7rem .9rem; color: #d5caff; font-size: .8rem; }
.sandbox-pending p + p { margin-top: 2px; color: #8f899c; }
.sandbox-spinner { width: 15px; height: 15px; flex: 0 0 auto; border: 2px solid rgba(199,185,255,.25); border-top-color: #c6b7ff; border-radius: 50%; animation: sandbox-spin .75s linear infinite; }
.sandbox-composer { display: flex; gap: 10px; border-top: 1px solid rgba(173,190,220,.1); background: rgba(10,11,17,.58); padding: 14px; }
.sandbox-composer input { min-width: 0; flex: 1; border: 1px solid rgba(173,190,220,.16); border-radius: .7rem; outline: none; background: rgba(255,255,255,.035); padding: .72rem .9rem; color: #f0edf7; font: inherit; font-size: .84rem; }
.sandbox-composer input::placeholder { color: #777286; }
.sandbox-composer input:focus { border-color: rgba(184,165,255,.6); box-shadow: 0 0 0 3px rgba(167,139,250,.12); }
.sandbox-composer input:disabled { cursor: not-allowed; opacity: .6; }
.sandbox-composer button { flex: 0 0 auto; border: 1px solid rgba(201,187,255,.23); border-radius: .7rem; background: linear-gradient(135deg,#8064d9,#6049b0); padding: .68rem 1.2rem; color: white; font-size: .82rem; font-weight: 650; }
.sandbox-composer button:hover:not(:disabled) { filter: brightness(1.12); }
.sandbox-composer button:disabled { cursor: not-allowed; opacity: .45; }
.sandbox-footnote { margin: 0; border-top: 1px solid rgba(173,190,220,.07); padding: .65rem 1rem; color: #777286; font-size: .68rem; }
@keyframes sandbox-spin { to { transform: rotate(360deg); } }
@media (max-width: 620px) {
  .sandbox-heading { align-items: flex-start; flex-direction: column; }
  .sandbox-secondary-button { align-self: flex-start; }
  .sandbox-message { max-width: 92%; }
  .sandbox-messages { min-height: 380px; max-height: 64vh; }
  .sandbox-composer { padding: 10px; }
}
@media (prefers-reduced-motion: reduce) { .sandbox-messages { scroll-behavior: auto; } .sandbox-spinner { animation-duration: 1.5s; } }
</style>
