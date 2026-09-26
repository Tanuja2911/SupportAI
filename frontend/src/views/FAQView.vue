<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">FAQ Overrides</h2>
        <p class="text-gray-500 text-sm mt-1">Set exact answers for specific questions (bypasses RAG)</p>
      </div>
      <div class="flex gap-3">
        <button
          @click="autoGenerate"
          :disabled="generating"
          class="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition disabled:opacity-50"
        >
          {{ generating ? 'Generating...' : 'Auto-Generate FAQs' }}
        </button>
        <button
          @click="showModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          Add FAQ
        </button>
      </div>
    </div>

    <!-- Auto-Generated Suggestions -->
    <div v-if="suggestions.length" class="mb-6 bg-blue-50 border border-blue-200 rounded-xl p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-semibold text-blue-800">AI-Generated Suggestions</h3>
          <p class="text-xs text-blue-500 mt-1">Review and accept the ones you want to add as FAQ overrides</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="acceptAll"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition"
          >
            Accept All ({{ suggestions.length }})
          </button>
          <button
            @click="suggestions = []"
            class="px-3 py-1.5 text-blue-600 border border-blue-300 rounded-lg text-xs font-medium hover:bg-blue-100 transition"
          >
            Dismiss
          </button>
        </div>
      </div>
      <div class="space-y-3">
        <div
          v-for="(s, i) in suggestions"
          :key="i"
          class="bg-white rounded-lg border border-blue-100 p-4"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1">
              <p class="font-medium text-gray-800 text-sm">Q: {{ s.question }}</p>
              <p class="text-sm text-gray-600 mt-1">A: {{ s.answer }}</p>
            </div>
            <div class="flex gap-2 flex-shrink-0">
              <button
                @click="acceptSuggestion(i)"
                class="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 transition"
              >
                Accept
              </button>
              <button
                @click="suggestions.splice(i, 1)"
                class="px-3 py-1.5 text-red-500 border border-red-200 rounded-lg text-xs font-medium hover:bg-red-50 transition"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate Error -->
    <div v-if="genError" class="mb-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm">
      {{ genError }}
    </div>

    <!-- Existing FAQs -->
    <div class="space-y-3">
      <div v-for="faq in faqs" :key="faq.id" class="bg-white rounded-xl border border-gray-200 p-5">
        <div class="flex items-start justify-between">
          <div>
            <p class="font-medium text-gray-800">Q: {{ faq.question }}</p>
            <p class="text-sm text-gray-600 mt-2">A: {{ faq.answer }}</p>
          </div>
          <button @click="deleteFaq(faq.id)" class="text-red-500 hover:text-red-700 text-sm ml-4">Delete</button>
        </div>
      </div>
      <div v-if="faqs.length === 0 && !suggestions.length" class="text-center text-gray-400 py-12">
        No FAQ overrides yet. Try "Auto-Generate FAQs" to create some from your documents.
      </div>
    </div>

    <!-- Manual Add Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-lg">
        <h3 class="text-lg font-bold mb-4">Add FAQ Override</h3>
        <input
          v-model="newQuestion"
          placeholder="Customer question..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 outline-none focus:ring-2 focus:ring-blue-500"
        />
        <textarea
          v-model="newAnswer"
          rows="4"
          placeholder="Your exact answer..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        ></textarea>
        <div class="flex justify-end gap-3">
          <button @click="showModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
          <button @click="addFaq" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Add</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const faqs = ref([])
const showModal = ref(false)
const newQuestion = ref('')
const newAnswer = ref('')
const suggestions = ref([])
const generating = ref(false)
const genError = ref('')
const bid = businessStore.currentBusiness?.id

async function loadFaqs() {
  if (!bid) return
  const { data } = await api.get(`/faq/${bid}`)
  faqs.value = data
}

async function addFaq() {
  if (!newQuestion.value || !newAnswer.value) return
  await api.post(`/faq/${bid}`, { question: newQuestion.value, answer: newAnswer.value })
  showModal.value = false
  newQuestion.value = ''
  newAnswer.value = ''
  await loadFaqs()
}

async function deleteFaq(faqId) {
  if (!confirm('Delete this FAQ?')) return
  await api.delete(`/faq/${bid}/${faqId}`)
  await loadFaqs()
}

async function autoGenerate() {
  generating.value = true
  genError.value = ''
  suggestions.value = []
  try {
    const { data } = await api.post(`/faq/${bid}/auto-generate`)
    suggestions.value = data.suggestions
  } catch (err) {
    genError.value = err.response?.data?.detail || 'Failed to generate FAQs. Make sure you have processed documents and an API key configured.'
  } finally {
    generating.value = false
  }
}

async function acceptSuggestion(index) {
  const s = suggestions.value[index]
  await api.post(`/faq/${bid}`, { question: s.question, answer: s.answer })
  suggestions.value.splice(index, 1)
  await loadFaqs()
}

async function acceptAll() {
  for (const s of suggestions.value) {
    await api.post(`/faq/${bid}`, { question: s.question, answer: s.answer })
  }
  suggestions.value = []
  await loadFaqs()
}

onMounted(loadFaqs)
</script>
