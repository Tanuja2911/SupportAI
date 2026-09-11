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
            @click="removeMember(m.id)"
            class="text-red-500 hover:text-red-700 text-sm"
          >
            Remove
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
        <div class="flex justify-end gap-3">
          <button @click="showModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
          <button @click="addMember" class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">Invite</button>
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
const members = ref([])
const showModal = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('agent')
const bid = businessStore.currentBusiness?.id

async function loadMembers() {
  if (!bid) return
  const { data } = await api.get(`/team/${bid}/members`)
  members.value = data
}

async function addMember() {
  if (!inviteEmail.value) return
  try {
    await api.post(`/team/${bid}/members`, { email: inviteEmail.value, role: inviteRole.value })
    showModal.value = false
    inviteEmail.value = ''
    await loadMembers()
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to add member')
  }
}

async function removeMember(memberId) {
  if (!confirm('Remove this member?')) return
  await api.delete(`/team/${bid}/members/${memberId}`)
  await loadMembers()
}

onMounted(loadMembers)
</script>
