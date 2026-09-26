<template>
  <div class="p-8">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Conversations</h2>

    <div class="flex gap-2 mb-4">
      <button
        v-for="f in filters"
        :key="f.value"
        @click="activeFilter = f.value"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
        :class="activeFilter === f.value ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-blue-50'"
      >
        {{ f.label }}
      </button>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
      <router-link
        v-for="conv in conversations"
        :key="conv.id"
        :to="`/app/conversations/${conv.id}`"
        class="flex items-center justify-between px-6 py-4 hover:bg-blue-50 transition block"
      >
        <div>
          <p class="font-medium text-gray-800">{{ conv.customer_name || 'Anonymous' }}</p>
          <p class="text-sm text-gray-500">{{ conv.customer_email || 'No email' }}</p>
        </div>
        <div class="text-right">
          <span
            class="px-2 py-1 rounded-full text-xs font-medium"
            :class="statusClass(conv.status)"
          >
            {{ conv.status }}
          </span>
          <p class="text-xs text-gray-400 mt-1">{{ conv.message_count }} messages</p>
        </div>
      </router-link>
      <div v-if="conversations.length === 0" class="px-6 py-12 text-center text-gray-400">
        No conversations yet.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const conversations = ref([])
const activeFilter = ref('')

const filters = [
  { label: 'All', value: '' },
  { label: 'Active', value: 'active' },
  { label: 'Escalated', value: 'escalated' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Closed', value: 'closed' },
]

function statusClass(status) {
  const map = {
    active: 'bg-green-100 text-green-700',
    escalated: 'bg-red-100 text-red-700',
    resolved: 'bg-emerald-100 text-emerald-700',
    closed: 'bg-gray-100 text-gray-700',
  }
  return map[status] || 'bg-gray-100 text-gray-700'
}

async function loadConversations() {
  const bid = businessStore.currentBusiness?.id
  if (!bid) return
  const params = activeFilter.value ? { status: activeFilter.value } : {}
  const { data } = await api.get(`/conversations/${bid}`, { params })
  conversations.value = data
}

watch(activeFilter, loadConversations)
onMounted(loadConversations)
</script>
