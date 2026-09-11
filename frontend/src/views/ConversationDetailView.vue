<template>
  <div class="p-8 max-w-3xl">
    <router-link to="/app/conversations" class="text-indigo-600 text-sm hover:underline mb-4 inline-block">
      &larr; Back to Conversations
    </router-link>

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <!-- Messages -->
      <div class="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="flex"
          :class="msg.sender === 'customer' ? 'justify-start' : 'justify-end'"
        >
          <div
            class="max-w-[75%] px-4 py-3 rounded-xl text-sm"
            :class="bubbleClass(msg.sender)"
          >
            <p class="text-xs font-medium mb-1 opacity-75">
              {{ msg.sender === 'customer' ? 'Customer' : msg.sender === 'ai' ? 'AI' : 'Agent' }}
            </p>
            <p class="whitespace-pre-wrap">{{ msg.content }}</p>
            <p v-if="msg.confidence_score !== null && msg.sender === 'ai'" class="text-xs mt-1 opacity-60">
              Confidence: {{ (msg.confidence_score * 100).toFixed(0) }}%
            </p>
          </div>
        </div>
      </div>

      <!-- Agent Reply (for escalated) -->
      <div class="border-t border-gray-200 p-4">
        <div class="flex gap-3">
          <input
            v-model="agentReply"
            @keyup.enter="sendReply"
            placeholder="Type a reply as an agent..."
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
          <button
            @click="sendReply"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition"
          >
            Send
          </button>
          <button
            @click="resolveConv"
            class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition"
          >
            Resolve
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const route = useRoute()
const businessStore = useBusinessStore()
const messages = ref([])
const agentReply = ref('')
const bid = businessStore.currentBusiness?.id
const convId = route.params.id

function bubbleClass(sender) {
  if (sender === 'customer') return 'bg-gray-100 text-gray-800'
  if (sender === 'ai') return 'bg-indigo-100 text-indigo-800'
  return 'bg-green-100 text-green-800'
}

async function loadMessages() {
  if (!bid || !convId) return
  const { data } = await api.get(`/conversations/${bid}/${convId}/messages`)
  messages.value = data
}

async function sendReply() {
  if (!agentReply.value.trim()) return
  await api.post(`/conversations/${bid}/${convId}/escalate`, {
    action: 'respond',
    agent_response: agentReply.value,
  })
  agentReply.value = ''
  await loadMessages()
}

async function resolveConv() {
  await api.post(`/conversations/${bid}/${convId}/escalate`, { action: 'resolve' })
  await loadMessages()
}

onMounted(loadMessages)
</script>
