<template>
  <div class="confirm-backdrop" @click.self="!busy && $emit('cancel')" @keydown.esc="!busy && $emit('cancel')">
    <section class="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-description">
      <span class="confirm-icon" aria-hidden="true">!</span>
      <h2 id="confirm-title">{{ title }}</h2>
      <p id="confirm-description">{{ message }}</p>
      <p v-if="error" class="confirm-error" role="alert">{{ error }}</p>
      <div class="confirm-actions">
        <button type="button" class="confirm-cancel" :disabled="busy" @click="$emit('cancel')">{{ cancelLabel }}</button>
        <button type="button" class="confirm-danger" :disabled="busy" @click="$emit('confirm')">
          {{ busy ? pendingLabel : confirmLabel }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  message: { type: String, required: true },
  error: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Delete' },
  cancelLabel: { type: String, default: 'Cancel' },
  pendingLabel: { type: String, default: 'Deleting…' },
  busy: { type: Boolean, default: false },
})

defineEmits(['cancel', 'confirm'])
</script>

<style scoped>
.confirm-backdrop { position: fixed; z-index: 90; inset: 0; display: grid; place-items: center; overflow-y: auto; background: rgba(4,5,9,.74); padding: 20px; backdrop-filter: blur(7px); }
.confirm-dialog { width: min(100%, 420px); border: 1px solid rgba(173,190,220,.17); border-radius: 1rem; background: #15161f; padding: 26px; box-shadow: 0 28px 90px rgba(0,0,0,.55); text-align: center; }
.confirm-icon { display: grid; width: 42px; height: 42px; place-items: center; margin: 0 auto 14px; border: 1px solid rgba(248,113,113,.22); border-radius: 14px; background: rgba(248,113,113,.1); color: #ffbebe; font-size: 1.1rem; font-weight: 700; }
.confirm-dialog h2 { color: #f0edf7; font-size: 1.12rem; font-weight: 650; }
.confirm-dialog p { max-width: 320px; margin: 8px auto 0; color: #a39dad; font-size: .8rem; line-height: 1.6; }
.confirm-dialog .confirm-error { max-width: none; color: #ffc1c1; font-size: .76rem; }
.confirm-actions { display: flex; justify-content: center; gap: 9px; margin-top: 22px; }
.confirm-actions button { border-radius: .68rem; padding: .65rem .85rem; font-size: .78rem; font-weight: 600; }
.confirm-cancel { border: 1px solid rgba(173,190,220,.13); background: rgba(255,255,255,.025); color: #bcb6c8; }
.confirm-cancel:hover:not(:disabled) { background: rgba(255,255,255,.07); color: #f1eff8; }
.confirm-danger { border: 1px solid rgba(248,113,113,.28); background: rgba(127,29,29,.28); color: #ffc1c1; }
.confirm-danger:hover:not(:disabled) { border-color: rgba(248,113,113,.4); background: rgba(127,29,29,.4); color: #ffd0d0; }
.confirm-actions button:disabled { cursor: not-allowed; opacity: .5; }
</style>
