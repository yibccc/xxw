<script setup>
defineProps({
  toasts: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <teleport to="body">
    <div class="toast-stack" aria-live="polite">
      <article
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-card"
        :data-tone="toast.tone"
      >
        <div class="toast-card__body">
          <p class="toast-card__title">{{ toast.title }}</p>
          <p v-if="toast.message" class="toast-card__message">{{ toast.message }}</p>
        </div>
      </article>
    </div>
  </teleport>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  top: 1.25rem;
  right: 1.25rem;
  display: grid;
  gap: 0.75rem;
  z-index: 80;
}

.toast-card {
  width: min(22rem, calc(100vw - 2rem));
  padding: 0.95rem 1rem;
  border-radius: 18px;
  border: 1px solid rgba(123, 92, 55, 0.18);
  background: rgba(255, 250, 244, 0.97);
  box-shadow: var(--shadow-soft);
}

.toast-card__body {
  min-width: 0;
}

.toast-card[data-tone='accent'] {
  border-color: rgba(201, 126, 62, 0.34);
}

.toast-card[data-tone='danger'] {
  border-color: rgba(176, 67, 46, 0.34);
}

.toast-card__title {
  margin: 0;
  font-weight: 700;
}

.toast-card__message {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
  font-size: 0.92rem;
}
</style>
