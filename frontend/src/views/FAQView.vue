<template>
  <section class="faq-page">
    <header class="faq-heading">
      <div>
        <p class="faq-kicker">SUPPORT CONTENT</p>
        <h2 class="text-2xl font-bold text-gray-800">FAQ library</h2>
        <p class="text-gray-500 text-sm mt-1">Create exact answers for common questions. Active FAQs take priority over document search.</p>
      </div>
      <div class="faq-header-actions">
        <button
          type="button"
          @click="autoGenerate"
          :disabled="generating || !businessId"
          class="faq-secondary-button"
        >
          {{ generating ? 'Generating…' : 'Generate from documents' }}
        </button>
        <button type="button" @click="openAddModal" class="faq-primary-button">Add FAQ</button>
      </div>
    </header>

    <div v-if="loadError" class="faq-alert faq-alert-error" role="alert">{{ loadError }}</div>
    <div v-if="genError" class="faq-alert faq-alert-error" role="alert">
      <div>
        <p>{{ genError.message }}</p>
        <p v-if="genError.diagnostic" class="faq-alert-detail">{{ genError.diagnostic }}</p>
        <p v-if="genError.actionHint" class="faq-alert-detail">{{ genError.actionHint }}</p>
      </div>
      <span v-if="genError.code" class="faq-error-code">{{ genError.code }}</span>
    </div>
    <div v-if="actionError" class="faq-alert faq-alert-error" role="alert">{{ actionError }}</div>
    <div v-if="successMessage" class="faq-alert faq-alert-success" role="status">{{ successMessage }}</div>

    <div v-if="generating" class="faq-generating" role="status" aria-live="polite">
      <span class="faq-spinner" aria-hidden="true"></span>
      <div><p>Reading your processed documents…</p><span>Generating suggested questions and answers.</span></div>
    </div>

    <section v-if="suggestions.length" class="faq-suggestions">
      <header class="faq-suggestions-heading">
        <div>
          <p class="faq-kicker">DRAFTS</p>
          <h3>Suggested FAQs <span>{{ suggestions.length }}</span></h3>
          <p>Review each answer before adding it to your live FAQ library.</p>
        </div>
        <div class="faq-header-actions">
          <button type="button" @click="acceptAll" :disabled="acceptingAll || acceptingIndex !== null" class="faq-primary-button">
            {{ acceptingAll ? 'Adding…' : 'Accept all' }}
          </button>
          <button type="button" @click="suggestions = []" :disabled="acceptingAll || acceptingIndex !== null" class="faq-quiet-button">Dismiss</button>
        </div>
      </header>
      <article v-for="(suggestion, index) in suggestions" :key="`${suggestion.question}-${index}`" class="faq-suggestion">
        <div class="faq-pair">
          <p class="faq-question">{{ suggestion.question }}</p>
          <p class="faq-answer">{{ suggestion.answer }}</p>
        </div>
        <div class="faq-row-actions">
          <button type="button" @click="acceptSuggestion(index)" :disabled="acceptingAll || acceptingIndex !== null" class="faq-accept-button">
            {{ acceptingIndex === index ? 'Adding…' : 'Add to library' }}
          </button>
          <button type="button" @click="rejectSuggestion(index)" :disabled="acceptingAll || acceptingIndex !== null" class="faq-reject-button">Reject</button>
        </div>
      </article>
    </section>

    <section class="faq-library">
      <header class="faq-library-heading">
        <div><h3>Your FAQs</h3><p>{{ faqs.length }} {{ faqs.length === 1 ? 'answer' : 'answers' }}</p></div>
        <span v-if="loading" class="faq-subtle-status">Loading…</span>
      </header>
      <div v-if="loading && !faqs.length" class="faq-empty">Loading FAQ library…</div>
      <div v-else-if="!faqs.length" class="faq-empty">
        <span class="faq-empty-icon" aria-hidden="true">?</span>
        <h4>No FAQ overrides yet</h4>
        <p>Add a precise answer or generate drafts from processed knowledge base documents.</p>
      </div>
      <article v-for="faq in faqs" :key="faq.id" class="faq-item">
        <div class="faq-pair">
          <p class="faq-question">{{ faq.question }}</p>
          <p class="faq-answer">{{ faq.answer }}</p>
        </div>
        <button type="button" @click="requestDelete(faq)" :disabled="deletingId === faq.id" class="faq-delete-button">
          {{ deletingId === faq.id ? 'Deleting…' : 'Delete' }}
        </button>
      </article>
    </section>

    <div v-if="showModal" class="faq-modal-backdrop" @click.self="closeAddModal" @keydown.esc="closeAddModal">
      <section class="faq-modal" role="dialog" aria-modal="true" aria-labelledby="faq-add-title">
        <button type="button" class="faq-modal-close" aria-label="Close" @click="closeAddModal">×</button>
        <p class="faq-kicker">NEW ANSWER</p>
        <h3 id="faq-add-title">Add FAQ override</h3>
        <p class="faq-modal-intro">Write the exact response you want customers to receive.</p>
        <form @submit.prevent="addFaq">
          <label for="faq-question">Customer question</label>
          <input id="faq-question" v-model="newQuestion" maxlength="500" required placeholder="e.g. What is your return policy?" />
          <label for="faq-answer">Your answer</label>
          <textarea id="faq-answer" v-model="newAnswer" maxlength="5000" rows="5" required placeholder="Write a clear, accurate answer…"></textarea>
          <p v-if="actionError" class="faq-inline-error" role="alert">{{ actionError }}</p>
          <div class="faq-modal-actions">
            <button type="button" @click="closeAddModal" :disabled="saving" class="faq-quiet-button">Cancel</button>
            <button type="submit" :disabled="saving || !newQuestion.trim() || !newAnswer.trim()" class="faq-primary-button">
              {{ saving ? 'Saving…' : 'Save FAQ' }}
            </button>
          </div>
        </form>
      </section>
    </div>

    <div v-if="faqToDelete" class="faq-modal-backdrop" @click.self="faqToDelete = null" @keydown.esc="faqToDelete = null">
      <section class="faq-confirm-modal" role="alertdialog" aria-modal="true" aria-labelledby="faq-delete-title" aria-describedby="faq-delete-description">
        <span class="faq-delete-icon" aria-hidden="true">!</span>
        <h3 id="faq-delete-title">Delete this FAQ?</h3>
        <p id="faq-delete-description">This answer will no longer be used for matching customer questions.</p>
        <p v-if="actionError" class="faq-inline-error" role="alert">{{ actionError }}</p>
        <div class="faq-modal-actions">
          <button type="button" @click="faqToDelete = null" :disabled="deletingId !== null" class="faq-quiet-button">Keep FAQ</button>
          <button type="button" @click="deleteFaq" :disabled="deletingId !== null" class="faq-danger-button">
            {{ deletingId ? 'Deleting…' : 'Delete FAQ' }}
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api from '../api/client.js'
import { useBusinessStore } from '../stores/business.js'

const businessStore = useBusinessStore()
const businessId = computed(() => businessStore.currentBusiness?.id || '')
const faqs = ref([])
const showModal = ref(false)
const newQuestion = ref('')
const newAnswer = ref('')
const suggestions = ref([])
const generating = ref(false)
const loading = ref(false)
const saving = ref(false)
const deletingId = ref(null)
const acceptingIndex = ref(null)
const acceptingAll = ref(false)
const genError = ref(null)
const actionError = ref('')
const loadError = ref('')
const successMessage = ref('')
const faqToDelete = ref(null)

function errorDetails(error, fallback) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return { message: detail }
  if (detail && typeof detail === 'object') {
    return {
      message: detail.message || fallback,
      code: detail.error_code || '',
      diagnostic: detail.diagnostic || '',
      actionHint: detail.action_hint || '',
    }
  }
  return { message: fallback }
}

function clearFeedback() {
  actionError.value = ''
  successMessage.value = ''
}

async function ensureBusiness() {
  if (businessId.value) return true
  try {
    const businesses = await businessStore.fetchMyBusinesses()
    return businesses.length > 0 && Boolean(businessId.value)
  } catch (error) {
    loadError.value = errorDetails(error, 'Could not load your workspace.').message
    return false
  }
}

async function loadFaqs() {
  if (!businessId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await api.get(`/faq/${businessId.value}`)
    faqs.value = data
  } catch (error) {
    loadError.value = errorDetails(error, 'Could not load FAQs. Please try again.').message
  } finally {
    loading.value = false
  }
}

function openAddModal() {
  clearFeedback()
  showModal.value = true
}

function closeAddModal() {
  if (saving.value) return
  showModal.value = false
  actionError.value = ''
}

async function addFaq() {
  const question = newQuestion.value.trim()
  const answer = newAnswer.value.trim()
  if (!question || !answer || saving.value) return
  clearFeedback()
  if (!businessId.value && !(await ensureBusiness())) {
    actionError.value = 'No workspace is available. Create one before adding an FAQ.'
    return
  }
  saving.value = true
  try {
    await api.post(`/faq/${businessId.value}`, { question, answer })
    showModal.value = false
    newQuestion.value = ''
    newAnswer.value = ''
    successMessage.value = 'FAQ added to your library.'
    await loadFaqs()
  } catch (error) {
    actionError.value = errorDetails(error, 'Could not save this FAQ. Please try again.').message
  } finally {
    saving.value = false
  }
}

function requestDelete(faq) {
  clearFeedback()
  faqToDelete.value = faq
}

async function deleteFaq() {
  if (!faqToDelete.value || deletingId.value) return
  const faq = faqToDelete.value
  deletingId.value = faq.id
  clearFeedback()
  try {
    await api.delete(`/faq/${businessId.value}/${faq.id}`)
    faqToDelete.value = null
    successMessage.value = 'FAQ deleted.'
    await loadFaqs()
  } catch (error) {
    actionError.value = errorDetails(error, 'Could not delete this FAQ. Please try again.').message
  } finally {
    deletingId.value = null
  }
}

async function autoGenerate() {
  if (generating.value) return
  clearFeedback()
  genError.value = null
  if (!businessId.value && !(await ensureBusiness())) {
    genError.value = { message: 'No workspace is available. Create one before generating FAQs.' }
    return
  }
  generating.value = true
  try {
    const { data } = await api.post(`/faq/${businessId.value}/auto-generate`, null, { timeout: 90000 })
    suggestions.value = Array.isArray(data.suggestions) ? data.suggestions : []
    if (!suggestions.value.length) genError.value = { message: 'The provider returned no FAQ suggestions. Try again or add an FAQ manually.' }
  } catch (error) {
    genError.value = errorDetails(error, 'FAQ generation failed. Check your processed documents and AI provider settings.')
  } finally {
    generating.value = false
  }
}

async function acceptSuggestion(index) {
  if (acceptingAll.value || acceptingIndex.value !== null) return
  const suggestion = suggestions.value[index]
  if (!suggestion) return
  acceptingIndex.value = index
  clearFeedback()
  try {
    await api.post(`/faq/${businessId.value}`, { question: suggestion.question, answer: suggestion.answer })
    suggestions.value.splice(index, 1)
    successMessage.value = 'FAQ added to your library.'
    await loadFaqs()
  } catch (error) {
    actionError.value = errorDetails(error, 'Could not add this suggestion. Please try again.').message
  } finally {
    acceptingIndex.value = null
  }
}

async function acceptAll() {
  if (acceptingAll.value || acceptingIndex.value !== null || !suggestions.value.length) return
  acceptingAll.value = true
  clearFeedback()
  let saved = 0
  try {
    while (suggestions.value.length) {
      const suggestion = suggestions.value[0]
      await api.post(`/faq/${businessId.value}`, { question: suggestion.question, answer: suggestion.answer })
      suggestions.value.shift()
      saved += 1
    }
    successMessage.value = `${saved} ${saved === 1 ? 'FAQ' : 'FAQs'} added to your library.`
    await loadFaqs()
  } catch (error) {
    actionError.value = errorDetails(error, `${saved} FAQ${saved === 1 ? '' : 's'} added; the remaining suggestions are still available.`).message
    if (saved) await loadFaqs()
  } finally {
    acceptingAll.value = false
  }
}

function rejectSuggestion(index) {
  suggestions.value.splice(index, 1)
}

watch(businessId, (nextId, previousId) => {
  if (nextId && nextId !== previousId) loadFaqs()
  else if (!nextId) faqs.value = []
})

onMounted(async () => {
  if (await ensureBusiness()) await loadFaqs()
})
</script>

<style scoped>
.faq-page { max-width: 1120px; margin: 0 auto; }
.faq-heading, .faq-suggestions-heading, .faq-library-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 22px; }
.faq-heading { margin-bottom: 24px; }
.faq-kicker { margin-bottom: 7px; color: #918ba0; font-size: .65rem; font-weight: 700; letter-spacing: .14em; }
.faq-heading h2 { margin-bottom: 2px; }
.faq-header-actions, .faq-row-actions { display: flex; align-items: center; gap: 9px; }
.faq-primary-button, .faq-secondary-button, .faq-quiet-button, .faq-accept-button, .faq-reject-button, .faq-delete-button, .faq-danger-button { border-radius: .68rem; font-size: .78rem; font-weight: 600; transition: color 180ms, background-color 180ms, border-color 180ms, transform 180ms; }
.faq-primary-button { border: 1px solid rgba(201,187,255,.23); background: linear-gradient(135deg,#8064d9,#6049b0); padding: .68rem .95rem; color: white; }
.faq-primary-button:hover:not(:disabled) { filter: brightness(1.12); }
.faq-secondary-button { border: 1px solid rgba(167,139,250,.27); background: rgba(167,139,250,.07); padding: .68rem .9rem; color: #d1c3ff; }
.faq-secondary-button:hover:not(:disabled) { border-color: rgba(184,165,255,.5); background: rgba(167,139,250,.14); }
.faq-quiet-button { border: 1px solid rgba(173,190,220,.13); background: rgba(255,255,255,.025); padding: .65rem .85rem; color: #bcb6c8; }
.faq-quiet-button:hover:not(:disabled) { background: rgba(255,255,255,.07); color: #f1eff8; }
.faq-accept-button { border: 1px solid rgba(52,211,153,.23); background: rgba(52,211,153,.1); padding: .58rem .75rem; color: #a9ebcf; }
.faq-accept-button:hover:not(:disabled) { background: rgba(52,211,153,.17); }
.faq-reject-button { border: 1px solid rgba(173,190,220,.13); background: transparent; padding: .58rem .75rem; color: #a49daf; }
.faq-reject-button:hover:not(:disabled) { border-color: rgba(248,113,113,.28); background: rgba(248,113,113,.08); color: #ffc1c1; }
.faq-delete-button { border: 1px solid rgba(248,113,113,.17); background: rgba(248,113,113,.045); padding: .55rem .72rem; color: #e8a6a6; }
.faq-delete-button:hover:not(:disabled), .faq-danger-button:hover:not(:disabled) { border-color: rgba(248,113,113,.4); background: rgba(127,29,29,.28); color: #ffd0d0; }
:where(.faq-page) button:disabled { cursor: not-allowed; opacity: .48; }
.faq-alert { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin: 0 0 14px; border: 1px solid; border-radius: .8rem; padding: .8rem 1rem; font-size: .82rem; }
.faq-alert-error { border-color: rgba(248,113,113,.2); background: rgba(127,29,29,.14); color: #ffc1c1; }
.faq-alert-success { border-color: rgba(52,211,153,.2); background: rgba(52,211,153,.08); color: #a9ebcf; }
.faq-alert-detail { margin-top: .32rem; color: #d2c8e7; font-size: .74rem; }
.faq-error-code { flex: 0 0 auto; color: #d5caff; font-size: .68rem; text-transform: uppercase; }
.faq-generating { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; border: 1px solid rgba(167,139,250,.18); border-radius: .8rem; background: rgba(167,139,250,.06); padding: .85rem 1rem; color: #d5caff; font-size: .82rem; }
.faq-generating span:last-child { display: block; margin-top: 2px; color: #918ba0; font-size: .72rem; }
.faq-spinner { width: 16px; height: 16px; flex: 0 0 auto; border: 2px solid rgba(199,185,255,.25); border-top-color: #c6b7ff; border-radius: 50%; animation: faq-spin .75s linear infinite; }
.faq-suggestions, .faq-library { overflow: hidden; border: 1px solid rgba(173,190,220,.12); border-radius: 1rem; background: rgba(19,20,28,.72); }
.faq-suggestions { margin-bottom: 20px; border-color: rgba(167,139,250,.19); background: rgba(139,115,232,.045); }
.faq-suggestions-heading, .faq-library-heading { padding: 20px 22px; }
.faq-suggestions-heading { align-items: center; border-bottom: 1px solid rgba(167,139,250,.12); }
.faq-suggestions-heading .faq-kicker { margin-bottom: 3px; }
.faq-suggestions-heading h3, .faq-library-heading h3 { color: #ede9f5; font-size: .98rem; font-weight: 650; }
.faq-suggestions-heading h3 span { margin-left: 5px; border: 1px solid rgba(167,139,250,.2); border-radius: 999px; background: rgba(167,139,250,.1); padding: .12rem .45rem; color: #d3c5ff; font-size: .68rem; }
.faq-suggestions-heading p:last-child, .faq-library-heading p { margin-top: 4px; color: #918ba0; font-size: .74rem; }
.faq-suggestion, .faq-item { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; border-bottom: 1px solid rgba(173,190,220,.08); padding: 18px 22px; }
.faq-suggestion:last-child, .faq-item:last-child { border-bottom: 0; }
.faq-pair { min-width: 0; }
.faq-question { color: #ece8f4; font-size: .86rem; font-weight: 620; line-height: 1.5; }
.faq-question::before { content: 'Q'; display: inline-grid; width: 19px; height: 19px; place-items: center; margin-right: 8px; border-radius: 6px; background: rgba(167,139,250,.12); color: #c7b6ff; font-size: .65rem; }
.faq-answer { margin: 8px 0 0 27px; color: #aaa4b5; font-size: .82rem; line-height: 1.7; white-space: pre-wrap; }
.faq-answer::before { content: 'A'; display: inline-grid; width: 19px; height: 19px; place-items: center; margin: 0 8px 0 -27px; border-radius: 6px; background: rgba(255,255,255,.055); color: #aaa4b5; font-size: .65rem; }
.faq-row-actions { flex: 0 0 auto; }
.faq-library { margin-top: 20px; }
.faq-library-heading { align-items: center; border-bottom: 1px solid rgba(173,190,220,.08); }
.faq-subtle-status { color: #918ba0; font-size: .72rem; }
.faq-item { padding-block: 20px; }
.faq-empty { display: grid; justify-items: center; padding: 46px 20px; color: #918ba0; font-size: .8rem; text-align: center; }
.faq-empty h4 { margin-top: 10px; color: #ddd8e8; font-size: .87rem; font-weight: 650; }
.faq-empty p { max-width: 420px; margin-top: 5px; line-height: 1.6; }
.faq-empty-icon { display: grid; width: 40px; height: 40px; place-items: center; border: 1px solid rgba(167,139,250,.18); border-radius: 13px; background: rgba(167,139,250,.08); color: #c7b6ff; font-weight: 700; }
.faq-modal-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; overflow-y: auto; background: rgba(4,5,9,.74); padding: 20px; backdrop-filter: blur(7px); }
.faq-modal, .faq-confirm-modal { position: relative; width: min(100%, 510px); border: 1px solid rgba(173,190,220,.17); border-radius: 1rem; background: #15161f; padding: 26px; box-shadow: 0 28px 90px rgba(0,0,0,.55); }
.faq-modal-close { position: absolute; top: 13px; right: 15px; width: 34px; height: 34px; border: 1px solid rgba(173,190,220,.11); border-radius: 9px; background: rgba(255,255,255,.03); color: #aca6b8; font-size: 1.35rem; line-height: 1; }
.faq-modal h3, .faq-confirm-modal h3 { color: #f0edf7; font-size: 1.2rem; font-weight: 650; }
.faq-modal-intro { margin-top: 5px; margin-bottom: 20px; color: #9c96a8; font-size: .8rem; }
.faq-modal form label { display: block; margin: 14px 0 6px; color: #c9c4d2; font-size: .77rem; font-weight: 600; }
.faq-modal input, .faq-modal textarea { width: 100%; border: 1px solid rgba(173,190,220,.16); border-radius: .65rem; outline: none; background: #101117; padding: .72rem .8rem; color: #f0edf7; font: inherit; font-size: .82rem; }
.faq-modal input:focus, .faq-modal textarea:focus { border-color: rgba(184,165,255,.58); box-shadow: 0 0 0 3px rgba(167,139,250,.11); }
.faq-modal textarea { resize: vertical; }
.faq-modal input::placeholder, .faq-modal textarea::placeholder { color: #777286; }
.faq-modal-actions { display: flex; justify-content: flex-end; gap: 9px; margin-top: 22px; }
.faq-inline-error { margin-top: 10px; color: #ffc1c1; font-size: .76rem; }
.faq-confirm-modal { width: min(100%, 420px); text-align: center; }
.faq-delete-icon { display: grid; width: 42px; height: 42px; place-items: center; margin: 0 auto 14px; border: 1px solid rgba(248,113,113,.22); border-radius: 14px; background: rgba(248,113,113,.1); color: #ffbebe; font-size: 1.1rem; font-weight: 700; }
.faq-confirm-modal > p { max-width: 310px; margin: 7px auto 0; color: #a39dad; font-size: .8rem; line-height: 1.6; }
.faq-danger-button { border: 1px solid rgba(248,113,113,.28); background: rgba(127,29,29,.28); padding: .65rem .85rem; color: #ffc1c1; }
@keyframes faq-spin { to { transform: rotate(360deg); } }
@media (max-width: 680px) {
  .faq-heading, .faq-suggestions-heading { align-items: flex-start; flex-direction: column; }
  .faq-header-actions { width: 100%; flex-wrap: wrap; }
  .faq-suggestion, .faq-item { flex-direction: column; gap: 13px; }
  .faq-row-actions { align-self: flex-end; }
  .faq-suggestions-heading, .faq-library-heading { padding: 17px; }
  .faq-suggestion, .faq-item { padding: 16px 17px; }
}
@media (prefers-reduced-motion: reduce) { .faq-spinner { animation-duration: 1.5s; } }
</style>
