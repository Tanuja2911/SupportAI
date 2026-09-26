<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Knowledge Base</h2>
      <div class="flex gap-3">
        <button
          @click="showUrlModal = true"
          class="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition"
        >
          Add URL
        </button>
        <label class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition cursor-pointer">
          Upload File
          <input type="file" class="hidden" accept=".pdf,.docx,.txt" @change="handleFileUpload" />
        </label>
      </div>
    </div>

    <div v-if="uploading" class="bg-blue-50 text-blue-700 p-3 rounded-lg mb-4 text-sm">
      Uploading and processing document...
    </div>

    <!-- Documents Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full">
        <thead class="bg-blue-50 border-b border-gray-200">
          <tr>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Title</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Type</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Chunks</th>
            <th class="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
            <th class="px-6 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="doc in documents" :key="doc.id" class="hover:bg-blue-50">
            <td class="px-6 py-4 text-sm font-medium text-gray-800">
              {{ doc.title }}
              <p v-if="doc.status === 'failed' && doc.error_message" class="mt-1 text-xs font-normal text-red-600">
                {{ doc.error_message }}
              </p>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500 uppercase">{{ doc.file_type }}</td>
            <td class="px-6 py-4">
              <span
                class="px-2 py-1 rounded-full text-xs font-medium"
                :class="statusClass(doc.status)"
              >
                {{ doc.status }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-500">{{ doc.chunk_count }}</td>
            <td class="px-6 py-4 text-sm text-gray-500">{{ new Date(doc.created_at).toLocaleDateString() }}</td>
            <td class="px-6 py-4">
              <button @click="deleteDoc(doc.id)" class="text-red-500 hover:text-red-700 text-sm">Delete</button>
            </td>
          </tr>
          <tr v-if="documents.length === 0">
            <td colspan="6" class="px-6 py-12 text-center text-gray-400">
              No documents yet. Upload a PDF, DOCX, or add a URL to get started.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- URL Modal -->
    <div v-if="showUrlModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-bold mb-4">Add URL</h3>
        <input
          v-model="urlInput"
          type="url"
          placeholder="https://docs.example.com/faq"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          v-model="urlTitle"
          type="text"
          placeholder="Title (optional)"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div class="flex justify-end gap-3">
          <button @click="showUrlModal = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 text-sm">Cancel</button>
          <button @click="handleUrlAdd" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Add</button>
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
const documents = ref([])
const uploading = ref(false)
const showUrlModal = ref(false)
const urlInput = ref('')
const urlTitle = ref('')

const bid = businessStore.currentBusiness?.id

function statusClass(status) {
  const map = {
    ready: 'bg-green-100 text-green-700',
    processing: 'bg-blue-100 text-blue-700',
    pending: 'bg-yellow-100 text-yellow-700',
    failed: 'bg-red-100 text-red-700',
  }
  return map[status] || 'bg-gray-100 text-gray-700'
}

async function loadDocs() {
  if (!bid) return
  const { data } = await api.get(`/knowledge/${bid}/documents`)
  documents.value = data
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await api.post(`/knowledge/${bid}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await loadDocs()
  } catch (err) {
    alert(err.response?.data?.detail || 'Upload failed')
  } finally {
    uploading.value = false
  }
}

async function handleUrlAdd() {
  if (!urlInput.value) return
  try {
    await api.post(`/knowledge/${bid}/url`, { url: urlInput.value, title: urlTitle.value || null })
    showUrlModal.value = false
    urlInput.value = ''
    urlTitle.value = ''
    await loadDocs()
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to add URL')
  }
}

async function deleteDoc(docId) {
  if (!confirm('Delete this document?')) return
  await api.delete(`/knowledge/${bid}/documents/${docId}`)
  await loadDocs()
}

onMounted(loadDocs)
</script>
