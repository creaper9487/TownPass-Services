<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useSportaStore } from '@/stores/sporta'

/**
 * Props
 * - modelValue: 控制開關（由放大鏡頁面星星觸發）
 * - fetcher: 取得下一批卡片的函式，回傳 Promise<{ items: CardItem[] }>
 * - options: 可調參數（滑動閾值、載入最短時間、主題色、批量大小等）
 */
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  fetcher: { type: Function, default: null },
  options: {
    type: Object,
    default: () => ({
      threshold: 96,            // 滑動決策閾值(px)
      minLoadMs: 500,           // 載入動畫最短時間
      brand: '#0ea5e9',         // 主色
      batchSize: 6,             // 一次抓取的卡片數量
    })
  }
})
const emit = defineEmits(['update:modelValue', 'decide', 'empty'])

/* ========= 時間、地點、類別格式化函數 ========= */
// Format time to Taiwan display format
function formatTaiwanTime(timeString) {
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

// Convert numeric rating to descriptive text
function getRatingDescription(rating) {
  if (!rating || isNaN(rating)) return '尚無評價'
  
  if (rating >= 4.5) return '優秀 (★★★★★)'
  if (rating >= 4.0) return '很好 (★★★★☆)'
  if (rating >= 3.5) return '良好 (★★★☆☆)'
  if (rating >= 3.0) return '普通 (★★★☆☆)'
  if (rating >= 2.0) return '待改進 (★★☆☆☆)'
  return '需要改進 (★☆☆☆☆)'
}

const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

/* ========= 真實資料來源（Pinia store） ========= */
// 將後端 event 轉成卡片顯示需要的 shape
async function mapEventToCard(e) {
  // Get decoded location, category, and rating
  const [location, category, rating] = await Promise.all([
    sporta.grabDecodelocation(e.location),
    sporta.grabDecodecategory(e.category), 
    sporta.fetchOrgar(e.organizer)
  ])
  
  return {
    id: e.id,
    title: e.title,
    cover: e.image,
    location: location,
    locationId: e.location,
    time: e.starttime || e.endtime || '',
    starttime: e.starttime,
    endtime: e.endtime,
    host: e.organizer,
    category: category,
    categoryId: e.category,
    rating: rating,
    description: e.description,
    tags: [category, e.organizer].filter(Boolean)
  }
}

let cursor = 0 // 指向下一批開始位置
async function defaultFetcher() {
  // 若尚未有資料，先拉一次 events
  if (!Array.isArray(sporta.events) || sporta.events.length === 0) {
    try { await sporta.fetchEvents() } catch {}
  }
  const src = sporta.events || []
  if (src.length === 0) return { items: [] }

  const size = Number(props.options.batchSize) > 0 ? Number(props.options.batchSize) : 6
  const batch = []
  for (let i = 0; i < size && i < src.length; i++) {
    const idx = (cursor + i) % src.length
    batch.push(await mapEventToCard(src[idx]))
  }
  cursor = (cursor + batch.length) % src.length
  return { items: batch }
}

const fetcher = computed(() => props.fetcher || defaultFetcher)

/* ========= 狀態 ========= */
const loading = ref(false)
const cards = ref([])     // 目前的卡堆（頂端 index 0）
const active = computed(() => cards.value[0] || null)
const gradient = ref('')  // 入場漸層背景
const sporta = useSportaStore()

function randomGradient() {
  const h1 = Math.floor(Math.random()*360)
  const h2 = (h1 + 60 + Math.floor(Math.random()*160)) % 360
  return `linear-gradient(135deg,hsl(${h1} 90% 96%),hsl(${h2} 90% 92%))`
}

/* ========= 載入下一組 pair ========= */
async function loadNextPair() {
  loading.value = true
  const start = performance.now()
  const g = randomGradient()
  gradient.value = g

  const res = await fetcher.value()
  const dt = Math.max(0, props.options.minLoadMs - (performance.now() - start))
  await new Promise(r => setTimeout(r, dt))

  cards.value = (res?.items || []).slice()
  loading.value = false
  if (!cards.value.length) emit('empty')
}

/* ========= 開關與初始 ========= */
watch(open, async v => {
  if (v) {
    await nextTick()
    await loadNextPair()
    bindKeys(true)
  } else {
    bindKeys(false)
    cards.value = []
  }
})

/* ========= Swipe 手勢 ========= */
const drag = reactive({ x: 0, y: 0, r: 0, dragging: false, startX: 0, startY: 0 })
const likeBadge = computed(() => drag.x > 0)
const strength = computed(() => Math.min(1, Math.abs(drag.x) / props.options.threshold))

function onPointerDown(e) {
  if (!active.value) return
  drag.dragging = true
  drag.startX = e.clientX || e.touches?.[0]?.clientX || 0
  drag.startY = e.clientY || e.touches?.[0]?.clientY || 0
}
function onPointerMove(e) {
  if (!drag.dragging) return
  const x = (e.clientX || e.touches?.[0]?.clientX || 0) - drag.startX
  const y = (e.clientY || e.touches?.[0]?.clientY || 0) - drag.startY
  drag.x = x; drag.y = y; drag.r = x * 0.06
}
async function onPointerUp() {
  if (!drag.dragging) return
  drag.dragging = false
  const decided =
    drag.x > props.options.threshold ? 'like' :
    drag.x < -props.options.threshold ? 'nope' : null
  if (decided) {
    await commitDecision(decided, true)
  } else {
    drag.x = drag.y = drag.r = 0
  }
}

async function commitDecision(type, viaSwipe=false) {
  const top = active.value
  if (!top) return
  // 滑出動畫：把卡片飛出去
  if (viaSwipe) {
    drag.x = (type === 'like' ? 1 : -1) * (window.innerWidth * 0.9)
    drag.r = (type === 'like' ? 1 : -1) * 25
    await new Promise(r => setTimeout(r, 200))
  }
  emit('decide', { type, item: top })
  // 右滑 / like -> 對活動進行訂閱
  if (type === 'like') {
    try {
      await sporta.subEvent(top.id)
    } catch (e) {
      console.warn('Subscription failed:', e)
    }
  }
  // 移除頂卡
  cards.value.shift()
  drag.x = drag.y = drag.r = 0

  // 若這組用完，載入下一組
  if (!cards.value.length) {
    await loadNextPair()
  }
}

/* ========= 快捷鍵 ========= */
function onKey(e) {
  if (!open.value || !active.value) return
  if (e.key === 'ArrowRight') { e.preventDefault(); commitDecision('like') }
  if (e.key === 'ArrowLeft')  { e.preventDefault(); commitDecision('nope') }
}
function bindKeys(v){ (v?window.removeEventListener:window.addEventListener)('keydown', onKey); if(v) window.addEventListener('keydown', onKey) }

/* ========= UI helpers ========= */
function tagColor(i) {
  const hues = [205, 150, 95, 270, 15]
  const h = hues[i % hues.length]
  return `hsl(${h} 70% 96%)`
}
</script>

<template>
  <transition name="fade">
    <div v-if="open" class="fixed inset-0 z-[70] bg-grey-50" :style="{ background: gradient }" @click.self="open=false">
      <!-- Top bar -->
      <header class="flex items-center justify-between px-4 py-3 gap-3">
        <button 
          class="w-10 h-10 bg-white border border-grey-200 rounded-xl flex items-center justify-center shadow-sm transition-colors duration-200 hover:bg-grey-50"
          @click="open=false" 
          aria-label="Close">
          <svg class="w-5 h-5 stroke-grey-800" viewBox="0 0 24 24" fill="none" stroke-width="1.6"><path d="M6 6l12 12M6 18L18 6"/></svg>
        </button>
        <h2 class="text-lg font-extrabold tracking-wide text-grey-800">Event Pair</h2>
        <button 
          class="w-10 h-10 bg-white border border-grey-200 rounded-xl flex items-center justify-center shadow-sm transition-colors duration-200 disabled:opacity-60 hover:bg-grey-50"
          title="Refresh" 
          :disabled="loading" 
          @click="loadNextPair">
          <svg class="w-5 h-5 stroke-grey-800" viewBox="0 0 24 24" fill="none" stroke-width="1.6"><path d="M3 12a9 9 0 0 1 15.3-6.3l1.7-1.7v6h-6l2.2-2.2A7 7 0 1 0 19 12h2a9 9 0 1 1-18 0z"/></svg>
        </button>
      </header>

      <!-- Loader -->
      <div v-if="loading" class="flex flex-col items-center justify-center gap-3 h-full pb-20">
        <div class="w-12 h-12 rounded-full border-4 border-primary-100 border-t-primary-500 animate-spin"></div>
        <p class="text-grey-700 font-bold">尋找活動中…</p>
      </div>

      <!-- Cards -->
      <div v-else class="relative px-4 py-3 flex items-center justify-center h-full pb-32">
        <!-- Back card（次序 2）-->
        <article v-if="cards[1]" class="card-base back-card">
          <div class="relative aspect-video bg-grey-200">
            <img class="w-full h-full object-cover" :src="cards[1].cover" :alt="cards[1].title" loading="lazy" />
            <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20"></div>
            <div class="absolute top-2 right-2 px-2.5 py-1 text-xs text-white bg-primary-500/90 border border-white/25 rounded-full backdrop-blur-sm" v-if="cards[1].category">
              {{ cards[1].category }}
            </div>
          </div>
          <div class="p-3">
            <h3 class="m-0 mb-2 text-base font-bold leading-tight text-grey-800">{{ cards[1].title }}</h3>
            <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
                <path d="M6 2h12a2 2 0 0 1 2 2v16l-8-4-8 4V4a2 2 0 0 1 2-2z"/>
              </svg>
              <span 
                class="cursor-help relative group"
                :title="getRatingDescription(cards[1].rating || 0)"
              >
                {{ cards[1].host }}
              </span>
            </div>
            <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
                <path d="M6 8h12M6 12h12M6 16h12"/>
              </svg>
              <span>{{ formatTaiwanTime(cards[1].starttime) }}</span>
            </div>
            <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
                <path d="M12 21s-7-4.5-7-10a7 7 0 1 1 14 0c0 5.5-7 10-7 10z"/>
                <circle cx="12" cy="11" r="3"/>
              </svg>
              <span>{{ cards[1].location }}</span>
            </div>
          </div>
        </article>

        <!-- Front card（次序 1，可滑）-->
        <article
          v-if="active"
          class="card-base front-card"
          :style="{
            transform: `translate(${drag.x}px, ${drag.y}px) rotate(${drag.r}deg)`
          }"
          @mousedown.prevent="onPointerDown"
          @mousemove.prevent="onPointerMove"
          @mouseup.prevent="onPointerUp"
          @mouseleave.prevent="onPointerUp"
          @touchstart.passive="onPointerDown"
          @touchmove.passive="onPointerMove"
          @touchend.passive="onPointerUp"
        >
          <div class="relative aspect-video bg-grey-200">
            <img class="w-full h-full object-cover" :src="active.cover" :alt="active.title" loading="lazy" />
            <div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20"></div>
            <div class="absolute top-2 right-2 px-2.5 py-1 text-xs text-white bg-primary-500/90 border border-white/25 rounded-full backdrop-blur-sm" v-if="active.category">
              {{ active.category }}
            </div>
          </div>

          <div class="p-3 text-grey-800">
            <h3 class="m-0 mb-2 text-base font-bold leading-tight">{{ active.title }}</h3>
            
            <!-- Host with rating tooltip -->
            <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
                <path d="M6 2h12a2 2 0 0 1 2 2v16l-8-4-8 4V4a2 2 0 0 1 2-2z"/>
              </svg>
              <span 
                class="cursor-help relative group"
                :title="getRatingDescription(active.rating || 0)"
              >
                {{ active.host }}
                <div class="absolute bottom-full left-0 mb-2 px-2 py-1 bg-grey-800 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10 pointer-events-none">
                  {{ getRatingDescription(active.rating || 0) }}
                </div>
              </span>
            </div>

            <!-- Time -->
            <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
                <path d="M6 8h12M6 12h12M6 16h12"/>
              </svg>
              <span>{{ formatTaiwanTime(active.starttime) }}</span>
            </div>

            <!-- Location -->
            <div class="flex items-center gap-2 text-grey-600 text-sm mt-1.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 stroke-current" fill="none" stroke-width="2">
                <path d="M12 21s-7-4.5-7-10a7 7 0 1 1 14 0c0 5.5-7 10-7 10z"/>
                <circle cx="12" cy="11" r="3"/>
              </svg>
              <span>{{ active.location }}</span>
            </div>

            <!-- Description if available -->
            <p v-if="active.description" class="mt-3 p-3 bg-grey-50 border border-grey-200 rounded-xl leading-relaxed text-sm text-grey-700 line-clamp-3">
              {{ active.description }}
            </p>

            <!-- Tags -->
            <div class="flex gap-2 flex-wrap mt-2">
              <span v-for="(t,i) in active.tags" :key="t" class="px-2.5 py-1.5 rounded-full font-extrabold text-xs border border-grey-200 bg-white" :style="{ background: tagColor(i) }">{{ t }}</span>
            </div>
          </div>

          <!-- Like/Nope badges -->
          <div 
            class="absolute top-3.5 left-3.5 px-2.5 py-1.5 rounded-lg font-black tracking-wider text-sm border-4 border-green-300 bg-green-50 text-green-600 pointer-events-none -rotate-12"
            :style="{ opacity: likeBadge ? strength : 0 }">
            LIKE
          </div>
          <div 
            class="absolute top-3.5 right-3.5 px-2.5 py-1.5 rounded-lg font-black tracking-wider text-sm border-4 border-warn-100 bg-warn-50 text-warn-200 pointer-events-none rotate-12"
            :style="{ opacity: !likeBadge ? strength : 0 }">
            NOPE
          </div>
        </article>

        <!-- Actions -->
        <div class="absolute bottom-0 flex gap-4 pb-16">
          <button 
            class="w-14 h-14 rounded-2xl bg-white border border-grey-200 flex items-center justify-center shadow-md transition-transform duration-75 active:translate-y-0.5 hover:bg-grey-50"
            @click="commitDecision('nope')">
            <svg class="w-5 h-5 stroke-warn-200" viewBox="0 0 24 24" fill="none" stroke-width="1.8"><path d="M7 7l10 10M17 7L7 17"/></svg>
          </button>
          <button 
            class="w-14 h-14 rounded-2xl bg-white border border-grey-200 flex items-center justify-center shadow-md transition-transform duration-75 active:translate-y-0.5 hover:bg-grey-50"
            @click="commitDecision('like')">
            <svg class="w-5 h-5 stroke-primary-500" viewBox="0 0 24 24" fill="none" stroke-width="1.8"><path d="M12 21s-7-4.35-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.65-7 10-7 10z"/></svg>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* Fade transition */
.fade-enter-active, .fade-leave-active { 
  transition: opacity 0.24s ease;
}
.fade-enter-from, .fade-leave-to { 
  opacity: 0;
}

/* Card base styling */
.card-base {
  width: min(92vw, 420px);
  aspect-ratio: 3/4;
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12), 0 2px 0 rgba(0, 0, 0, 0.06);
  border: 1px solid #eef1f7;
  position: absolute;
  user-select: none;
  display: flex;
  flex-direction: column;
}

/* Ensure proper image aspect ratio */
.card-base .aspect-video {
  aspect-ratio: 16/9;
  flex-shrink: 0;
}

/* Line clamp utility */
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Front card animation */
.front-card {
  z-index: 2;
  animation: float-in 0.24s ease;
}

/* Back card positioning */
.back-card {
  z-index: 1;
  transform: translateY(14px) scale(0.98);
  opacity: 0.9;
}

/* Float in animation */
@keyframes float-in {
  from {
    transform: translateY(10px) scale(0.98);
    opacity: 0;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .fade-enter-active, 
  .fade-leave-active, 
  .card-base {
    transition: none;
    animation: none;
  }
}
</style>
