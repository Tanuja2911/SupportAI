<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-7xl space-y-6">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Precise answers</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">FAQ Overrides</h1><p class="mt-1 text-sm text-stone-500">Set exact answers for common questions. These take priority over generated answers.</p></div>
        <div class="flex flex-wrap gap-2"><button @click="autoGenerate" :disabled="generating" class="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition hover:border-blue-200 hover:bg-blue-50 disabled:opacity-60">{{ generating ? 'Generating…' : 'Suggest FAQs' }}</button><button @click="showModal = true" class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700">Add FAQ</button></div>
      </header>

      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3"><article class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Published answers</p><p class="mt-2 text-2xl font-bold text-stone-900">{{ faqs.length }}</p></article><article class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Suggestions to review</p><p class="mt-2 text-2xl font-bold text-blue-700">{{ suggestions.length }}</p></article><article class="col-span-2 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:col-span-1 sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Answer mode</p><p class="mt-2 text-sm font-semibold text-stone-800">Exact match priority</p></article></div>

      <div v-if="genError" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" role="alert">{{ genError }}</div>
      <div v-if="actionMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">{{ actionMessage }}</div>

      <section v-if="suggestions.length" class="overflow-hidden rounded-2xl border border-blue-200 bg-white shadow-sm">
        <div class="flex flex-col gap-3 border-b border-blue-100 bg-blue-50/70 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5"><div><h2 class="text-base font-semibold text-stone-900">AI suggestions</h2><p class="mt-1 text-sm text-stone-500">Review these draft answers before adding them to your FAQ.</p></div><div class="flex gap-2"><button @click="acceptAll" :disabled="acceptingAll" class="rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60">{{ acceptingAll ? 'Adding…' : `Accept all (${suggestions.length})` }}</button><button @click="suggestions = []" class="rounded-lg border border-stone-200 bg-white px-3 py-2 text-xs font-semibold text-stone-600 hover:bg-stone-50">Dismiss</button></div></div>
        <div class="divide-y divide-stone-100"><article v-for="(suggestion, index) in suggestions" :key="index" class="flex flex-col gap-4 p-4 sm:flex-row sm:items-start sm:justify-between sm:p-5"><div class="min-w-0 flex-1"><p class="text-xs font-semibold uppercase tracking-wide text-blue-600">Suggested question</p><p class="mt-1 text-sm font-semibold text-stone-900">{{ suggestion.question }}</p><p class="mt-4 text-xs font-semibold uppercase tracking-wide text-stone-400">Draft answer</p><p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-stone-600">{{ suggestion.answer }}</p></div><div class="flex shrink-0 gap-2"><button @click="acceptSuggestion(index)" class="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700">Accept</button><button @click="suggestions.splice(index, 1)" class="rounded-lg border border-stone-200 px-3 py-2 text-xs font-semibold text-stone-600 hover:bg-stone-50">Dismiss</button></div></article></div>
      </section>

      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label="FAQ answers">
        <div class="flex flex-col gap-3 border-b border-stone-100 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5"><div><h2 class="text-base font-semibold text-stone-900">Published FAQs</h2><p class="mt-1 text-sm text-stone-500">{{ faqs.length }} exact {{ faqs.length === 1 ? 'answer' : 'answers' }} configured</p></div><label class="relative sm:w-64"><svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" d="m16 16 4 4"/></svg><input v-model="searchQuery" type="search" aria-label="Search FAQs" placeholder="Search questions" class="w-full rounded-xl border border-stone-200 py-2 pl-9 pr-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label></div>
        <div v-if="loading" class="divide-y divide-stone-100" aria-label="Loading FAQs" aria-live="polite"><div v-for="n in 3" :key="n" class="space-y-3 p-5"><div class="h-4 w-56 animate-pulse rounded bg-stone-100"></div><div class="h-3 w-full animate-pulse rounded bg-stone-100"></div><div class="h-3 w-2/3 animate-pulse rounded bg-stone-100"></div></div></div>
        <div v-else-if="filteredFaqs.length" class="divide-y divide-stone-100"><article v-for="faq in filteredFaqs" :key="faq.id" class="flex flex-col gap-3 p-4 sm:flex-row sm:items-start sm:justify-between sm:p-5"><div class="min-w-0 flex-1"><p class="text-xs font-semibold uppercase tracking-wide text-blue-600">Question</p><p class="mt-1 text-sm font-semibold text-stone-900">{{ faq.question }}</p><p class="mt-4 text-xs font-semibold uppercase tracking-wide text-stone-400">Exact answer</p><p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-stone-600">{{ faq.answer }}</p></div><button @click="deleteFaq(faq.id)" class="self-start rounded-lg px-3 py-2 text-xs font-semibold text-stone-500 transition hover:bg-rose-50 hover:text-rose-700">Delete</button></article></div>
        <div v-else class="px-6 py-14 text-center"><span class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9.5 9a2.6 2.6 0 1 1 4.2 2.1c-1 .7-1.7 1.1-1.7 2.4m0 3h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg></span><p class="mt-4 text-sm font-semibold text-stone-800">{{ faqs.length ? 'No matching FAQs' : 'No FAQ overrides yet' }}</p><p class="mt-1 text-sm text-stone-500">{{ faqs.length ? 'Try a different search.' : 'Add an exact answer or generate suggestions from your documents.' }}</p><button v-if="!faqs.length && !suggestions.length" @click="showModal = true" class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">Add your first FAQ</button><button v-else-if="searchQuery" @click="searchQuery = ''" class="mt-4 text-sm font-semibold text-blue-600">Clear search</button></div>
      </section>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/45 p-4 backdrop-blur-[2px]" @click.self="showModal = false"><section role="dialog" aria-modal="true" aria-labelledby="faq-dialog-title" class="w-full max-w-lg rounded-2xl border border-stone-200 bg-white p-5 shadow-xl sm:p-6"><div class="flex items-start justify-between"><div><p class="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">New exact answer</p><h2 id="faq-dialog-title" class="mt-1 text-xl font-bold text-stone-900">Add FAQ override</h2><p class="mt-1 text-sm text-stone-500">Choose the question and response your assistant should use.</p></div><button @click="showModal = false" class="rounded-lg p-2 text-stone-400 hover:bg-stone-100" aria-label="Close dialog">×</button></div><form class="mt-5 space-y-4" @submit.prevent="addFaq"><label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Customer question</span><input v-model="newQuestion" required placeholder="How do I reset my password?" class="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label><label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Exact answer</span><textarea v-model="newAnswer" required rows="5" placeholder="Write the answer exactly as customers should receive it…" class="w-full resize-y rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"></textarea></label><div class="flex justify-end gap-2 border-t border-stone-100 pt-4"><button type="button" @click="showModal = false" class="rounded-xl px-4 py-2.5 text-sm font-semibold text-stone-600 hover:bg-stone-100">Cancel</button><button type="submit" class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">Add FAQ</button></div></form></section></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const faqs = ref([])
const showModal = ref(false)
const newQuestion = ref('')
const newAnswer = ref('')
const suggestions = ref([])
const generating = ref(false)
const acceptingAll = ref(false)
const loading = ref(true)
const genError = ref('')
const actionMessage = ref('')
const searchQuery = ref('')
const bid = businessStore.currentBusiness?.id
const filteredFaqs = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return faqs.value
  return faqs.value.filter((faq) => `${faq.question} ${faq.answer}`.toLowerCase().includes(query))
})

async function loadFaqs() {
  if (!bid) { loading.value = false; return }
  loading.value = true
  try { const { data } = await api.get(`/faq/${bid}`); faqs.value = data }
  catch (err) { genError.value = err.response?.data?.detail || 'Could not load FAQs. Please try again.' }
  finally { loading.value = false }
}

async function addFaq() {
  if (!newQuestion.value.trim() || !newAnswer.value.trim()) return
  try {
    await api.post(`/faq/${bid}`, { question: newQuestion.value.trim(), answer: newAnswer.value.trim() })
    showModal.value = false
    newQuestion.value = ''; newAnswer.value = ''
    actionMessage.value = 'FAQ added.'
    await loadFaqs()
  } catch (err) { genError.value = err.response?.data?.detail || 'Could not add this FAQ.' }
}

async function deleteFaq(faqId) {
  if (!window.confirm('Delete this FAQ?')) return
  try { await api.delete(`/faq/${bid}/${faqId}`); actionMessage.value = 'FAQ deleted.'; await loadFaqs() }
  catch (err) { genError.value = err.response?.data?.detail || 'Could not delete this FAQ.' }
}

async function autoGenerate() {
  generating.value = true; genError.value = ''; actionMessage.value = ''; suggestions.value = []
  try { const { data } = await api.post(`/faq/${bid}/auto-generate`); suggestions.value = data.suggestions }
  catch (err) { genError.value = err.response?.data?.detail || 'Failed to generate FAQs. Make sure you have processed documents and an API key configured.' }
  finally { generating.value = false }
}

async function acceptSuggestion(index) {
  const suggestion = suggestions.value[index]
  try { await api.post(`/faq/${bid}`, { question: suggestion.question, answer: suggestion.answer }); suggestions.value.splice(index, 1); actionMessage.value = 'Suggested FAQ added.'; await loadFaqs() }
  catch (err) { genError.value = err.response?.data?.detail || 'Could not add this suggestion.' }
}

async function acceptAll() {
  acceptingAll.value = true; genError.value = ''
  try {
    for (const suggestion of [...suggestions.value]) await api.post(`/faq/${bid}`, { question: suggestion.question, answer: suggestion.answer })
    suggestions.value = []; actionMessage.value = 'All suggestions added.'; await loadFaqs()
  } catch (err) { genError.value = err.response?.data?.detail || 'Could not add all suggestions. You can accept the remaining suggestions individually.'; await loadFaqs() }
  finally { acceptingAll.value = false }
}

onMounted(loadFaqs)
</script>
