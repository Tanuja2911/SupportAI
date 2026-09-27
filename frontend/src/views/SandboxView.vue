<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-4xl space-y-6">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Preview your assistant</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Test Chat</h1><p class="mt-1 text-sm text-stone-500">Try customer questions before adding the widget to your website.</p></div><button @click="newChat" class="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition hover:bg-stone-50">Start a new chat</button></header>
      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <div class="flex items-center gap-3 border-b border-stone-100 px-4 py-3.5 sm:px-5"><span class="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/></svg></span><span class="flex-1"><span class="block text-sm font-semibold text-stone-900">{{ businessStore.currentBusiness?.name || 'Your assistant' }}</span><span class="mt-0.5 flex items-center gap-1.5 text-xs text-stone-500"><span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>Sandbox conversation</span></span><span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">Test mode</span></div>
        <div ref="chatContainer" class="min-h-[24rem] max-h-[62vh] space-y-5 overflow-y-auto bg-stone-50/70 p-4 sm:p-6" aria-live="polite">
          <div v-if="!messages.length" class="flex min-h-80 items-center justify-center text-center"><div class="max-w-sm"><span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/></svg></span><p class="mt-4 text-sm font-semibold text-stone-800">Ask your assistant a question</p><p class="mt-1 text-sm leading-6 text-stone-500">Try something a customer might ask. The assistant will answer using your knowledge sources.</p></div></div>
          <article v-for="(msg, i) in messages" :key="i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"><div class="max-w-[90%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[78%]" :class="msg.role === 'user' ? 'rounded-tr-md bg-blue-600 text-white' : 'rounded-tl-md border border-stone-200 bg-white text-stone-800'"><p class="mb-1 text-[11px] font-semibold uppercase tracking-wide opacity-70">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</p><p class="whitespace-pre-wrap break-words text-sm leading-6">{{ msg.content }}</p><p v-if="msg.confidence !== undefined && msg.confidence !== null" class="mt-2 text-[11px] opacity-65">Confidence {{ (msg.confidence * 100).toFixed(0) }}%</p><div v-if="msg.sources?.length" class="mt-3 border-t border-stone-100 pt-2 text-xs text-stone-500">Based on {{ msg.sources.length }} {{ msg.sources.length === 1 ? 'source' : 'sources' }}</div></div></article>
          <div v-if="thinking" class="flex justify-start"><div class="rounded-2xl rounded-tl-md border border-stone-200 bg-white px-4 py-3 text-sm text-stone-500 shadow-sm"><span class="inline-flex items-center gap-2"><span class="flex gap-1"><i class="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500"></i><i class="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:120ms]"></i><i class="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500 [animation-delay:240ms]"></i></span>Thinking…</span></div></div>
        </div>
        <form class="border-t border-stone-100 p-4 sm:p-5" @submit.prevent="sendMessage"><label for="sandbox-prompt" class="sr-only">Ask your assistant</label><div class="flex gap-2"><input id="sandbox-prompt" v-model="input" placeholder="Ask your assistant something…" class="min-w-0 flex-1 rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" :disabled="thinking"/><button type="submit" :disabled="thinking || !input.trim()" class="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m5 12 14-7-4 14-3-6-7-1Z"/></svg><span class="hidden sm:inline">Send</span></button></div></form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const messages = ref([])
const input = ref('')
const thinking = ref(false)
const conversationId = ref(null)
const chatContainer = ref(null)

function newChat() {
  messages.value = []
  conversationId.value = null
  input.value = ''
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  thinking.value = true

  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }

  try {
    const apiKey = businessStore.currentBusiness?.api_key
    const { data } = await axios.post(`/api/chat/${apiKey}`, {
      message: text,
      conversation_id: conversationId.value,
      customer_name: 'Sandbox User',
    })
    conversationId.value = data.conversation_id
    messages.value.push({
      role: 'ai',
      content: data.message,
      confidence: data.confidence_score,
      sources: data.sources,
    })
  } catch (err) {
    messages.value.push({
      role: 'ai',
      content: 'Error: ' + (err.response?.data?.detail || 'Failed to get response'),
    })
  } finally {
    thinking.value = false
    await nextTick()
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }
}
</script>
