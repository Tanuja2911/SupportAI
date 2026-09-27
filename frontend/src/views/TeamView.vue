<template>
  <div class="min-h-full bg-blue-50 px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
    <div class="mx-auto max-w-7xl space-y-6">
      <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Workspace access</p><h1 class="mt-2 text-3xl font-bold tracking-tight text-stone-900">Team</h1><p class="mt-1 text-sm text-stone-500">Manage who can view and support your customers.</p></div><button @click="showModal = true" class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700">Invite a member</button></header>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3"><article class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Team members</p><p class="mt-2 text-2xl font-bold text-stone-900">{{ members.length }}</p></article><article class="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Agents</p><p class="mt-2 text-2xl font-bold text-blue-700">{{ members.filter((member) => member.role === 'agent').length }}</p></article><article class="col-span-2 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:col-span-1 sm:p-5"><p class="text-xs font-medium text-stone-500 sm:text-sm">Viewers</p><p class="mt-2 text-2xl font-bold text-stone-700">{{ members.filter((member) => member.role === 'viewer').length }}</p></article></div>
      <div v-if="message" class="rounded-xl border px-4 py-3 text-sm" :class="error ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'" role="status">{{ message }}</div>
      <section class="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm" aria-label="Team members"><div class="border-b border-stone-100 p-4 sm:p-5"><h2 class="text-base font-semibold text-stone-900">Members</h2><p class="mt-1 text-sm text-stone-500">Owners manage settings, agents reply to conversations, viewers have read-only access.</p></div>
        <div v-if="loading" class="divide-y divide-stone-100" aria-label="Loading team members" aria-live="polite"><div v-for="n in 3" :key="n" class="flex items-center gap-4 px-4 py-4 sm:px-5"><div class="h-11 w-11 animate-pulse rounded-full bg-stone-100"></div><div class="flex-1 space-y-2"><div class="h-4 w-40 animate-pulse rounded bg-stone-100"></div><div class="h-3 w-52 animate-pulse rounded bg-stone-100"></div></div><div class="h-6 w-16 animate-pulse rounded-full bg-stone-100"></div></div></div>
        <div v-else-if="loadError" class="px-6 py-14 text-center"><p class="text-sm font-semibold text-stone-800">Couldn’t load team members</p><button @click="loadMembers" class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">Try again</button></div>
        <div v-else-if="members.length" class="divide-y divide-stone-100"><article v-for="member in members" :key="member.id" class="flex items-center gap-3 px-4 py-4 sm:gap-4 sm:px-5"><span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-50 text-sm font-bold text-blue-700 ring-1 ring-blue-100">{{ initials(member.full_name || member.email) }}</span><span class="min-w-0 flex-1"><span class="block truncate text-sm font-semibold text-stone-900">{{ member.full_name || 'Team member' }}</span><span class="mt-1 block truncate text-sm text-stone-500">{{ member.email }}</span></span><span class="rounded-full px-2.5 py-1 text-xs font-semibold capitalize" :class="roleClass(member.role)">{{ member.role }}</span><button v-if="member.role !== 'owner'" @click="removeMember(member.id)" :disabled="removingId === member.id" class="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-stone-500 transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50">{{ removingId === member.id ? 'Removing…' : 'Remove' }}</button></article></div>
        <div v-else class="px-6 py-14 text-center"><p class="text-sm font-semibold text-stone-800">No team members yet</p><p class="mt-1 text-sm text-stone-500">Invite a colleague to help support your customers.</p></div>
      </section>
    </div>
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/45 p-4 backdrop-blur-[2px]" @click.self="closeModal"><section role="dialog" aria-modal="true" aria-labelledby="invite-title" class="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-5 shadow-xl sm:p-6"><p class="text-xs font-semibold uppercase tracking-[0.14em] text-blue-600">Workspace access</p><h2 id="invite-title" class="mt-1 text-xl font-bold text-stone-900">Invite a teammate</h2><p class="mt-1 text-sm text-stone-500">Add someone to help manage conversations or review support activity.</p><form class="mt-5 space-y-4" @submit.prevent="addMember"><label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Email address</span><input v-model="inviteEmail" type="email" required placeholder="member@company.com" class="w-full rounded-xl border border-stone-200 px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" /></label><label class="block"><span class="mb-1.5 block text-sm font-medium text-stone-700">Role</span><select v-model="inviteRole" class="w-full rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"><option value="agent">Agent — reply to conversations</option><option value="viewer">Viewer — read-only access</option></select></label><p v-if="inviteError" class="text-sm text-rose-600" role="alert">{{ inviteError }}</p><div class="flex justify-end gap-2 border-t border-stone-100 pt-4"><button type="button" @click="closeModal" class="rounded-xl px-4 py-2.5 text-sm font-semibold text-stone-600 hover:bg-stone-100">Cancel</button><button type="submit" :disabled="inviting" class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60">{{ inviting ? 'Sending…' : 'Send invite' }}</button></div></form></section></div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const members = ref([])
const showModal = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('agent')
const loading = ref(true)
const loadError = ref(false)
const inviting = ref(false)
const removingId = ref(null)
const inviteError = ref('')
const message = ref('')
const error = ref(false)
const bid = businessStore.currentBusiness?.id

function initials(name) { return name ? name.trim().split(/\s+/).slice(0, 2).map((part) => part[0].toUpperCase()).join('') : '?' }
function roleClass(role) { return role === 'owner' ? 'bg-blue-50 text-blue-700' : role === 'agent' ? 'bg-emerald-50 text-emerald-700' : 'bg-stone-100 text-stone-600' }
function closeModal() { if (inviting.value) return; showModal.value = false; inviteError.value = '' }

async function loadMembers() {
  if (!bid) { loading.value = false; return }
  loading.value = true; loadError.value = false
  try { const { data } = await api.get(`/team/${bid}/members`); members.value = data }
  catch { loadError.value = true }
  finally { loading.value = false }
}

async function addMember() {
  if (!inviteEmail.value.trim() || inviting.value) return
  inviting.value = true; inviteError.value = ''
  try {
    await api.post(`/team/${bid}/members`, { email: inviteEmail.value.trim(), role: inviteRole.value })
    showModal.value = false; inviteEmail.value = ''; message.value = 'Team member added.'; error.value = false
    await loadMembers()
  } catch (err) { inviteError.value = err.response?.data?.detail || 'Failed to add team member.' }
  finally { inviting.value = false }
}

async function removeMember(memberId) {
  if (!window.confirm('Remove this member from the workspace?')) return
  removingId.value = memberId; message.value = ''
  try { await api.delete(`/team/${bid}/members/${memberId}`); message.value = 'Team member removed.'; error.value = false; await loadMembers() }
  catch (err) { message.value = err.response?.data?.detail || 'Could not remove this member.'; error.value = true }
  finally { removingId.value = null }
}

onMounted(loadMembers)
</script>
