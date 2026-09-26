<template>
  <div class="min-h-screen bg-blue-50 text-stone-900">
    <div v-if="mobileNavOpen" class="fixed inset-0 z-40 bg-stone-950/40 backdrop-blur-[2px] lg:hidden" @click="mobileNavOpen = false"></div>

    <aside class="fixed inset-y-0 left-0 z-50 flex w-[17rem] flex-col border-r border-stone-200 bg-white transition-transform duration-200 lg:translate-x-0" :class="mobileNavOpen ? 'translate-x-0' : '-translate-x-full'">
      <div class="flex h-[4.5rem] items-center justify-between border-b border-stone-100 px-5">
        <router-link to="/app" class="flex items-center gap-3" @click="mobileNavOpen = false">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm shadow-blue-200">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.5a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 8.5v7A2.25 2.25 0 0 0 6 17.75h2.25L12 21l3.75-3.25H18a2.25 2.25 0 0 0 2.25-2.25v-7Z"/><path stroke-linecap="round" d="M8 10h8M8 13.5h5"/></svg>
          </span>
          <span class="text-lg font-bold tracking-tight text-stone-900">Support<span class="text-blue-600">AI</span></span>
        </router-link>
        <button @click="mobileNavOpen = false" class="rounded-lg p-2 text-stone-400 hover:bg-stone-100 lg:hidden" aria-label="Close navigation">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" d="m6 6 12 12M18 6 6 18"/></svg>
        </button>
      </div>

      <div class="border-b border-stone-100 px-4 py-4">
        <p class="px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-400">Workspace</p>
        <div class="mt-2 flex items-center gap-3 rounded-xl border border-stone-200 bg-blue-50 px-3 py-2.5">
          <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-sm font-bold text-blue-600 shadow-sm ring-1 ring-stone-200">{{ businessStore.currentBusiness?.name?.charAt(0)?.toUpperCase() || 'S' }}</span>
          <div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-stone-800">{{ businessStore.currentBusiness?.name || 'My workspace' }}</p><p class="mt-0.5 text-xs text-stone-500">Support workspace</p></div>
          <svg class="h-4 w-4 shrink-0 text-stone-400" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m7 10 5 5 5-5"/></svg>
        </div>
      </div>

      <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Main navigation">
        <p class="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-400">Manage</p>
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" @click="mobileNavOpen = false" class="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition" :class="isActive(item) ? 'bg-blue-50 text-blue-700' : 'text-stone-600 hover:bg-blue-50 hover:text-stone-900'">
          <span class="flex h-8 w-8 items-center justify-center rounded-lg transition" :class="isActive(item) ? 'bg-white text-blue-600 shadow-sm' : 'text-stone-400 group-hover:text-stone-700'">
            <svg class="h-[18px] w-[18px]" fill="none" stroke="currentColor" stroke-width="1.65" viewBox="0 0 24 24" aria-hidden="true">
              <path v-if="item.icon === 'grid'" stroke-linecap="round" stroke-linejoin="round" d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>
              <path v-else-if="item.icon === 'book'" stroke-linecap="round" stroke-linejoin="round" d="M12 7c-2.5-2-5-2.4-8-1.5v13c3-.9 5.5-.5 8 1.5m0-13c2.5-2 5-2.4 8-1.5v13c-3-.9-5.5-.5-8 1.5m0-13v13"/>
              <path v-else-if="item.icon === 'chat'" stroke-linecap="round" stroke-linejoin="round" d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-9.5A7.5 7.5 0 0 1 10.5 4H12a8 8 0 0 1 8 7.5Z"/><path v-if="item.icon === 'chat'" stroke-linecap="round" d="M8 10h7M8 13h5"/>
              <path v-else-if="item.icon === 'alert'" stroke-linecap="round" stroke-linejoin="round" d="M12 9v3m0 4h.01M10.3 4.5 2.9 17.3A1.8 1.8 0 0 0 4.5 20h15a1.8 1.8 0 0 0 1.6-2.7L13.7 4.5a2 2 0 0 0-3.4 0Z"/>
              <path v-else-if="item.icon === 'lightbulb'" stroke-linecap="round" stroke-linejoin="round" d="M9 18h6m-5 3h4m-4-6.5a6 6 0 1 1 4 0c-.7.5-1 1.2-1 2h-2c0-.8-.3-1.5-1-2Z"/>
              <path v-else-if="item.icon === 'help'" stroke-linecap="round" stroke-linejoin="round" d="M9.5 9a2.6 2.6 0 1 1 4.2 2.1c-1 .7-1.7 1.1-1.7 2.4m0 3h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/>
              <path v-else-if="item.icon === 'settings'" stroke-linecap="round" stroke-linejoin="round" d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm0-5 1 .2.8 2.2 1.6.9 2.3-.4 1.3 1.7-.8 2.2.1 1.8 1.6 1.7-.8 2-2.4.2-1.5 1.1-.8 2.2-2.1.4-1.5-1.8-1.7-.5-2.2.8-1.7-1.4.3-2.3-.7-1.6-2-1.3.2-2.1 2.1-.9 1-1.4-.1-2.4 1.8-1.1 2.1 1.1 1.7-.1L12 3.5Z"/>
              <path v-else-if="item.icon === 'users'" stroke-linecap="round" stroke-linejoin="round" d="M16 20v-1.5a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4V20m6-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm6-5a3 3 0 0 1 0 6m2 3h1a3 3 0 0 1 3 3v2"/>
              <path v-else stroke-linecap="round" stroke-linejoin="round" d="M4 5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5Zm4 4 3 3-3 3m5 0h3"/>
            </svg>
          </span>
          <span class="flex-1">{{ item.label }}</span>
          <span v-if="item.badge" class="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">{{ item.badge }}</span>
          <span v-if="isActive(item)" class="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
        </router-link>
      </nav>

      <div class="border-t border-stone-100 p-3">
        <div class="flex items-center gap-3 rounded-xl px-2 py-2">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-100 to-blue-100 text-sm font-bold text-blue-700">{{ auth.user?.full_name?.charAt(0)?.toUpperCase() || '?' }}</div>
          <div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-stone-800">{{ auth.user?.full_name || 'Account' }}</p><p class="truncate text-xs text-stone-500">{{ auth.user?.email }}</p></div>
        </div>
        <button @click="handleLogout" class="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-stone-500 transition hover:bg-blue-50 hover:text-blue-700"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M10 17l5-5-5-5m5 5H3m9-9h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/></svg>Sign out</button>
      </div>
    </aside>

    <div class="min-h-screen lg:pl-[17rem]">
      <header class="sticky top-0 z-30 flex h-[4.5rem] items-center justify-between border-b border-stone-200/80 bg-white/90 px-4 backdrop-blur-md sm:px-6 lg:px-8">
        <div class="flex min-w-0 items-center gap-3">
          <button @click="mobileNavOpen = true" class="flex h-9 w-9 items-center justify-center rounded-xl border border-stone-200 text-stone-600 transition hover:bg-blue-50 lg:hidden" aria-label="Open navigation"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16"/></svg></button>
          <div class="min-w-0"><p class="truncate text-sm font-semibold text-stone-800">{{ currentSection }}</p><p class="hidden text-xs text-stone-500 sm:block">Manage your AI customer support</p></div>
        </div>
        <div class="flex items-center gap-3">
          <span class="hidden items-center gap-2 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-600 sm:inline-flex"><span class="h-2 w-2 rounded-full bg-emerald-500"></span>Workspace active</span>
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-sm font-bold text-blue-700 ring-1 ring-blue-100">{{ auth.user?.full_name?.charAt(0)?.toUpperCase() || '?' }}</div>
        </div>
      </header>
      <main class="min-h-[calc(100vh-4.5rem)]"><router-view /></main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useBusinessStore } from '../stores/business.js'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const businessStore = useBusinessStore()
const mobileNavOpen = ref(false)

const navItems = [
  { path: '/app', label: 'Dashboard', icon: 'grid' },
  { path: '/app/knowledge', label: 'Knowledge Base', icon: 'book' },
  { path: '/app/conversations', label: 'Conversations', icon: 'chat' },
  { path: '/app/escalations', label: 'Escalations', icon: 'alert' },
  { path: '/app/knowledge-gaps', label: 'Knowledge Gaps', icon: 'lightbulb' },
  { path: '/app/faq', label: 'FAQ Overrides', icon: 'help' },
  { path: '/app/widget', label: 'Widget Config', icon: 'settings' },
  { path: '/app/ai-settings', label: 'AI Settings', icon: 'sparkle' },
  { path: '/app/team', label: 'Team', icon: 'users' },
  { path: '/app/sandbox', label: 'Test Chat', icon: 'terminal' },
]

const currentSection = computed(() => {
  return navItems.find((item) => isActive(item))?.label || 'Workspace'
})

function isActive(item) {
  if (item.path === '/app') return route.path === '/app'
  return route.path === item.path || route.path.startsWith(`${item.path}/`)
}

watch(() => route.fullPath, () => { mobileNavOpen.value = false })

function handleLogout() {
  auth.logout()
  businessStore.clearBusiness()
  router.push('/login')
}
</script>
