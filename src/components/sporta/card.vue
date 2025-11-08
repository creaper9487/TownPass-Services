<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { eventInfo } from '@/stores/sporta'

const props = defineProps({
  event: { type: eventInfo, required: true },
  // external control if needed
  modelValue: { type: Boolean, default: undefined }, // v-model
  defaultOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'open', 'close', 'register', 'cancel'])

const cardRef = ref(null)
const portalOpenUncontrolled = ref(props.defaultOpen)
const usingControlled = computed(() => props.modelValue !== undefined)
const isOpen = computed({
  get: () => (usingControlled.value ? !!props.modelValue : portalOpenUncontrolled.value),
  set: (v) => {
    if (!usingControlled.value) portalOpenUncontrolled.value = v
    emit('update:modelValue', v)
    v ? emit('open') : emit('close')
  },
})

function openPortal() {
  if (isOpen.value) return
  isOpen.value = true
  nextTick(runOpenAnimation)
}
function closePortal() {
  if (!isOpen.value) return
  runCloseAnimation().finally(() => {
    isOpen.value = false
  })
}

function onCardKeydown(e) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    openPortal()
  }
}

const portalCardRef = ref(null)
const portalWrapRef = ref(null)
let revertTimer

function measureFlip() {
  const src = cardRef.value?.getBoundingClientRect()
  const dst = portalCardRef.value?.getBoundingClientRect()
  if (!src || !dst) return null
  const dx = src.left - dst.left
  const dy = src.top - dst.top
  const sx = src.width / dst.width
  const sy = src.height / dst.height
  return { dx, dy, sx, sy }
}

function applyFromTransform() {
  const r = measureFlip()
  if (!r) return
  const el = portalCardRef.value
  el.style.setProperty('--dx', `${r.dx}px`)
  el.style.setProperty('--dy', `${r.dy}px`)
  el.style.setProperty('--sx', r.sx)
  el.style.setProperty('--sy', r.sy)
  el.classList.add('from')
  // force reflow
  // eslint-disable-next-line no-unused-expressions
  el.offsetHeight
}

function clearTransforms() {
  const el = portalCardRef.value
  if (!el) return
  el.classList.remove('from')
  el.classList.add('to')
  const onEnd = () => {
    el.classList.remove('to')
    el.removeEventListener('transitionend', onEnd)
  }
  el.addEventListener('transitionend', onEnd)
}

async function runOpenAnimation() {
  applyFromTransform()
  // fade in backdrop
  portalWrapRef.value?.classList.add('backdrop-in')
  // go to identity transform
  clearTransforms()
}

function runCloseAnimation() {
  return new Promise((resolve) => {
    const el = portalCardRef.value
    if (!el) return resolve()
    // set back to "from" transform values based on current geometry
    const r = measureFlip()
    if (!r) return resolve()
    el.style.setProperty('--dx', `${r.dx}px`)
    el.style.setProperty('--dy', `${r.dy}px`)
    el.style.setProperty('--sx', r.sx)
    el.style.setProperty('--sy', r.sy)

    // trigger back transition
    el.classList.add('to') // ensure we are at identity first
    // force reflow
    // eslint-disable-next-line no-unused-expressions
    el.offsetHeight
    el.classList.remove('to')
    el.classList.add('from')
    portalWrapRef.value?.classList.remove('backdrop-in')

    const onEnd = () => {
      el.classList.remove('from')
      el.removeEventListener('transitionend', onEnd)
      resolve()
    }
    el.addEventListener('transitionend', onEnd)
    // safety fallback
    clearTimeout(revertTimer)
    revertTimer = setTimeout(resolve, 320)
  })
}

function onEsc(e) {
  if (e.key === 'Escape') closePortal()
}

onMounted(() => {
  window.addEventListener('keydown', onEsc)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onEsc)
  clearTimeout(revertTimer)
})
</script>

<template>
  <!-- List card (click to open) -->
  <article
    ref="cardRef"
    class="event-card"
    role="button"
    tabindex="0"
    aria-haspopup="dialog"
    :aria-expanded="isOpen ? 'true' : 'false'"
    @click="openPortal"
    @keydown="onCardKeydown"
  >
    <div class="cover-wrap">
      <img class="cover" :src="event.cover" :alt="event.title" loading="lazy" />
      <div class="cover-gradient"></div>
      <div class="chip" v-if="event.category">{{ event.category }}</div>
    </div>

    <div class="meta">
      <h3 class="title">{{ event.title }}</h3>
      <div class="row">
        <svg viewBox="0 0 24 24" class="i"><path d="M6 2h12a2 2 0 0 1 2 2v16l-8-4-8 4V4a2 2 0 0 1 2-2z"/></svg>
        <span>{{ event.organizer }}</span>
      </div>
      <div class="row">
        <svg viewBox="0 0 24 24" class="i"><path d="M6 8h12M6 12h12M6 16h12"/></svg>
        <span>{{ event.starttime }}</span>
      </div>
      <div class="row">
        <svg viewBox="0 0 24 24" class="i"><path d="M12 21s-7-4.5-7-10a7 7 0 1 1 14 0c0 5.5-7 10-7 10z"/><circle cx="12" cy="11" r="3"/></svg>
        <span>{{ event.location }}</span>
      </div>
    </div>
  </article>

  <!-- Popup overlay -->
  <Teleport to="body">
    <div
      v-if="isOpen"
      ref="portalWrapRef"
      class="portal-wrap"
      role="dialog"
      aria-modal="true"
      @click.self="closePortal"
    >
      <div ref="portalCardRef" class="portal-card" @click.stop>
        <button class="close" aria-label="close" @click="closePortal">
          <svg viewBox="0 0 24 24" class="i"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>

        <div class="portal-cover">
          <img :src="event.cover" :alt="event.title" />
          <div class="portal-cover-grad"></div>
          <div class="portal-chip" v-if="event.category">{{ event.category }}</div>
        </div>

        <div class="portal-body">
          <h2 class="portal-title">{{ event.title }}</h2>

          <div class="kv">
            <div class="item">
              <label>主辦</label>
              <p>{{ event.organizer }}</p>
            </div>
            <div class="item">
              <label>時間</label>
              <p>{{ event.starttime }}<span v-if="event.endtime"> — {{ event.endtime }}</span></p>
            </div>
            <div class="item">
              <label>地點</label>
              <p>{{ event.location }}</p>
            </div>
            <div class="item" v-if="event.capacity">
              <label>名額</label>
              <p>{{ event.capacity }}</p>
            </div>
            <div class="item" v-if="event.price !== undefined">
              <label>費用</label>
              <p>{{ event.price === 0 ? '免費' : `NT$ ${event.price}` }}</p>
            </div>
          </div>

          <p v-if="event.description" class="desc">{{ event.description }}</p>

          <slot name="details"></slot>
        </div>

        <div class="actions">
          <button class="btn primary" @click="$emit('register', event)">報名</button>
          <button class="btn ghost" @click="$emit('cancel', event)">取消</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* base list card */
.event-card {
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,.22), rgba(255,255,255,.12));
  border: 1px solid var(--glass-border, rgba(255,255,255,.25));
  backdrop-filter: blur(var(--blur, 10px));
  -webkit-backdrop-filter: blur(var(--blur, 10px));
  box-shadow: 0 10px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.25);
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
  cursor: pointer; outline: none;
}
.event-card:focus { box-shadow: 0 10px 36px rgba(0,0,0,.4), 0 0 0 2px rgba(56,132,255,.55) inset; }
.event-card:hover { transform: translateY(-2px); }
.cover-wrap { position: relative; aspect-ratio: 16/9; background: rgba(0,0,0,.3); }
.cover { width: 100%; height: 100%; object-fit: cover; display: block; }
.cover-gradient { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,.25) 100%); pointer-events: none; }
.chip { position: absolute; top: 10px; right: 10px; padding: 6px 10px; font-size: 12px; color: #fff; background: rgba(0,0,0,.5); border: 1px solid rgba(255,255,255,.25); border-radius: 999px; backdrop-filter: blur(6px); }

.meta { padding: 12px 14px 14px; color: var(--fg, #fff); }
.title { margin: 0 0 8px; font-size: 16px; line-height: 1.3; letter-spacing: .2px; }
.row { display: flex; align-items: center; gap: 8px; color: var(--muted, rgba(255,255,255,.8)); font-size: 13px; margin-top: 6px; min-height: 20px; }
.i { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.6; }

/* portal overlay */
.portal-wrap {
  position: fixed; inset: 0; display: grid; place-items: center;
  padding: 16px; z-index: 60;
  background: rgba(6,10,18,0); /* start transparent */
  -webkit-backdrop-filter: blur(0px);
  backdrop-filter: blur(0px);
  transition: background 220ms ease, backdrop-filter 220ms ease;
}
.portal-wrap.backdrop-in {
  background: rgba(6,10,18,.35);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}

/* popup card target geometry */
.portal-card {
  width: clamp(320px, 92vw, 560px);
  max-height: 86vh;
  overflow: hidden;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255,255,255,.26), rgba(255,255,255,.14));
  border: 1px solid rgba(255,255,255,.35);
  box-shadow: 0 30px 80px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.3);
  transform-origin: top left;
  position: relative;
  /* FLIP states */
  transform: translate3d(0,0,0) scale(1,1);
  opacity: 1;
  transition: transform 260ms cubic-bezier(.2,.7,.2,1), opacity 180ms ease;
}
.portal-card.from {
  transform: translate3d(var(--dx, 0), var(--dy, 0), 0) scale(var(--sx, 1), var(--sy, 1));
  opacity: .6;
}
.portal-card.to {
  transform: translate3d(0,0,0) scale(1,1);
  opacity: 1;
}

/* close button */
.close {
  position: absolute; top: 10px; right: 10px;
  width: 36px; height: 36px; border-radius: 10px; border: 1px solid rgba(255,255,255,.35);
  background: rgba(0,0,0,.25); color: #fff; display: grid; place-items: center;
  cursor: pointer; z-index: 2;
  backdrop-filter: blur(6px);
}
.close .i { width: 18px; height: 18px; }

/* portal content */
.portal-cover { position: relative; aspect-ratio: 16/9; background: rgba(0,0,0,.3); }
.portal-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.portal-cover-grad { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,.25) 100%); }
.portal-chip { position: absolute; top: 12px; right: 12px; padding: 6px 10px; font-size: 12px; color: #fff; background: rgba(0,0,0,.5); border: 1px solid rgba(255,255,255,.25); border-radius: 999px; backdrop-filter: blur(6px); }

.portal-body { padding: 14px; color: #fff; }
.portal-title { margin: 0 0 10px; font-size: 20px; line-height: 1.3; letter-spacing: .2px; }
.kv { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px; }
@media (min-width: 520px) { .kv { grid-template-columns: repeat(4, 1fr); } }
.kv .item label { display: block; font-size: 11px; opacity: .85; letter-spacing: .3px; margin-bottom: 4px; }
.kv .item p { margin: 0; font-size: 13px; }
.desc {
  margin-top: 10px; padding: 10px 12px;
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.18);
  border-radius: 12px; line-height: 1.5; font-size: 13px;
}

.actions {
  position: sticky; bottom: 0; left: 0; right: 0;
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  padding: 10px 14px 14px;
  background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,.25) 40%, rgba(0,0,0,.35) 100%);
  backdrop-filter: blur(8px);
}
.btn {
  appearance: none; border: 0; border-radius: 12px;
  padding: 12px 14px; font-size: 14px; font-weight: 600; letter-spacing: .2px;
  transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease, opacity 120ms ease;
  cursor: pointer;
}
.btn:active { transform: translateY(1px); }
.btn.primary { color: #0b1221; background: linear-gradient(180deg, #8fd3ff, #5ab6ff); box-shadow: 0 6px 20px rgba(90,182,255,.45), inset 0 1px 0 rgba(255,255,255,.6); }
.btn.ghost { color: #fff; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.3); box-shadow: inset 0 1px 0 rgba(255,255,255,.25); }
</style>
