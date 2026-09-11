<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-2">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">Knowledge Gaps</h2>
        <p class="text-gray-500 text-sm mt-1">AI-detected topics your knowledge base doesn't cover well</p>
      </div>
      <button
        @click="analyze"
        :disabled="analyzing"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50"
      >
        {{ analyzing ? 'Analyzing...' : 'Run Analysis' }}
      </button>
    </div>

    <!-- How it works -->
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 text-sm text-gray-500">
      Analyzes low-confidence AI responses and escalated conversations to find topics your documents don't cover. Based on active learning — the AI identifies what it doesn't know and tells you what to add.
    </div>

    <!-- Analysis result message -->
    <div v-if="resultMsg" class="mb-4 bg-green-50 text-green-700 p-3 rounded-lg text-sm">
      {{ resultMsg }}
    </div>
    <div v-if="error" class="mb-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm">
      {{ error }}
    </div>

    <!-- Gaps List -->
    <div class="space-y-4">
      <div
        v-for="gap in gaps"
        :key="gap.id"
        class="bg-white rounded-xl border border-gray-200 p-5"
        :class="gap.status === 'resolved' ? 'opacity-50' : ''"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="font-semibold text-gray-800">{{ gap.topic }}</h3>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="gap.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'"
              >
                {{ gap.status === 'resolved' ? 'Resolved' : 'Open' }}
              </span>
              <span class="text-xs text-gray-400">{{ gap.query_count }} queries</span>
            </div>
            <p class="text-sm text-gray-600 mb-3">{{ gap.description }}</p>

            <!-- Suggestion -->
            <div class="bg-indigo-50 rounded-lg p-3 mb-3">
              <p class="text-xs font-medium text-indigo-700 mb-1">Suggested Action</p>
              <p class="text-sm text-indigo-600">{{ gap.suggestion }}</p>
            </div>

            <!-- Sample queries -->
            <div v-if="gap.sample_queries && gap.sample_queries.length">
              <p class="text-xs font-medium text-gray-500 mb-1">Sample customer queries:</p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(q, i) in gap.sample_queries.slice(0, 5)"
                  :key="i"
                  class="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600"
                >
                  "{{ q }}"
                </span>
              </div>
            </div>
          </div>

          <button
            v-if="gap.status !== 'resolved'"
            @click="resolve(gap.id)"
            class="px-3 py-1.5 text-green-600 border border-green-200 rounded-lg text-xs font-medium hover:bg-green-50 transition flex-shrink-0"
          >
            Mark Resolved
          </button>
        </div>
      </div>

      <div v-if="!gaps.length && !analyzing" class="text-center py-16">
        <p class="text-gray-400 mb-2">No knowledge gaps detected yet.</p>
        <p class="text-gray-400 text-sm">Click "Run Analysis" after your chatbot has handled some conversations.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const bid = businessStore.currentBusiness?.id
const gaps = ref([])
const analyzing = ref(false)
const resultMsg = ref('')
const error = ref('')

async function loadGaps() {
  if (!bid) return
  try {
    const { data } = await api.get(`/knowledge-gaps/${bid}`)
    gaps.value = data
  } catch (err) {
    console.error('Failed to load gaps', err)
  }
}

async function analyze() {
  analyzing.value = true
  resultMsg.value = ''
  error.value = ''
  try {
    const { data } = await api.post(`/knowledge-gaps/${bid}/analyze`)
    resultMsg.value = data.message
    await loadGaps()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Analysis failed. Make sure you have conversations and an API key configured.'
  } finally {
    analyzing.value = false
  }
}

async function resolve(gapId) {
  try {
    await api.patch(`/knowledge-gaps/${bid}/${gapId}`)
    await loadGaps()
  } catch (err) {
    console.error('Failed to resolve gap', err)
  }
}

onMounted(loadGaps)
</script>
