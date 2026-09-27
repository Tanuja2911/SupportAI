<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-6xl space-y-6">
      <header><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Website appearance</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Widget Configuration</h1><p class="mt-1 text-sm text-stone-500">Customize the chat widget customers see on your website.</p></header>
      <div v-if="loading" class="grid gap-5 lg:grid-cols-2" aria-label="Loading widget settings" aria-live="polite"><div class="h-[30rem] animate-pulse rounded-2xl border border-stone-200 bg-white"></div><div class="h-[30rem] animate-pulse rounded-2xl border border-stone-200 bg-white"></div></div>
      <div v-else-if="loadError" class="rounded-2xl border border-stone-200 bg-white px-6 py-14 text-center"><p class="text-sm font-semibold text-stone-800">Couldn’t load widget settings</p><p class="mt-1 text-sm text-stone-500">Check your connection and try again.</p><button @click="loadConfig" class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">Try again</button></div>
      <div v-else-if="config" class="grid items-start gap-5 lg:grid-cols-[1.05fr_.95fr]">
        <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm"><div class="border-b border-stone-100 p-5 sm:p-6"><h2 class="text-base font-semibold text-stone-900">Appearance and behavior</h2><p class="mt-1 text-sm text-stone-500">Changes apply to the widget wherever it is embedded.</p></div><form class="space-y-5 p-5 sm:p-6" @submit.prevent="saveConfig">
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Assistant name</span><input v-model="config.bot_name" required maxlength="60" class="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label>
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Welcome message</span><textarea v-model="config.welcome_message" required rows="3" maxlength="500" class="w-full resize-y rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm leading-6 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"></textarea><span class="mt-1 block text-right text-xs text-stone-400">{{ config.welcome_message?.length || 0 }}/500</span></label>
          <div><p class="mb-1.5 text-sm font-medium text-stone-700">Brand color</p><div class="flex items-center gap-3"><input v-model="config.primary_color" type="color" aria-label="Choose brand color" class="h-11 w-12 cursor-pointer rounded-lg border border-stone-200 bg-white p-1"/><input v-model="config.primary_color" aria-label="Brand color hex value" pattern="^#[0-9A-Fa-f]{6}$" class="w-32 rounded-xl border border-stone-200 px-3 py-2.5 font-mono text-sm uppercase outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"/><span class="text-xs text-stone-400">Used on the chat header and buttons</span></div></div>
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Widget position</span><select v-model="config.position" class="w-full rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"><option value="bottom-right">Bottom right</option><option value="bottom-left">Bottom left</option></select></label>
          <label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Input placeholder</span><input v-model="config.placeholder_text" maxlength="100" class="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label>
          <label class="flex items-start gap-3 rounded-xl border border-stone-200 p-4"><input v-model="config.show_branding" type="checkbox" class="mt-0.5 h-4 w-4 rounded border-stone-300 text-blue-600 focus:ring-blue-500"/><span><span class="block text-sm font-semibold text-stone-800">Show SupportAI branding</span><span class="mt-1 block text-xs leading-5 text-stone-500">Display a small “Powered by SupportAI” note in the widget.</span></span></label>
          <div v-if="notice" class="rounded-xl border px-4 py-3 text-sm" :class="saveError ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'" role="status">{{ notice }}</div>
          <button type="submit" :disabled="saving" class="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-60">{{ saving ? 'Saving changes…' : 'Save configuration' }}</button>
        </form></section>
        <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm"><div class="border-b border-stone-100 p-5 sm:p-6"><h2 class="text-base font-semibold text-stone-900">Live preview</h2><p class="mt-1 text-sm text-stone-500">A preview of your chat widget’s appearance.</p></div><div class="bg-gradient-to-br from-blue-50 to-stone-100 p-5 sm:p-8"><div class="mx-auto max-w-sm overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-xl"><div class="flex items-center gap-3 px-4 py-4 text-white" :style="{ backgroundColor: config.primary_color }"><span class="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/></svg></span><span class="min-w-0"><span class="block truncate text-sm font-semibold">{{ config.bot_name || 'Support Assistant' }}</span><span class="mt-0.5 flex items-center gap-1.5 text-xs text-white/80"><span class="h-1.5 w-1.5 rounded-full bg-emerald-300"></span>Typically replies instantly</span></span></div><div class="min-h-56 space-y-4 bg-stone-50 p-4"><div class="max-w-[88%] rounded-2xl rounded-tl-md border border-stone-100 bg-white p-3.5 text-sm leading-6 text-stone-700 shadow-sm">{{ config.welcome_message }}</div><div class="ml-auto max-w-[80%] rounded-2xl rounded-tr-md px-3.5 py-2.5 text-sm text-white" :style="{ backgroundColor: config.primary_color }">How can I get started?</div></div><div class="border-t border-stone-100 p-3"><div class="flex items-center gap-2 rounded-xl border border-stone-200 bg-white px-3 py-2.5"><span class="flex-1 text-sm text-stone-400">{{ config.placeholder_text }}</span><span class="flex h-8 w-8 items-center justify-center rounded-lg text-white" :style="{ backgroundColor: config.primary_color }"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m5 12 14-7-4 14-3-6-7-1Z"/></svg></span></div><p v-if="config.show_branding" class="mt-2 text-center text-[10px] text-stone-400">Powered by SupportAI</p></div></div><p class="mt-4 text-center text-xs text-stone-500">Position: {{ config.position === 'bottom-left' ? 'bottom left' : 'bottom right' }}</p></div></section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const config = ref(null)
const saving = ref(false)
const loading = ref(true)
const loadError = ref(false)
const notice = ref('')
const saveError = ref(false)
const bid = businessStore.currentBusiness?.id

async function loadConfig() {
  if (!bid) { loading.value = false; return }
  loading.value = true; loadError.value = false
  try { const { data } = await api.get(`/widget/${bid}/config`); config.value = data }
  catch { loadError.value = true }
  finally { loading.value = false }
}

async function saveConfig() {
  if (!bid || saving.value) return
  saving.value = true; notice.value = ''
  try { const { data } = await api.put(`/widget/${bid}/config`, config.value); config.value = data; notice.value = 'Widget configuration saved.'; saveError.value = false }
  catch (err) { notice.value = err.response?.data?.detail || 'Could not save your changes. Please try again.'; saveError.value = true }
  finally { saving.value = false }
}

onMounted(loadConfig)
</script>
