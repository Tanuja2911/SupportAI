<template>
  <div class="p-8 max-w-2xl">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Widget Configuration</h2>

    <div v-if="config" class="space-y-6">
      <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Bot Name</label>
          <input v-model="config.bot_name" class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-pink-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Welcome Message</label>
          <textarea v-model="config.welcome_message" rows="2" class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-pink-500 resize-none"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
          <div class="flex items-center gap-3">
            <input v-model="config.primary_color" type="color" class="w-10 h-10 rounded cursor-pointer" />
            <input v-model="config.primary_color" class="px-4 py-2 border border-gray-300 rounded-lg outline-none w-32 text-sm" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Position</label>
          <select v-model="config.position" class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none">
            <option value="bottom-right">Bottom Right</option>
            <option value="bottom-left">Bottom Left</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Placeholder Text</label>
          <input v-model="config.placeholder_text" class="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-pink-500" />
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="config.show_branding" id="branding" class="rounded" />
          <label for="branding" class="text-sm text-gray-700">Show SupportAI branding</label>
        </div>

        <button
          @click="saveConfig"
          :disabled="saving"
          class="w-full bg-pink-600 text-white py-2.5 rounded-lg font-medium hover:bg-pink-700 transition disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : 'Save Configuration' }}
        </button>
      </div>

      <!-- Preview -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-sm font-medium text-gray-700 mb-4">Preview</h3>
        <div class="border border-gray-200 rounded-xl overflow-hidden max-w-sm mx-auto shadow-lg">
          <div class="p-4 text-white text-sm font-medium" :style="{ backgroundColor: config.primary_color }">
            {{ config.bot_name }}
          </div>
          <div class="p-4 bg-pink-50 min-h-[200px]">
            <div class="bg-white px-3 py-2 rounded-lg shadow-sm text-sm text-gray-700 inline-block">
              {{ config.welcome_message }}
            </div>
          </div>
          <div class="p-3 border-t border-gray-200">
            <input
              disabled
              :placeholder="config.placeholder_text"
              class="w-full px-3 py-2 bg-gray-100 rounded-lg text-sm"
            />
          </div>
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
const config = ref(null)
const saving = ref(false)
const bid = businessStore.currentBusiness?.id

async function loadConfig() {
  if (!bid) return
  const { data } = await api.get(`/widget/${bid}/config`)
  config.value = data
}

async function saveConfig() {
  saving.value = true
  try {
    await api.put(`/widget/${bid}/config`, config.value)
    alert('Widget configuration saved!')
  } catch (err) {
    alert(err.response?.data?.detail || 'Save failed')
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>
