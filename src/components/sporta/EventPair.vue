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

const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

/* ========= 真實資料來源（Pinia store） ========= */
// 將後端 event 轉成卡片顯示需要的 shape
function mapEventToCard(e) {
  return {
    id: e.id,
    title: e.title,
    cover: e.image,
    location: e.location,
    time: e.starttime || e.endtime || '',
    host: e.organizer,
    tags: [e.category, e.organizer].filter(Boolean)
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
    batch.push(mapEventToCard(src[idx]))
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
    <div v-if="open" class="ep-overlay" :style="{ '--bg': gradient }" @click.self="open=false">
      <!-- Top bar -->
      <header class="ep-top">
        <button class="icon ghost" @click="open=false" aria-label="Close">
          <svg viewBox="0 0 24 24"><path d="M6 6l12 12M6 18L18 6"/></svg>
        </button>
        <h2>Event Pair</h2>
        <button class="icon" title="Refresh" :disabled="loading" @click="loadNextPair">
          <svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 15.3-6.3l1.7-1.7v6h-6l2.2-2.2A7 7 0 1 0 19 12h2a9 9 0 1 1-18 0z"/></svg>
        </button>
      </header>

      <!-- Loader -->
      <div v-if="loading" class="loader">
        <div class="spinner"></div>
        <p>Finding a great match…</p>
      </div>

      <!-- Cards -->
      <div v-else class="stack">
        <!-- Back card（次序 2）-->
        <article v-if="cards[1]" class="card back">
          <img class="cover" :src="cards[1].cover" :alt="cards[1].title" />
          <div class="meta">
            <h3>{{ cards[1].title }}</h3>
            <p class="loc">{{ cards[1].location }} · {{ cards[1].time }}</p>
          </div>
        </article>

        <!-- Front card（次序 1，可滑）-->
        <article
          v-if="active"
          class="card front"
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
          <img class="cover" :src="active.cover" :alt="active.title" />
          <div class="meta">
            <h3>{{ active.title }}</h3>
            <p class="loc">{{ active.location }} · {{ active.time }}</p>
            <div class="tags">
              <span v-for="(t,i) in active.tags" :key="t" class="tag" :style="{ background: tagColor(i) }">{{ t }}</span>
            </div>
          </div>

          <!-- Like/Nope badges -->
          <div class="badge like" :style="{ opacity: likeBadge ? strength : 0 }">LIKE</div>
          <div class="badge nope" :style="{ opacity: !likeBadge ? strength : 0 }">NOPE</div>
        </article>

        <!-- Actions -->
        <div class="actions">
          <button class="act nope" @click="commitDecision('nope')">
            <svg viewBox="0 0 24 24"><path d="M7 7l10 10M17 7L7 17"/></svg>
          </button>
          <button class="act like" @click="commitDecision('like')">
            <svg viewBox="0 0 24 24"><path d="M12 21s-7-4.35-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.65-7 10-7 10z"/></svg>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* Overlay */
.ep-overlay{
  position: fixed; inset: 0; z-index: 70;
  display: grid; grid-template-rows: auto 1fr;
  background: var(--bg, linear-gradient(135deg,#f7faff,#eef6ff));
  color: #0f1115;
}
.fade-enter-active,.fade-leave-active{ transition: opacity .24s ease }
.fade-enter-from,.fade-leave-to{ opacity: 0 }

/* Top bar */
.ep-top{
  display:flex; align-items:center; justify-content:space-between;
  padding: 12px 14px; gap: 10px;
}
.ep-top h2{ margin:0; font-weight:800; letter-spacing:.3px; font-size:18px; }
.icon{
  appearance:none; border:1px solid #e6e8f0; background:#fff; width:40px;height:40px;border-radius:12px;
  display:grid; place-items:center; box-shadow: 0 6px 18px rgba(0,0,0,.06);
}
.icon.ghost{ background: #fff }
.icon:disabled{ opacity:.6 }
.icon svg{ width:18px;height:18px; fill:none; stroke: currentColor; stroke-width:1.6 }

/* Loader */
.loader{ display:grid; place-items:center; align-content:center; gap:12px; }
.spinner{
  width:48px;height:48px;border-radius:50%;
  border:4px solid rgba(14,165,233,.15); border-top-color:#0ea5e9;
  animation: spin 1s linear infinite;
}
.loader p{ color:#334155; font-weight:700 }
@keyframes spin{ to{ transform: rotate(360deg) }}

/* Stack area */
.stack{
  position: relative; padding: 10px 16px 16px; display:grid; align-content:center; justify-items:center; top: 11%;
}

/* Card base */
.card{
  width: min(92vw, 420px);
  aspect-ratio: 3/4;
  background:#fff; border-radius: 18px; overflow:hidden;
  box-shadow: 0 16px 40px rgba(0,0,0,.12), 0 2px 0 rgba(0,0,0,.06);
  border: 1px solid #eef1f7;
  position:absolute;
  user-select:none;
}
.card .cover{ width:100%; height:65%; object-fit: cover; display:block }
.card .meta{ padding: 10px 12px 12px; }
.card h3{ margin: 0 0 4px; font-size: 18px; font-weight: 900 }
.card .loc{ margin:0; color:#64748b; font-size: 13px }
.tags{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px }
.tag{ padding:6px 10px; border-radius:999px; font-weight:800; font-size:12px; border:1px solid #e5ebff }

.front{ z-index: 2; animation: float-in .24s ease }
.back { z-index: 1; transform: translateY(14px) scale(.98); opacity:.9 }

/* Badges */
.badge{
  position:absolute; top:14px; padding:6px 10px; border-radius:10px;
  font-weight:900; letter-spacing:1px; font-size: 14px; pointer-events:none;
  border: 3px solid; transform: rotate(-12deg);
}
.badge.like{ left:14px; color:#16a34a; border-color:#86efac; background: #ecfdf5; }
.badge.nope{ right:14px; color:#dc2626; border-color:#fecaca; background:#fff1f2; transform: rotate(12deg) }

/* Actions */
.actions{
  position:absolute; bottom:-72px; display:flex; gap:16px;
}
.act{
  width:58px;height:58px;border-radius:16px; display:grid; place-items:center;
  background:#fff; border:1px solid #e6e8f0; box-shadow: 0 10px 24px rgba(0,0,0,.08);
  transition: transform .06s ease;
}
.act:active{ transform: translateY(1px) }
.act svg{ width:22px;height:22px; fill:none; stroke: currentColor; stroke-width: 1.8 }
.act.like{ color:#0ea5e9 }
.act.nope{ color:#ef4444 }

/* Animations */
@keyframes float-in{ from{ transform: translateY(10px) scale(.98); opacity:0 } }

@media (prefers-reduced-motion: reduce){
  .fade-enter-active,.fade-leave-active,.card{ transition: none; animation: none }
}
</style>
