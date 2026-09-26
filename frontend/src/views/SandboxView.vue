<template>
  <div class="p-8 max-w-2xl">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-2xl font-bold text-gray-800">Test Chat Sandbox</h2>
      <button
        @click="newChat"
        class="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition"
      >
        New Chat
      </button>
    </div>
    <p class="text-gray-500 text-sm mb-6">Test your AI agent before going live.</p>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <!-- Messages -->
      <div class="p-6 space-y-4 min-h-[400px] max-h-[60vh] overflow-y-auto" ref="chatContainer">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[75%] px-4 py-3 rounded-xl text-sm"
            :class="msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'"
          >
            <p class="whitespace-pre-wrap">{{ msg.content }}</p>
            <p v-if="msg.confidence" class="text-xs mt-1 opacity-60">
              Confidence: {{ (msg.confidence * 100).toFixed(0) }}%
            </p>
            <div v-if="msg.sources && msg.sources.length" class="mt-2 text-xs opacity-60">
              Sources: {{ msg.sources.length }} document(s)
            </div>
          </div>
        </div>
        <div v-if="thinking" class="flex justify-start">
          <div class="bg-gray-100 px-4 py-3 rounded-xl text-sm text-gray-500">Thinking...</div>
        </div>
      </div>

      <!-- Input -->
      <div class="border-t border-gray-200 p-4">
        <div class="flex gap-3">
          <input
            v-model="input"
            @keyup.enter="sendMessage"
            placeholder="Ask your AI agent something..."
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            :disabled="thinking"
          />
          <button
            @click="sendMessage"
            :disabled="thinking || !input.trim()"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
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
