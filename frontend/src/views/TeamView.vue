<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Team Members</h2>
      <button
        @click="showModal = true"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
      >
        Invite Member
      </button>
    </div>

    <div v-if="actionError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{{ actionError }}</div>
    <div v-if="actionSuccess" class="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700" role="status">{{ actionSuccess }}</div>

    <div class="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
      <div v-for="m in members" :key="m.id" class="flex items-center justify-between px-6 py-4">
        <div>
          <p class="font-medium text-gray-800">{{ m.full_name }}</p>
          <p class="text-sm text-gray-500">{{ m.email }}</p>
        </div>
        <div class="flex items-center gap-4">
          <span
            class="px-2 py-1 rounded-full text-xs font-medium"
            :class="m.role === 'owner' ? 'bg-purple-100 text-purple-700' : m.role === 'agent' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'"
          >
            {{ m.role }}
          </span>
          <button
            v-if="m.role !== 'owner'"
            @click="requestRemove(m)"
            :disabled="removingId === m.id"
            class="text-red-500 hover:text-red-700 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ removingId === m.id ? 'Removing…' : 'Remove' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-bold mb-4">Invite Team Member</h3>
        <input
          v-model="inviteEmail"
          type="email"
          placeholder="member@company.com"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select v-model="inviteRole" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 outline-none">
          <option value="agent">Agent</option>
          <option value="viewer">Viewer</option>
        </select>
        <p v-if="actionError" class="mb-3 text-sm text-red-400" role="alert">{{ actionError }}</p>
        <div class="flex justify-end gap-3">
          <button @click="showModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
          <button @click="addMember" class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">Invite</button>
        </div>
      </div>
    </div>

    <ConfirmDialog
      v-if="memberToRemove"
      title="Remove this team member?"
      :message="`${memberToRemove.full_name || memberToRemove.email} will lose access to this workspace.`"
      :error="actionError"
      confirm-label="Remove member"
      pending-label="Removing…"
      :busy="removingId !== null"
      @cancel="memberToRemove = null"
      @confirm="removeMember"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const members = ref([])
const showModal = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('agent')
const actionError = ref('')
const actionSuccess = ref('')
const memberToRemove = ref(null)
const removingId = ref(null)
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
  if (!inviteEmail.value) return
  actionError.value = ''
  actionSuccess.value = ''
  try {
    await api.post(`/team/${bid}/members`, { email: inviteEmail.value.trim(), role: inviteRole.value })
    showModal.value = false; inviteEmail.value = ''; message.value = 'Team member added.'; error.value = false
    await loadMembers()
    actionSuccess.value = 'Team member invited.'
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Failed to add member'
  }
}

function requestRemove(member) {
  actionError.value = ''
  actionSuccess.value = ''
  memberToRemove.value = member
}

async function removeMember() {
  if (!memberToRemove.value || removingId.value) return
  const memberId = memberToRemove.value.id
  removingId.value = memberId
  actionError.value = ''
  try {
    await api.delete(`/team/${bid}/members/${memberId}`)
    memberToRemove.value = null
    actionSuccess.value = 'Team member removed.'
    await loadMembers()
  } catch (err) {
    actionError.value = err.response?.data?.detail || 'Failed to remove member'
  } finally {
    removingId.value = null
  }
}

onMounted(loadMembers)
</script>
