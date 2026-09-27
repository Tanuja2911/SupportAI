<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-4xl space-y-5">
      <router-link to="/app/conversations" class="inline-flex items-center gap-2 text-sm font-semibold text-stone-600 transition hover:text-blue-700"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m15 18-6-6 6-6M9 12h12"/></svg>Back to conversations</router-link>
      <header><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Conversation transcript</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Customer conversation</h1><p class="mt-1 text-sm text-stone-500">Review the chat and send a reply when a person needs to step in.</p></header>
      <div v-if="notice" class="rounded-xl border px-4 py-3 text-sm" :class="error ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'" role="status">{{ notice }}</div>
      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <div class="flex items-center justify-between border-b border-stone-100 px-4 py-3.5 sm:px-5"><div class="flex items-center gap-3"><span class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-sm font-bold text-blue-700">{{ customerInitial }}</span><span><span class="block text-sm font-semibold text-stone-900">Customer</span><span class="block text-xs text-stone-500">{{ messages.length }} {{ messages.length === 1 ? 'message' : 'messages' }}</span></span></div><span class="rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700">Human support</span></div>
        <div ref="messageContainer" class="min-h-[22rem] max-h-[65vh] space-y-5 overflow-y-auto bg-stone-50/70 p-4 sm:p-6" aria-label="Conversation messages" aria-live="polite">
          <div v-if="loading" class="space-y-4" aria-label="Loading messages"><div v-for="n in 3" :key="n" class="h-20 w-3/4 animate-pulse rounded-2xl bg-stone-200"></div></div>
          <div v-else-if="!messages.length" class="flex min-h-72 items-center justify-center text-center"><div><p class="text-sm font-semibold text-stone-800">No messages yet</p><p class="mt-1 text-sm text-stone-500">Messages will appear here when available.</p></div></div>
          <article v-for="msg in messages" v-show="!loading && messages.length" :key="msg.id" class="flex" :class="msg.sender === 'customer' ? 'justify-start' : 'justify-end'"><div class="max-w-[90%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[78%]" :class="bubbleClass(msg.sender)"><p class="mb-1.5 text-[11px] font-semibold uppercase tracking-wide opacity-70">{{ msg.sender === 'customer' ? 'Customer' : msg.sender === 'ai' ? 'AI assistant' : 'Support agent' }}</p><p class="whitespace-pre-wrap break-words text-sm leading-6">{{ msg.content }}</p><p v-if="msg.confidence_score !== null && msg.sender === 'ai'" class="mt-2 text-[11px] opacity-65">Confidence {{ (msg.confidence_score * 100).toFixed(0) }}%</p></div></article>
        </div>
        <form class="border-t border-stone-100 p-4 sm:p-5" @submit.prevent="sendReply"><label for="agent-reply" class="mb-2 block text-sm font-semibold text-stone-800">Reply to customer</label><div class="flex flex-col gap-2 sm:flex-row"><input id="agent-reply" v-model="agentReply" placeholder="Write a helpful reply…" class="min-w-0 flex-1 rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" :disabled="sending || resolving"/><button type="submit" :disabled="sending || resolving || !agentReply.trim()" class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m5 12 14-7-4 14-3-6-7-1Z"/></svg>{{ sending ? 'Sending…' : 'Send reply' }}</button><button type="button" @click="resolveConv" :disabled="sending || resolving" class="rounded-xl border border-emerald-200 px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50 disabled:opacity-50">{{ resolving ? 'Resolving…' : 'Mark resolved' }}</button></div></form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const route = useRoute()
const businessStore = useBusinessStore()
const messages = ref([])
const agentReply = ref('')
const messageContainer = ref(null)
const loading = ref(true)
const sending = ref(false)
const resolving = ref(false)
const notice = ref('')
const error = ref(false)
const bid = businessStore.currentBusiness?.id
const convId = route.params.id
const customerInitial = computed(() => messages.value.find((message) => message.sender === 'customer')?.content?.charAt(0)?.toUpperCase() || 'C')

function bubbleClass(sender) {
  if (sender === 'customer') return 'rounded-tl-md border border-stone-200 bg-white text-stone-800'
  if (sender === 'ai') return 'rounded-tr-md bg-blue-100 text-blue-900'
  return 'rounded-tr-md bg-emerald-100 text-emerald-900'
}

async function scrollToBottom() {
  await nextTick()
  if (messageContainer.value) messageContainer.value.scrollTop = messageContainer.value.scrollHeight
}

async function loadMessages() {
  if (!bid || !convId) { loading.value = false; return }
  loading.value = true
  try { const { data } = await api.get(`/conversations/${bid}/${convId}/messages`); messages.value = data; await scrollToBottom() }
  catch (err) { notice.value = err.response?.data?.detail || 'Could not load this conversation. Please try again.'; error.value = true }
  finally { loading.value = false }
}

async function sendReply() {
  if (!agentReply.value.trim() || sending.value) return
  sending.value = true; notice.value = ''
  try {
    await api.post(`/conversations/${bid}/${convId}/escalate`, { action: 'respond', agent_response: agentReply.value.trim() })
    agentReply.value = ''; await loadMessages(); notice.value = 'Reply sent.'; error.value = false
  } catch (err) { notice.value = err.response?.data?.detail || 'Could not send your reply.'; error.value = true }
  finally { sending.value = false }
}

async function resolveConv() {
  if (resolving.value) return
  resolving.value = true; notice.value = ''
  try { await api.post(`/conversations/${bid}/${convId}/escalate`, { action: 'resolve' }); await loadMessages(); notice.value = 'Conversation marked as resolved.'; error.value = false }
  catch (err) { notice.value = err.response?.data?.detail || 'Could not resolve this conversation.'; error.value = true }
  finally { resolving.value = false }
}

onMounted(loadMessages)
</script>
