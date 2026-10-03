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
        <div class="flex flex-wrap gap-2">
          <button @click="showUrlModal = true" class="inline-flex items-center gap-2 rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition hover:border-blue-200 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
            <svg class="h-4 w-4 text-blue-600" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M10 13a5 5 0 0 0 7.1 0l3-3A5 5 0 0 0 13 2.9l-1.7 1.7m2.7 6.4a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7"/></svg>
            Add a URL
          </button>
          <label class="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-within:outline-none focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2" :class="uploading ? 'pointer-events-none opacity-60' : ''">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0L7 9m5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>
            {{ uploading ? 'Uploading…' : 'Upload a file' }}
            <input type="file" class="sr-only" accept=".pdf,.docx,.txt" :disabled="uploading" @change="handleFileUpload" />
          </label>
        </div>
      </header>

      <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <article v-for="item in summary" :key="item.label" class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5">
          <p class="text-xs font-medium text-stone-500 sm:text-sm">{{ item.label }}</p>
          <p class="mt-2 text-2xl font-bold tracking-tight text-stone-900">{{ item.value }}</p>
        </article>
      </div>

      <div v-if="notice.message" class="flex items-start gap-3 rounded-xl border px-4 py-3 text-sm" :class="notice.type === 'error' ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'" role="status" aria-live="polite">
        <svg class="mt-0.5 h-4 w-4 shrink-0" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path v-if="notice.type === 'error'" stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M10.3 4.5 2.9 17.3A1.8 1.8 0 0 0 4.5 20h15a1.8 1.8 0 0 0 1.6-2.7L13.7 4.5a2 2 0 0 0-3.4 0Z"/><path v-else stroke-linecap="round" stroke-linejoin="round" d="m5 12 4 4L19 6"/></svg>
        <span>{{ notice.message }}</span>
        <button @click="notice.message = ''" class="ml-auto rounded p-0.5 text-current/70 hover:text-current" aria-label="Dismiss message"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" d="m6 6 12 12M18 6 6 18"/></svg></button>
      </div>

      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label="Knowledge documents">
        <div class="flex flex-col gap-4 border-b border-stone-100 p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 class="text-base font-semibold text-stone-900">Your sources</h2>
            <p class="mt-1 text-sm text-stone-500">Documents are processed into searchable knowledge for your assistant.</p>
          </div>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div class="relative sm:w-64">
              <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" d="m16 16 4 4"/></svg>
              <input v-model="searchQuery" type="search" aria-label="Search knowledge sources" placeholder="Search sources" class="w-full rounded-xl border border-stone-200 py-2 pl-9 pr-3 text-sm outline-none transition placeholder:text-stone-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100" />
            </div>
            <select v-model="statusFilter" aria-label="Filter sources by status" class="rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100">
              <option value="">All statuses</option><option value="ready">Ready</option><option value="processing">Processing</option><option value="pending">Pending</option><option value="failed">Failed</option>
            </select>
          </div>
        </div>

        <div v-if="loading" class="divide-y divide-stone-100" aria-label="Loading sources" aria-live="polite">
          <div v-for="n in 4" :key="n" class="flex items-center gap-4 px-4 py-4 sm:px-5"><div class="h-10 w-10 animate-pulse rounded-xl bg-stone-100"></div><div class="flex-1 space-y-2"><div class="h-4 w-48 max-w-full animate-pulse rounded bg-stone-100"></div><div class="h-3 w-28 animate-pulse rounded bg-stone-100"></div></div><div class="h-6 w-16 animate-pulse rounded-full bg-stone-100"></div></div>
        </div>
        <div v-else-if="loadError" class="px-6 py-14 text-center">
          <p class="text-sm font-semibold text-stone-800">Couldn’t load your sources</p><p class="mt-1 text-sm text-stone-500">Check your connection and try again.</p>
          <button @click="loadDocs" class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">Try again</button>
        </div>
        <div v-else-if="filteredDocuments.length" class="divide-y divide-stone-100">
          <article v-for="doc in filteredDocuments" :key="doc.id" class="flex flex-col gap-3 px-4 py-4 transition hover:bg-blue-50/40 sm:flex-row sm:items-center sm:gap-4 sm:px-5">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="doc.status === 'failed' ? 'bg-rose-50 text-rose-600' : 'bg-blue-50 text-blue-600'">
              <svg v-if="isUrl(doc)" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M10 13a5 5 0 0 0 7.1 0l3-3A5 5 0 0 0 13 2.9l-1.7 1.7m2.7 6.4a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7"/></svg>
              <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm7 0v5h5M9 13h6m-6 4h6"/></svg>
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-semibold text-stone-900">{{ doc.title || 'Untitled source' }}</p>
              <p class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-stone-500"><span class="uppercase">{{ doc.file_type || (isUrl(doc) ? 'URL' : 'File') }}</span><span aria-hidden="true">·</span><span>{{ doc.chunk_count ?? 0 }} chunks</span><span aria-hidden="true">·</span><span>{{ formatDate(doc.created_at) }}</span></p>
              <p v-if="doc.status === 'failed' && doc.error_message" class="mt-2 text-xs text-rose-600">{{ doc.error_message }}</p>
            </div>
            <div class="flex items-center justify-between gap-3 sm:justify-end">
              <span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold capitalize" :class="statusClass(doc.status)"><span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass(doc.status)"></span>{{ doc.status }}</span>
              <button @click="deleteDoc(doc.id)" :disabled="deletingId === doc.id" class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-stone-500 transition hover:bg-rose-50 hover:text-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-300 disabled:opacity-50">{{ deletingId === doc.id ? 'Deleting…' : 'Delete' }}</button>
            </div>
          </article>
        </div>
        <div v-else class="px-6 py-16 text-center">
          <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm7 0v5h5M9 13h6m-6 4h6"/></svg></span>
          <p class="mt-4 text-sm font-semibold text-stone-800">{{ documents.length ? 'No matching sources' : 'Your knowledge base is empty' }}</p>
          <p class="mt-1 text-sm text-stone-500">{{ documents.length ? 'Try another search or status filter.' : 'Upload a PDF, DOCX, or text file, or add a web page to get started.' }}</p>
          <button v-if="documents.length" @click="clearFilters" class="mt-4 text-sm font-semibold text-blue-600 hover:text-blue-800">Clear filters</button>
          <div v-else class="mt-5 flex justify-center gap-2"><button @click="showUrlModal = true" class="rounded-lg border border-stone-200 px-3 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50">Add a URL</button><label class="cursor-pointer rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700">Upload file<input type="file" class="sr-only" accept=".pdf,.docx,.txt" :disabled="uploading" @change="handleFileUpload" /></label></div>
        </div>
      </section>
    </div>

    <div v-if="showUrlModal" class="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/45 p-4 backdrop-blur-[2px]" @click.self="closeUrlModal" @keydown.esc="closeUrlModal">
      <section role="dialog" aria-modal="true" aria-labelledby="url-modal-title" class="w-full max-w-lg rounded-2xl border border-stone-200 bg-white p-5 shadow-xl sm:p-6">
        <div class="flex items-start justify-between gap-4"><div><p class="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">Add a source</p><h2 id="url-modal-title" class="mt-1 text-xl font-bold text-stone-900">Import a web page</h2><p class="mt-1 text-sm text-stone-500">Your assistant will use this page as a source when answering questions.</p></div><button @click="closeUrlModal" class="rounded-lg p-2 text-stone-400 hover:bg-stone-100 hover:text-stone-700" aria-label="Close dialog"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" d="m6 6 12 12M18 6 6 18"/></svg></button></div>
        <form class="mt-5 space-y-4" @submit.prevent="handleUrlAdd">
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Page URL</span><input v-model="urlInput" type="url" required placeholder="https://docs.example.com/faq" class="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label>
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Source title <span class="font-normal text-stone-400">(optional)</span></span><input v-model="urlTitle" type="text" placeholder="Help center FAQ" class="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none transition placeholder:text-stone-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label>
          <p v-if="urlError" class="text-sm text-rose-600" role="alert">{{ urlError }}</p>
          <div class="flex justify-end gap-2 border-t border-stone-100 pt-4"><button type="button" @click="closeUrlModal" class="rounded-xl px-4 py-2.5 text-sm font-semibold text-stone-600 hover:bg-stone-100">Cancel</button><button type="submit" :disabled="addingUrl" class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{{ addingUrl ? 'Adding…' : 'Add source' }}</button></div>
        </form>
      </section>
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
const loading = ref(true)
const loadError = ref(false)
const showUrlModal = ref(false)
const addingUrl = ref(false)
const deletingId = ref(null)
const searchQuery = ref('')
const statusFilter = ref('')
const urlInput = ref('')
const urlTitle = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const documentToDelete = ref(null)
const deletingId = ref(null)

const bid = computed(() => businessStore.currentBusiness?.id)
const filteredDocuments = computed(() => documents.value.filter((doc) => {
  const matchesStatus = !statusFilter.value || doc.status === statusFilter.value
  const matchesSearch = !searchQuery.value.trim() || (doc.title || '').toLowerCase().includes(searchQuery.value.trim().toLowerCase())
  return matchesStatus && matchesSearch
}))
const summary = computed(() => [
  { label: 'Total sources', value: documents.value.length },
  { label: 'Ready to use', value: documents.value.filter((doc) => doc.status === 'ready').length },
  { label: 'Processing', value: documents.value.filter((doc) => ['processing', 'pending'].includes(doc.status)).length },
  { label: 'Needs attention', value: documents.value.filter((doc) => doc.status === 'failed').length },
])

function statusClass(status) {
  const map = { ready: 'bg-emerald-50 text-emerald-700', processing: 'bg-blue-50 text-blue-700', pending: 'bg-amber-50 text-amber-700', failed: 'bg-rose-50 text-rose-700' }
  return map[status] || 'bg-stone-100 text-stone-600'
}

function statusDotClass(status) {
  const map = { ready: 'bg-emerald-500', processing: 'bg-blue-500', pending: 'bg-amber-500', failed: 'bg-rose-500' }
  return map[status] || 'bg-stone-400'
}

function isUrl(doc) {
  return String(doc.file_type || '').toLowerCase() === 'url'
}

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Date unavailable'
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = ''
}

function showNotice(type, message) {
  notice.value = { type, message }
}

function closeUrlModal() {
  if (addingUrl.value) return
  showUrlModal.value = false
  urlError.value = ''
}

async function loadDocs() {
  if (!bid.value) {
    documents.value = []
    loading.value = false
    return
  }
  loading.value = true
  loadError.value = false
  try {
    const { data } = await api.get(`/knowledge/${bid.value}/documents`)
    documents.value = data
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function handleFileUpload(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || !bid.value) return
  uploading.value = true
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    await api.post(`/knowledge/${bid.value}/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    showNotice('success', `${file.name} uploaded. Processing has started.`)
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
    await api.post(`/knowledge/${bid.value}/url`, { url: urlInput.value, title: urlTitle.value || null })
    const sourceTitle = urlTitle.value || urlInput.value
    showUrlModal.value = false
    urlInput.value = ''
    urlTitle.value = ''
    showNotice('success', `${sourceTitle} added. Processing has started.`)
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
