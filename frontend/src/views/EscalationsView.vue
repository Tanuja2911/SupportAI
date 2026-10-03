<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-7xl space-y-6">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.16em] text-rose-600">Human follow-up</p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Escalations</h1>
          <p class="mt-1 text-sm text-stone-500">Conversations where the assistant needs a person to step in.</p>
        </div>
        <span class="inline-flex w-fit items-center gap-2 rounded-full border border-rose-100 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700"><span class="h-2 w-2 rounded-full bg-rose-500"></span>{{ filteredEscalations.length }} waiting</span>
      </header>

      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label="Escalated conversations">
        <div class="flex flex-col gap-3 border-b border-stone-100 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
          <div><h2 class="text-base font-semibold text-stone-900">Needs your attention</h2><p class="mt-1 text-sm text-stone-500">Open a conversation to review the customer’s chat.</p></div>
          <label class="relative sm:w-64"><svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" d="m16 16 4 4"/></svg><input v-model="searchQuery" type="search" aria-label="Search escalations" placeholder="Search name or email" class="w-full rounded-xl border border-stone-200 py-2 pl-9 pr-3 text-sm outline-none transition placeholder:text-stone-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label>
        </div>

        <div v-if="loading" class="divide-y divide-stone-100" aria-label="Loading escalations" aria-live="polite">
          <div v-for="n in 4" :key="n" class="flex items-center gap-4 px-4 py-4 sm:px-5"><div class="h-11 w-11 animate-pulse rounded-full bg-stone-100"></div><div class="flex-1 space-y-2"><div class="h-4 w-40 animate-pulse rounded bg-stone-100"></div><div class="h-3 w-56 max-w-full animate-pulse rounded bg-stone-100"></div></div><div class="h-6 w-20 animate-pulse rounded-full bg-stone-100"></div></div>
        </div>
        <div v-else-if="error" class="px-6 py-14 text-center"><p class="text-sm font-semibold text-stone-800">Couldn’t load escalations</p><p class="mt-1 text-sm text-stone-500">Check your connection and try again.</p><button @click="loadEscalations" class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">Try again</button></div>
        <div v-else-if="filteredEscalations.length" class="divide-y divide-stone-100">
          <router-link v-for="conv in filteredEscalations" :key="conv.id" :to="`/app/conversations/${conv.id}`" class="group flex items-center gap-3 px-4 py-4 transition hover:bg-rose-50/40 focus:bg-rose-50 focus:outline-none sm:gap-4 sm:px-5">
            <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-rose-50 text-sm font-bold text-rose-700 ring-1 ring-rose-100">{{ initials(conv.customer_name) }}</span>
            <span class="min-w-0 flex-1"><span class="flex flex-wrap items-center gap-x-2 gap-y-1"><span class="truncate text-sm font-semibold text-stone-900 group-hover:text-rose-700">{{ conv.customer_name || 'Anonymous customer' }}</span><span class="rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700">Escalated</span></span><span class="mt-1 block truncate text-sm text-stone-500">{{ conv.customer_email || 'No email provided' }}</span></span>
            <span class="flex shrink-0 items-center gap-3 text-right"><span class="hidden text-xs text-stone-400 sm:block">{{ formatDate(conv.updated_at) }}</span><span class="whitespace-nowrap rounded-lg bg-stone-100 px-2.5 py-1.5 text-xs font-medium text-stone-600">{{ conv.message_count ?? 0 }} <span class="hidden sm:inline">messages</span><span class="sm:hidden">msg</span></span><svg class="h-4 w-4 text-stone-300 transition group-hover:translate-x-0.5 group-hover:text-rose-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m9 18 6-6-6-6"/></svg></span>
          </router-link>
        </div>
        <div v-else class="px-6 py-16 text-center">
          <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m5 12 4 4L19 6"/></svg></span>
          <p class="mt-4 text-sm font-semibold text-stone-800">{{ escalations.length ? 'No matching escalations' : 'You’re all caught up' }}</p>
          <p class="mt-1 text-sm text-stone-500">{{ escalations.length ? 'Try searching for a different customer.' : 'There are no conversations waiting for human follow-up.' }}</p>
          <button v-if="searchQuery" @click="searchQuery = ''" class="mt-4 text-sm font-semibold text-blue-600 hover:text-blue-800">Clear search</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const escalations = ref([])
const searchQuery = ref('')
const loading = ref(true)
const error = ref(false)

const filteredEscalations = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return escalations.value
  return escalations.value.filter((conv) => `${conv.customer_name || ''} ${conv.customer_email || ''}`.toLowerCase().includes(query))
})

function initials(name) {
  if (!name) return '?'
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part.charAt(0).toUpperCase()).join('')
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

async function loadEscalations() {
  const bid = businessStore.currentBusiness?.id
  if (!bid) {
    escalations.value = []
    loading.value = false
    return
  }
  loading.value = true
  error.value = false
  try {
    const { data } = await api.get(`/conversations/${bid}`, { params: { status: 'escalated' } })
    escalations.value = data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadEscalations)
</script>
