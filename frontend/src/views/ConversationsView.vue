<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-7xl space-y-6">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Support inbox</p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Conversations</h1>
          <p class="mt-1 text-sm text-stone-500">Review customer chats and follow up on conversations that need attention.</p>
        </div>
        <span class="inline-flex w-fit items-center gap-2 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-600">
          <span class="h-2 w-2 rounded-full bg-blue-500"></span>{{ resultLabel }}
        </span>
      </header>

      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label="Conversation list">
        <div class="border-b border-stone-100 p-4 sm:p-5">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="relative w-full lg:max-w-sm">
              <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" d="m16 16 4 4"/></svg>
              <input v-model="searchQuery" type="search" aria-label="Search conversations" placeholder="Search name or email" class="w-full rounded-xl border border-stone-200 bg-white py-2.5 pl-10 pr-3 text-sm text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100" />
            </div>
            <div class="flex gap-2 overflow-x-auto pb-1 lg:pb-0" aria-label="Filter conversations by status">
              <button v-for="filter in filters" :key="filter.value" @click="activeFilter = filter.value" :aria-pressed="activeFilter === filter.value" class="shrink-0 rounded-lg px-3 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1" :class="activeFilter === filter.value ? 'bg-blue-600 text-white shadow-sm' : 'border border-stone-200 bg-white text-stone-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700'">
                {{ filter.label }}<span v-if="filter.value === ''" class="ml-1.5 text-xs" :class="activeFilter === filter.value ? 'text-blue-100' : 'text-stone-400'">{{ conversations.length }}</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="loading" class="divide-y divide-stone-100" aria-label="Loading conversations" aria-live="polite">
          <div v-for="n in 5" :key="n" class="flex items-center gap-4 px-4 py-4 sm:px-5">
            <div class="h-11 w-11 animate-pulse rounded-full bg-stone-100"></div>
            <div class="min-w-0 flex-1 space-y-2"><div class="h-4 w-36 animate-pulse rounded bg-stone-100"></div><div class="h-3 w-52 max-w-full animate-pulse rounded bg-stone-100"></div></div>
            <div class="h-6 w-20 animate-pulse rounded-full bg-stone-100"></div>
          </div>
        </div>

        <div v-else-if="error" class="px-6 py-14 text-center">
          <p class="text-sm font-semibold text-stone-800">Couldn’t load conversations</p>
          <p class="mt-1 text-sm text-stone-500">Check your connection and try again.</p>
          <button @click="loadConversations" class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">Try again</button>
        </div>

        <div v-else-if="filteredConversations.length" class="divide-y divide-stone-100">
          <router-link v-for="conv in filteredConversations" :key="conv.id" :to="`/app/conversations/${conv.id}`" class="group flex items-center gap-3 px-4 py-4 transition hover:bg-blue-50/70 focus:bg-blue-50 focus:outline-none sm:gap-4 sm:px-5">
            <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-50 text-sm font-bold text-blue-700 ring-1 ring-blue-100">{{ initials(conv.customer_name) }}</span>
            <span class="min-w-0 flex-1">
              <span class="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span class="truncate text-sm font-semibold text-stone-900 group-hover:text-blue-700">{{ conv.customer_name || 'Anonymous customer' }}</span>
                <span class="rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize" :class="statusClass(conv.status)">{{ conv.status || 'Unknown' }}</span>
              </span>
              <span class="mt-1 block truncate text-sm text-stone-500">{{ conv.customer_email || 'No email provided' }}</span>
            </span>
            <span class="flex shrink-0 items-center gap-3 text-right">
              <span class="hidden text-xs text-stone-400 sm:block">{{ formatDate(conv.updated_at || conv.created_at) }}</span>
              <span class="whitespace-nowrap rounded-lg bg-stone-100 px-2.5 py-1.5 text-xs font-medium text-stone-600">{{ conv.message_count ?? 0 }} <span class="hidden sm:inline">messages</span><span class="sm:hidden">msg</span></span>
              <svg class="h-4 w-4 text-stone-300 transition group-hover:translate-x-0.5 group-hover:text-blue-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m9 18 6-6-6-6"/></svg>
            </span>
          </router-link>
        </div>

        <div v-else class="px-6 py-16 text-center">
          <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/><path stroke-linecap="round" d="M8 10h7M8 13.5h5"/></svg>
          </span>
          <p class="mt-4 text-sm font-semibold text-stone-800">{{ emptyTitle }}</p>
          <p class="mt-1 text-sm text-stone-500">{{ emptyMessage }}</p>
          <button v-if="searchQuery || activeFilter" @click="clearFilters" class="mt-4 text-sm font-semibold text-blue-600 hover:text-blue-800">Clear filters</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const conversations = ref([])
const activeFilter = ref('')
const searchQuery = ref('')
const loading = ref(true)
const error = ref(false)

const filters = [
  { label: 'All', value: '' },
  { label: 'Active', value: 'active' },
  { label: 'Escalated', value: 'escalated' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Closed', value: 'closed' },
]

const filteredConversations = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return conversations.value
  return conversations.value.filter((conv) =>
    `${conv.customer_name || ''} ${conv.customer_email || ''}`.toLowerCase().includes(query),
  )
})

const resultLabel = computed(() => `${filteredConversations.value.length} ${filteredConversations.value.length === 1 ? 'conversation' : 'conversations'}`)
const emptyTitle = computed(() => conversations.value.length ? 'No matching conversations' : 'No conversations yet')
const emptyMessage = computed(() => conversations.value.length
  ? 'Try a different search or status filter.'
  : 'New customer chats will show up here when they arrive.')

function statusClass(status) {
  const map = {
    active: 'bg-emerald-50 text-emerald-700',
    escalated: 'bg-rose-50 text-rose-700',
    resolved: 'bg-blue-50 text-blue-700',
    closed: 'bg-stone-100 text-stone-600',
  }
  return map[status] || 'bg-stone-100 text-stone-600'
}

function initials(name) {
  if (!name) return '?'
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part.charAt(0).toUpperCase()).join('')
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date)
}

function clearFilters() {
  searchQuery.value = ''
  activeFilter.value = ''
}

async function loadConversations() {
  const bid = businessStore.currentBusiness?.id
  if (!bid) {
    conversations.value = []
    loading.value = false
    return
  }
  loading.value = true
  error.value = false
  try {
    const params = activeFilter.value ? { status: activeFilter.value } : {}
    const { data } = await api.get(`/conversations/${bid}`, { params })
    conversations.value = data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

watch(activeFilter, loadConversations)
onMounted(loadConversations)
</script>
