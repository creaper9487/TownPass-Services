<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { eventInfo, useSportaStore } from '@/stores/sporta'
import { useConnectionMessage } from '@/composables/useConnectionMessage'
import { get } from 'node_modules/axios/index.cjs'
const sportaStore = useSportaStore()
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
  // Prevent body scrolling when portal is open
  document.body.style.overflow = 'hidden'
  nextTick(runOpenAnimation)
}
function closePortal() {
  if (!isOpen.value) return
  runCloseAnimation().finally(() => {
    isOpen.value = false
    // Restore body scrolling when portal is closed
    document.body.style.overflow = ''
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

async function subEvent(e: eventInfo) {
  useConnectionMessage('sporta_notify',{eventName:e.title, eventTime:e.starttime})

  console.log('Subscribing to event:', e)
  if (!e || !e.id) {
    console.error('Event or event ID is undefined:', e)
    return
  }
  try {
    await sportaStore.subEvent(e.id)
    console.log('Successfully subscribed to event:', e.id)
  } catch (error) {
    console.error('Failed to subscribe to event:', error)
  }
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
  // Restore body scrolling if component is unmounted while portal is open
  if (isOpen.value) {
    document.body.style.overflow = ''
  }
})
async function getLocation(id){
  return sportaStore.grabDecodelocation(id)
}
let location = ref('')
let category = ref('')
onMounted(async()=>{
  location.value = await getLocation(props.event.location)
  category.value = await sportaStore.grabDecodecategory(props.event.category)
})

// Format time to Taiwan display format
function formatTaiwanTime(timeString: string): string {
  if (!timeString) return ''
  
  try {
    const date = new Date(timeString)
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    const day = date.getDate()
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    const weekday = weekdays[date.getDay()]
    
    return `${year}年${month}月${day}日 (週${weekday}) ${hours}:${minutes}`
  } catch (error) {
    return timeString
  }
}
</script>

<template>
  <!-- List card (click to open) -->
  <article
    ref="cardRef"
    class="bg-white rounded-2xl shadow-card border border-grey-100 overflow-hidden transition-all duration-200 cursor-pointer outline-none hover:-translate-y-1 hover:shadow-lg focus:ring-2 focus:ring-primary-300"
    role="button"
    tabindex="0"
    aria-haspopup="dialog"
    :aria-expanded="isOpen ? 'true' : 'false'"
    @click="openPortal"
    @keydown="onCardKeydown"
  >
    <div class="relative aspect-video bg-grey-200">
      <img class="w-full h-full object-cover" :src="event.image" :alt="event.title" loading="lazy" />
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20"></div>
      <div class="absolute top-2 right-2 px-2.5 py-1 text-xs text-white bg-primary-500/90 border border-white/25 rounded-full backdrop-blur-sm" v-if="event.category">
        {{ category }}
      </div>
    </div>

    <div class="p-3.5 text-grey-800">
      <h3 class="m-0 mb-2 text-base font-bold leading-tight">{{ event.title }}</h3>
      <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
        <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
          <path d="M6 2h12a2 2 0 0 1 2 2v16l-8-4-8 4V4a2 2 0 0 1 2-2z"/>
        </svg>
        <span>{{ event.organizer }}</span>
      </div>
      <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
        <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
          <path d="M6 8h12M6 12h12M6 16h12"/>
        </svg>
        <span>{{ formatTaiwanTime(event.starttime) }}</span>
      </div>
      <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
        <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
          <path d="M12 21s-7-4.5-7-10a7 7 0 1 1 14 0c0 5.5-7 10-7 10z"/>
          <circle cx="12" cy="11" r="3"/>
        </svg>
        <span>{{ location }}</span>
      </div>
    </div>
  </article>

  <!-- Popup overlay -->
  <Teleport to="body">
    <div
      v-if="isOpen"
      ref="portalWrapRef"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm transition-all duration-300"
      :class="{ 'backdrop-in': isOpen }"
      role="dialog"
      aria-modal="true"
      @click.self="closePortal"
    >
      <div ref="portalCardRef" class="portal-card bg-white rounded-2xl shadow-2xl border border-grey-200 w-full max-w-lg max-h-[86vh] overflow-hidden relative" @click.stop>
        <button class="absolute top-3 right-3 w-9 h-9 rounded-xl bg-white/90 border border-grey-200 text-grey-700 flex items-center justify-center z-10 hover:bg-grey-50 transition-colors shadow-md" aria-label="close" @click="closePortal">
          <svg viewBox="0 0 24 24" class="w-5 h-5 stroke-current" fill="none" stroke-width="2">
            <path d="M6 6l12 12M18 6L6 18"/>
          </svg>
        </button>

        <div class="relative aspect-video bg-grey-200">
          <img :src="event.image" :alt="event.title" class="w-full h-full object-cover" />
          <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20"></div>
          <div class="absolute top-3 left-3 px-3 py-1.5 text-sm font-medium text-white bg-primary-500/90 border border-white/25 rounded-full backdrop-blur-sm" v-if="event.category">
            {{ category }}
          </div>
        </div>

        <div class="p-4 text-grey-800 max-h-[50vh] overflow-y-auto">
          <h2 class="m-0 mb-3 text-xl font-bold leading-tight">{{ event.title }}</h2>

          <div class="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label class="block text-xs text-grey-500 font-medium mb-1">主辦</label>
              <p class="m-0 text-sm text-grey-800">{{ event.organizer }}</p>
            </div>
            <div>
              <label class="block text-xs text-grey-500 font-medium mb-1">時間</label>
              <p class="m-0 text-sm text-grey-800">{{ formatTaiwanTime(event.starttime) }}<span v-if="event.endtime"> — {{ formatTaiwanTime(event.endtime) }}</span></p>
            </div>
            <div>
              <label class="block text-xs text-grey-500 font-medium mb-1">地點</label>
              <p class="m-0 text-sm text-grey-800">{{ location }}</p>
            </div>
            <div v-if="event.capacity">
              <label class="block text-xs text-grey-500 font-medium mb-1">名額</label>
              <p class="m-0 text-sm text-grey-800">{{ event.capacity }}</p>
            </div>
            <div v-if="event.price !== undefined">
              <label class="block text-xs text-grey-500 font-medium mb-1">費用</label>
              <p class="m-0 text-sm text-grey-800">{{ event.price === 0 ? '免費' : `NT$ ${event.price}` }}</p>
            </div>
          </div>

          <p v-if="event.description" class="mt-3 p-3 bg-grey-50 border border-grey-200 rounded-xl leading-relaxed text-sm text-grey-700">
            {{ event.description }}
          </p>

          <slot name="details"></slot>
        </div>

        <div class="sticky bottom-0 left-0 right-0 flex justify-center p-4 bg-gradient-to-t from-white via-white to-transparent">
          <button @click="subEvent(event)" class="px-6 py-3 rounded-xl bg-primary-500 hover:bg-primary-600 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all duration-200 active:scale-95 w-2/3">
            報名
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* FLIP animation states */
.portal-card {
  transform-origin: top left;
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

.backdrop-in {
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
</style>
