<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  width: {
    type: String,
    default: '560px',
  },
  closable: {
    type: Boolean,
    default: true,
  },
  closeOnBackdrop: {
    type: Boolean,
    default: true,
  },
})

defineEmits(['close'])
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="closeOnBackdrop && $emit('close')">
      <section class="modal-panel" :style="{ maxWidth: width }">
        <header class="modal-panel__header">
          <div>
            <h2>{{ title }}</h2>
            <p v-if="description" class="modal-panel__description">{{ description }}</p>
          </div>
          <button v-if="closable" class="button ghost" type="button" @click="$emit('close')">关闭</button>
        </header>
        <div class="modal-panel__body">
          <slot />
        </div>
        <footer v-if="$slots.actions" class="modal-panel__actions">
          <slot name="actions" />
        </footer>
      </section>
    </div>
  </teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgba(28, 25, 23, 0.58);
  backdrop-filter: blur(10px);
  z-index: 50;
}

.modal-panel {
  width: min(100%, 100%);
  border-radius: 28px;
  border: 1px solid rgba(123, 92, 55, 0.18);
  background: rgba(255, 249, 241, 0.98);
  box-shadow: 0 28px 80px rgba(55, 37, 22, 0.18);
}

.modal-panel__header,
.modal-panel__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
}

.modal-panel__header {
  border-bottom: 1px solid var(--line);
}

.modal-panel__description {
  margin: 0.5rem 0 0;
  color: var(--text-muted);
}

.modal-panel__body {
  padding: 1.5rem;
}

.modal-panel__actions {
  justify-content: flex-end;
  border-top: 1px solid var(--line);
}
</style>
