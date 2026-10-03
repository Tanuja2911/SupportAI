<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Knowledge Base</h2>
      <div class="flex gap-3">
        <button
          @click="showUrlModal = true"
          class="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-50 transition"
        >
          Add URL
        </button>
        <label class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition cursor-pointer">
          Upload File
          <input type="file" class="hidden" accept=".pdf,.docx,.txt" @change="handleFileUpload" />
        </label>
      </div>
    </div>

    <div v-if="actionError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
      {{ actionError }}
    </div>
    <div v-if="actionSuccess" class="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700" role="status">
      {{ actionSuccess }}
    </div>

    <div v-if="uploading" class="bg-blue-50 text-blue-700 p-3 rounded-lg mb-4 text-sm">
      Uploading and processing document...
    </div>

    <!-- Documents Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
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
          <tr v-for="doc in documents" :key="doc.id" class="hover:bg-gray-50">
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
              <button type="button" @click="requestDelete(doc)" :disabled="deletingId === doc.id" class="text-red-500 hover:text-red-700 text-sm disabled:cursor-not-allowed disabled:opacity-50">{{ deletingId === doc.id ? 'Deleting…' : 'Delete' }}</button>
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
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <input
          v-model="urlTitle"
          type="text"
          placeholder="Title (optional)"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <p v-if="actionError" class="mb-3 text-sm text-red-400" role="alert">{{ actionError }}</p>
        <div class="flex justify-end gap-3">
          <button @click="showUrlModal = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 text-sm">Cancel</button>
          <button @click="handleUrlAdd" class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">Add</button>
        </div>
      </div>
    </div>

    <ConfirmDialog
      v-if="documentToDelete"
      title="Delete this document?"
      :message="`“${documentToDelete.title}” and its indexed content will be removed from your knowledge base.`"
      :error="actionError"
      confirm-label="Delete document"
      :busy="deletingId !== null"
      @cancel="documentToDelete = null"
      @confirm="deleteDoc"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const documents = ref([])
const uploading = ref(false)
const showUrlModal = ref(false)
const urlInput = ref('')
const urlTitle = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const documentToDelete = ref(null)
const deletingId = ref(null)

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
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    await api.post(`/knowledge/${bid}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await loadDocs()
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Upload failed'
  } finally {
    uploading.value = false
  }
}

async function handleUrlAdd() {
  if (!urlInput.value) return
  actionError.value = ''
  actionSuccess.value = ''
  try {
    await api.post(`/knowledge/${bid}/url`, { url: urlInput.value, title: urlTitle.value || null })
    showUrlModal.value = false
    urlInput.value = ''
    urlTitle.value = ''
    await loadDocs()
    actionSuccess.value = 'URL added to your knowledge base.'
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Failed to add URL'
  }
}

function requestDelete(document) {
  actionError.value = ''
  actionSuccess.value = ''
  documentToDelete.value = document
}

async function deleteDoc() {
  if (!documentToDelete.value || deletingId.value) return
  const document = documentToDelete.value
  deletingId.value = document.id
  actionError.value = ''
  try {
    await api.delete(`/knowledge/${bid}/documents/${document.id}`)
    documentToDelete.value = null
    actionSuccess.value = 'Document deleted from your knowledge base.'
    await loadDocs()
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Failed to delete document'
  } finally {
    deletingId.value = null
  }
}

onMounted(loadDocs)
</script>
