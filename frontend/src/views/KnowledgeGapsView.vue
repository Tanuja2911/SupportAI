<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-7xl space-y-6">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Improve your coverage</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Knowledge Gaps</h1><p class="mt-1 text-sm text-stone-500">Topics customers ask about that your current sources don’t cover well.</p></div>
        <button @click="analyze" :disabled="analyzing" class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"><svg v-if="!analyzing" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v3m0 12v3m9-9h-3M6 12H3m15.36-6.36-2.12 2.12M7.76 16.24l-2.12 2.12m12.72 0-2.12-2.12M7.76 7.76 5.64 5.64"/></svg>{{ analyzing ? 'Analyzing…' : 'Run analysis' }}</button>
      </header>

      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <article class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Total topics</p><p class="mt-2 text-2xl font-bold text-stone-900">{{ gaps.length }}</p></article>
        <article class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Open</p><p class="mt-2 text-2xl font-bold text-blue-700">{{ openGaps.length }}</p></article>
        <article class="col-span-2 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:col-span-1 sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Resolved</p><p class="mt-2 text-2xl font-bold text-emerald-700">{{ gaps.length - openGaps.length }}</p></article>
      </div>

      <div class="rounded-2xl border border-blue-100 bg-white p-4 sm:p-5"><div class="flex gap-3"><span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 18h6m-5 3h4m-4-6.5a6 6 0 1 1 4 0c-.7.5-1 1.2-1 2h-2c0-.8-.3-1.5-1-2Z"/></svg></span><div><p class="text-sm font-semibold text-stone-900">How gap analysis works</p><p class="mt-1 text-sm leading-6 text-stone-500">Analysis looks at low-confidence answers and escalated conversations to identify topics your sources may be missing. Run it again as new conversations come in.</p></div></div></div>

      <div v-if="resultMsg" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">{{ resultMsg }}</div>
      <div v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" role="alert">{{ error }}</div>

      <section class="space-y-3" aria-label="Detected knowledge gaps">
        <div v-if="loading" class="space-y-3" aria-label="Loading knowledge gaps" aria-live="polite"><div v-for="n in 3" :key="n" class="h-40 animate-pulse rounded-2xl border border-stone-200 bg-white"></div></div>
        <article v-for="gap in gaps" v-show="!loading" :key="gap.id" class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5" :class="gap.status === 'resolved' ? 'opacity-75' : ''">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2"><h2 class="text-base font-semibold text-stone-900">{{ gap.topic }}</h2><span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="gap.status === 'resolved' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'">{{ gap.status === 'resolved' ? 'Resolved' : 'Open' }}</span><span class="text-xs text-stone-400">{{ gap.query_count }} {{ gap.query_count === 1 ? 'query' : 'queries' }}</span></div>
              <p class="mt-2 text-sm leading-6 text-stone-600">{{ gap.description }}</p>
              <div class="mt-4 rounded-xl border border-blue-100 bg-blue-50/70 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-blue-700">Suggested next step</p><p class="mt-1 text-sm leading-6 text-stone-700">{{ gap.suggestion }}</p></div>
              <div v-if="gap.sample_queries?.length" class="mt-4"><p class="mb-2 text-xs font-semibold text-stone-500">Example customer questions</p><div class="flex flex-wrap gap-2"><span v-for="(query, index) in gap.sample_queries.slice(0, 5)" :key="index" class="rounded-lg border border-stone-200 bg-stone-50 px-2.5 py-1.5 text-xs text-stone-600">“{{ query }}”</span></div></div>
            </div>
            <button v-if="gap.status !== 'resolved'" @click="resolve(gap.id)" :disabled="resolvingId === gap.id" class="shrink-0 rounded-xl border border-emerald-200 px-3.5 py-2 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50 disabled:opacity-50">{{ resolvingId === gap.id ? 'Saving…' : 'Mark resolved' }}</button>
          </div>
        </article>
        <div v-if="!loading && !gaps.length" class="rounded-2xl border border-stone-200 bg-white px-6 py-16 text-center"><span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 18h6m-5 3h4m-4-6.5a6 6 0 1 1 4 0c-.7.5-1 1.2-1 2h-2c0-.8-.3-1.5-1-2Z"/></svg></span><p class="mt-4 text-sm font-semibold text-stone-800">No knowledge gaps detected yet</p><p class="mt-1 text-sm text-stone-500">Run an analysis after your assistant has handled some conversations.</p></div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const bid = businessStore.currentBusiness?.id
const gaps = ref([])
const analyzing = ref(false)
const loading = ref(true)
const error = ref('')
const resultMsg = ref('')
const resolvingId = ref(null)
const openGaps = computed(() => gaps.value.filter((gap) => gap.status !== 'resolved'))

async function loadGaps() {
  if (!bid) { loading.value = false; return }
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/knowledge-gaps/${bid}`)
    gaps.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load knowledge gaps. Please try again.'
  } finally { loading.value = false }
}

async function analyze() {
  if (!bid || analyzing.value) return
  analyzing.value = true
  resultMsg.value = ''
  error.value = ''
  try {
    const { data } = await api.post(`/knowledge-gaps/${bid}/analyze`)
    resultMsg.value = data.message
    await loadGaps()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Analysis failed. Make sure you have conversations and an API key configured.'
  } finally { analyzing.value = false }
}

async function resolve(gapId) {
  resolvingId.value = gapId
  error.value = ''
  try {
    await api.patch(`/knowledge-gaps/${bid}/${gapId}`)
    await loadGaps()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not update this topic. Please try again.'
  } finally { resolvingId.value = null }
}

onMounted(loadGaps)
</script>
