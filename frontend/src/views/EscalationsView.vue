<template>
  <div class="p-8">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Escalations</h2>
    <p class="text-gray-500 mb-4">Conversations where the AI wasn't confident enough and needs human help.</p>

    <div class="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
      <router-link
        v-for="conv in escalations"
        :key="conv.id"
        :to="`/app/conversations/${conv.id}`"
        class="flex items-center justify-between px-6 py-4 hover:bg-pink-50 transition block"
      >
        <div>
          <p class="font-medium text-gray-800">{{ conv.customer_name || 'Anonymous' }}</p>
          <p class="text-sm text-gray-500">{{ conv.message_count }} messages</p>
        </div>
        <div class="text-right">
          <span class="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">Escalated</span>
          <p class="text-xs text-gray-400 mt-1">{{ new Date(conv.updated_at).toLocaleString() }}</p>
        </div>
      </router-link>
      <div v-if="escalations.length === 0" class="px-6 py-12 text-center text-gray-400">
        No escalated conversations. Your AI is handling everything!
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const escalations = ref([])

onMounted(async () => {
  const bid = businessStore.currentBusiness?.id
  if (!bid) return
  const { data } = await api.get(`/conversations/${bid}`, { params: { status: 'escalated' } })
  escalations.value = data
})
</script>
