<script setup>
import { reactive, ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { createEvent } from '@/utils/eventsmock'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  categories: { type: Array, default: () => ['Running','Cycling','Yoga','Basketball','Hiking'] }
})
const emit = defineEmits(['update:modelValue', 'created'])

const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

// lock background scroll
function lockBody(v) {
  const cls = 'no-scroll'
  if (v) document.body.classList.add(cls)
  else document.body.classList.remove(cls)
}
watch(open, lockBody)
onMounted(() => lockBody(open.value))
onBeforeUnmount(() => lockBody(false))

// random light gradient for page background
const gradient = ref('')
function randomGradient() {
  const h1 = Math.floor(Math.random() * 360)
  const h2 = (h1 + 50 + Math.floor(Math.random() * 160)) % 360
  // keep it light & readable
  return `linear-gradient(135deg,
    hsl(${h1} 85% 96%) 0%,
    hsl(${h2} 85% 92%) 100%)`
}
function refreshGradient() { gradient.value = randomGradient() }
watch(open, v => { if (v) refreshGradient() })
onMounted(() => { if (open.value) refreshGradient() })

// form state
const form = reactive({
  title: '',
  start: '',
  end: '',
  location: '',
  description: '',
  category: '',
  coverFile: null,
  coverUrl: ''
})
const loading = ref(false)
const err = ref('')
const canSubmit = computed(() =>
  form.title.trim() && form.start && form.end && form.location.trim()
)

function onPickCover(e) {
  const f = e.target.files?.[0]
  if (!f) return
  form.coverFile = f
  form.coverUrl = URL.createObjectURL(f)
}

async function submit() {
  if (!canSubmit.value || loading.value) return
  err.value = ''
  loading.value = true
  try {
    const payload = {
      title: form.title.trim(),
      date: `${form.start} ~ ${form.end}`,
      start: form.start, end: form.end,
      location: form.location.trim(),
      description: form.description.trim(),
      category: form.category,
      cover: form.coverUrl || 'https://picsum.photos/seed/new/800/480',
      host: 'You'
    }
    const created = await createEvent(payload)
    emit('created', created)
    reset()
    open.value = false
  } catch (e) {
    err.value = 'Create failed, please try again.'
  } finally {
    loading.value = false
  }
}

function reset() {
  form.title = ''
  form.start = ''
  form.end = ''
  form.location = ''
  form.description = ''
  form.category = ''
  form.coverFile = null
  form.coverUrl = ''
}

// focus first input when open
const firstInput = ref(null)
watch(open, async v => {
  if (v) {
    await nextTick()
    firstInput.value?.focus()
  }
})
</script>

<template>
  <transition name="page-up">
    <div
      v-if="open"
      class="page"
      role="dialog"
      aria-modal="true"
      :style="{ '--page-bg': gradient }"
    >
      <header class="topbar">
        <button class="tb-btn" @click="open=false" aria-label="Close">
          <svg viewBox="0 0 24 24" class="ico"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
        <h1 class="tb-title">Create activity</h1>
        <div class="tb-spacer"></div>
      </header>

      <div class="scroller">
        <!-- Cover -->
        <div class="cover-wrap">
          <label class="cover-picker" :class="{ 'has-img': !!form.coverUrl }">
            <input type="file" accept="image/*" hidden @change="onPickCover" />
            <img v-if="form.coverUrl" :src="form.coverUrl" alt="cover" class="cover-img" />
            <div v-else class="cover-placeholder">
              <svg viewBox="0 0 24 24" class="ico"><path d="M12 5v14M5 12h14"/></svg>
              <span>Upload cover</span>
            </div>
          </label>
        </div>

        <!-- Form -->
        <form class="form" @submit.prevent="submit">
          <div class="input">
            <label>Name</label>
            <input ref="firstInput" v-model="form.title" type="text" autocomplete="off" placeholder="Activity name" />
          </div>

          <!-- Aesthetic stacked date range -->
          <div class="input">
            <label>Date & Time</label>
            <div class="range-stack">
              <input
                class="field top"
                v-model="form.start"
                type="datetime-local"
                aria-label="Start time"
                placeholder="Start"
              />
              <span class="range-chip" aria-hidden="true">to</span>
              <div class="divider" aria-hidden="true"></div>
              <input
                class="field bottom"
                v-model="form.end"
                type="datetime-local"
                aria-label="End time"
                placeholder="End"
              />
            </div>
            <p v-if="form.start && form.end && form.end < form.start" class="hint warn">End must be after start</p>
          </div>

          <div class="input">
            <label>Location</label>
            <input v-model="form.location" type="text" placeholder="Venue / City" />
          </div>

          <div class="input">
            <label>Description</label>
            <textarea v-model="form.description" rows="3" placeholder="What’s special about this event?"></textarea>
          </div>

          <div class="input">
            <label>Category</label>
            <select v-model="form.category">
              <option value="" disabled>Select category</option>
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <p v-if="err" class="err">{{ err }}</p>

          <div class="actions">
            <button type="button" class="btn ghost" @click="open=false">Cancel</button>
            <button type="submit" class="btn primary" :disabled="!canSubmit || loading">
              {{ loading ? 'Saving…' : 'Create' }}
            </button>
          </div>

          <div class="safe-bottom"></div>
        </form>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* Light theme tokens */
.page {
  --page-solid: #f7f8fc;
  --card: #ffffff;
  --text: #0f1115;
  --muted: #586174;
  --border: #e6e8f0;
  --ring: #3b82f6;
  --ring-soft: rgba(59, 130, 246, 0.18);
  --shadow: 0 10px 30px rgba(0,0,0,0.06);
  --shadow-soft: 0 6px 18px rgba(0,0,0,0.05);
  --btn-primary: #0ea5e9;
  --btn-primary-ink: #ffffff;
  --btn-primary-hover: #0284c7;
}

/* Page: uses random gradient if provided */
.page {
  position: fixed; inset: 0; z-index: 60;
  background: var(--page-bg, var(--page-solid));
  color: var(--text);
  display: grid; grid-template-rows: auto 1fr;
}
.page-up-enter-active, .page-up-leave-active {
  transition: transform .28s cubic-bezier(.2,.7,.2,1), opacity .3s ease;
}
.page-up-enter-from, .page-up-leave-to { transform: translateY(100%); opacity: .85; }

/* Top bar */
.topbar {
  height: 58px; display: grid; grid-template-columns: 58px 1fr 58px; align-items: center;
  padding: env(safe-area-inset-top) 10px 0;
  background: transparent;
  position: sticky; top: 0; z-index: 2;
  backdrop-filter: blur(8px);
}
.tb-title { margin: 0; font-size: 17px; text-align: center; font-weight: 700; letter-spacing: .2px; }
.tb-btn, .tb-spacer { display: inline-flex; align-items: center; justify-content: center; }
.tb-btn {
  -webkit-tap-highlight-color: transparent;
  appearance: none; border: 0; background: rgba(255,255,255,.6); color: var(--text);
  width: 40px; height: 40px; border-radius: 10px; box-shadow: var(--shadow-soft);
}
.tb-btn:active { transform: scale(.96); }
.ico { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.6; }

.scroller { overflow: auto; -webkit-overflow-scrolling: touch; }

/* Cover */
.cover-wrap { padding: 16px 16px 0; }
.cover-picker {
  display: block; border-radius: 18px; overflow: hidden; background: rgba(255,255,255,.7);
  border: 1px dashed var(--border);
  box-shadow: var(--shadow-soft);
  transition: border-color .2s ease, box-shadow .2s ease, transform .08s ease, background .2s ease;
  cursor: pointer;
  backdrop-filter: blur(4px);
}
.cover-picker:hover { border-color: #cfd6e6; box-shadow: 0 10px 22px rgba(10,50,120,.08); }
.cover-picker:active { transform: scale(.996); }
.cover-picker.has-img { border-style: solid; background: var(--card); }
.cover-img { display: block; width: 100%; height: auto; aspect-ratio: 16/9; object-fit: cover; }
.cover-placeholder {
  height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 6px; color: var(--muted); font-weight: 600;
}

/* Form */
.form { padding: 14px 16px 16px; }
.input { margin: 14px 0; }
.input label { display: block; font-size: 12px; opacity: .9; margin-bottom: 8px; font-weight: 700; letter-spacing: .2px; color: #2a3243; }
.input input, .input textarea, .input select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 12px;
  color: var(--text);
  background: var(--card);
  outline: none; font-size: 15px;
  transition: border-color .2s ease, box-shadow .2s ease, background .2s ease, transform .04s ease;
  box-shadow: var(--shadow-soft);
}
.input textarea { resize: vertical; }
.input input:focus, .input textarea:focus, .input select:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px var(--ring-soft), var(--shadow);
}

/* Aesthetic stacked range */
.range-stack {
  position: relative;
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 0;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  padding: 6px;                       /* outer padding for shared card */
  transition: box-shadow .2s ease, border-color .2s ease, transform .04s ease;
}
.range-stack:focus-within {
  border-color: var(--ring);
  box-shadow: 0 0 0 4px var(--ring-soft), var(--shadow);
}
.range-stack .field {
  width: 100%;
  border: 0;
  background: #fff;
  color: var(--text);
  padding: 12px 14px;
  font-size: 15px;
  border-radius: 12px;
  box-shadow: 0 1px 0 rgba(0,0,0,.02);
  outline: none;
}
.range-stack .field.top {
  margin-bottom: 8px;                 /* clean separation inside shared card */
}
.range-stack .field.bottom { margin-top: 8px; }

/* Mid divider and chip */
.range-stack .divider {
  position: absolute; left: 12px; right: 12px; top: calc(50% - 1px);
  height: 2px; background: #eef2f7; border-radius: 2px; pointer-events: none;
}
.range-chip {
  position: absolute; left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  display: inline-flex; align-items: center; justify-content: center;
  height: 22px; padding: 0 8px; font-size: 12px; font-weight: 700; letter-spacing: .3px;
  color: #245aa7; background: #e8f1ff; border: 1px solid #d6e7ff; border-radius: 999px;
  box-shadow: 0 2px 8px rgba(36, 90, 167, .18);
  pointer-events: none;
}

/* Helper text */
.hint { margin-top: 6px; font-size: 12px; color: #6b7280; }
.hint.warn { color: #b42318; }

/* Actions */
.actions { display: flex; gap: 12px; margin-top: 10px; }
.btn {
  -webkit-tap-highlight-color: transparent;
  appearance: none; border: 1px solid var(--border);
  padding: 12px 14px; border-radius: 12px; background: var(--card);
  color: var(--text); font-weight: 700; width: 100%;
  box-shadow: var(--shadow-soft);
  transition: transform .06s ease, box-shadow .2s ease, background .2s ease, border-color .2s ease;
}
.btn:hover { box-shadow: var(--shadow); }
.btn:active { transform: translateY(1px); }
.btn.primary { background: var(--btn-primary); color: var(--btn-primary-ink); border-color: transparent; }
.btn.primary:hover { background: var(--btn-primary-hover); }
.btn:disabled { opacity: .6; }
.btn.ghost { background: #ffffff; }

/* Safe bottom on iOS */
.safe-bottom { height: calc(env(safe-area-inset-bottom, 0px) + 10px); }

/* Reduce motion */
@media (prefers-reduced-motion: reduce) {
  .page-up-enter-active, .page-up-leave-active { transition: none; }
  .btn, .cover-picker, .range-stack { transition: none; }
}
</style>
