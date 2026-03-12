<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="auth-card">
    <header class="auth-card__header">
      <p class="auth-card__eyebrow">Timer Service</p>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="auth-card__subtitle">{{ subtitle }}</p>
    </header>
    <div class="auth-card__body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="auth-card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped>
.auth-card {
  width: min(100%, 460px);
  padding: 2rem;
  border: 1px solid var(--line);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 243, 236, 0.92));
  box-shadow: var(--shadow-soft);
}

.auth-card__header {
  margin-bottom: 1.75rem;
}

.auth-card__eyebrow {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.auth-card__subtitle {
  margin: 0.65rem 0 0;
  color: var(--text-muted);
}

.auth-card__footer {
  margin-top: 1rem;
  color: var(--text-muted);
}
</style>
