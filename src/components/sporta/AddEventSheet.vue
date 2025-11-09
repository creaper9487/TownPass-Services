<script setup lang="ts">
import { reactive, ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { createEvent } from '@/utils/eventsmock'
import { useSportaStore } from '@/stores/sporta'
import mapboxgl from 'mapbox-gl'
import MapboxDraw from '@mapbox/mapbox-gl-draw'

// Import Mapbox CSS
import 'mapbox-gl/dist/mapbox-gl.css'
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css'

const sportaStore = useSportaStore()

// Mapbox Access Token
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || 'YOUR_MAPBOX_ACCESS_TOKEN'

// Mapbox related variables
let map: mapboxgl.Map | null = null
let draw: MapboxDraw | null = null
const pathCoordinates = ref<[number, number][]>([])
const locationMode = ref<'text' | 'map'>('text') // Toggle between text input and map drawing
const submittingLocation = ref(false)
const locationSubmitError = ref('')
const locationSubmitSuccess = ref(false)

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  categories: { type: Array as () => string[], default: () => ['Running','Cycling','Yoga','Basketball','Hiking'] }
})
const emit = defineEmits(['update:modelValue', 'created'])

const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

// Initialize/destroy map based on locationMode
watch([open, locationMode], ([isOpen, mode]) => {
  if (isOpen && mode === 'map') {
    nextTick(() => initializeMap())
  } else if (map) {
    destroyMap()
  }
})

// lock background scroll
function lockBody(v: boolean) {
  const cls = 'no-scroll'
  if (v) document.body.classList.add(cls)
  else document.body.classList.remove(cls)
}
watch(open, lockBody)
onMounted(() => lockBody(open.value))
onBeforeUnmount(() => {
  lockBody(false)
  destroyMap()
})

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
  coverFile: null as File | null,
  coverUrl: ''
})
const loading = ref(false)
const err = ref('')
const canSubmit = computed(() => {
  const hasBasicInfo = form.title.trim() && form.start && form.end
  const hasLocation = locationMode.value === 'text' 
    ? (form.location || '').trim() // <-- Use (form.location || '')
    : pathCoordinates.value.length >= 2
  return hasBasicInfo && hasLocation
})

// Mapbox initialization
function initializeMap() {
  if (map) return // Already initialized
  
  const container = document.getElementById('map-container')
  if (!container) return

  map = new mapboxgl.Map({
    container: 'map-container',
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [121.5654, 25.0330], // Taipei coordinates
    zoom: 12
  })

  draw = new MapboxDraw({
    displayControlsDefault: false,
    controls: {
      line_string: true, // Allow drawing lines
      trash: true        // Allow deletion
    }
  })

  map.addControl(draw, 'top-left')
  map.on('draw.create', handleDrawCreate)
  map.on('draw.update', handleDrawCreate)
}

function handleDrawCreate(e: any) {
  const feature = e.features[0]
  if (feature && feature.geometry.type === 'LineString') {
    pathCoordinates.value = feature.geometry.coordinates
    console.log('繪製完成，座標點：', pathCoordinates.value)
    locationSubmitSuccess.value = false // Reset success state on new draw
  }
}

async function submitLocationApplication() {
  if (submittingLocation.value || pathCoordinates.value.length < 2) return
  
  locationSubmitError.value = ''
  locationSubmitSuccess.value = false
  submittingLocation.value = true
  
  try {
    // Generate a name based on the path or allow user to provide one
    const locationName = `Route ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`
    
    // For now, submit the first coordinate as the location point
    // If you want to submit the entire path, backend needs to be updated to accept paths
    const firstCoordinate: [number, number] = [
      pathCoordinates.value[0][0],
      pathCoordinates.value[0][1]
    ]
    
    await sportaStore.submitLocation({
      name: locationName,
      coordinates: firstCoordinate
    })
    
    locationSubmitSuccess.value = true
    console.log('位置申請提交成功')
  } catch (error) {
    console.error('位置申請失敗:', error)
    locationSubmitError.value = '提交失敗，請稍後再試'
  } finally {
    submittingLocation.value = false
  }
}

function destroyMap() {
  if (map) {
    map.off('draw.create', handleDrawCreate)
    map.off('draw.update', handleDrawCreate)
    map.remove()
    map = null
    draw = null
  }
}

function onPickCover(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  if (!f) return
  form.coverFile = f
  form.coverUrl = URL.createObjectURL(f)
}

async function submit() {
  err.value = ''
  loading.value = true
  try {
    const payload: any = {
      id: `event-${Date.now()}`,
      title: form.title.trim(),
      organizer: sportaStore.user.userID,
      participants: [],
      category: form.category,
      description: [form.description.trim()], // Backend expects array
      image: form.coverUrl || 'https://picsum.photos/seed/new/800/480',
      start_time: form.start, // Use snake_case
      end_time: form.end      // Use snake_case
    }

    // location field (required - must be string):
    // - Map mode: JSON stringified array of coordinates
    // - Text mode: plain text string
if (locationMode.value === 'map') {
      payload.location = JSON.stringify(pathCoordinates.value)
    } else {
      payload.location = (form.location || '').trim() // <-- Use (form.location || '')
    }
    console.log('Form submitted:', payload)
    await sportaStore.SubmitEvent(payload)
    const created = await createEvent({
      ...payload,
      date: `${form.start} ~ ${form.end}`,
      start: form.start,
      end: form.end,
      cover: payload.image,
      host: payload.organizer,
      starttime: form.start, // Keep for compatibility
      endtime: form.end      // Keep for compatibility
    })
    emit('created', created)
    reset()
    open.value = false
  } catch (e) {
    console.error('Submit error:', e)
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
  pathCoordinates.value = []
  locationSubmitError.value = ''
  locationSubmitSuccess.value = false
  if (draw) {
    draw.deleteAll()
  }
}

// focus first input when open
const firstInput = ref<HTMLInputElement | null>(null)
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
      class="fixed inset-0 z-50 bg-grey-50 grid grid-rows-[auto_1fr]"
      :style="{ background: gradient }"
      role="dialog"
      aria-modal="true"
    >
      <header class="sticky top-0 z-10 h-14 grid grid-cols-[3.5rem_1fr_3.5rem] items-center px-3 bg-white/80 backdrop-blur-md" style="padding-top: env(safe-area-inset-top, 0px)">
        <button class="w-10 h-10 rounded-xl bg-white border border-grey-200 flex items-center justify-center shadow-sm active:scale-95 transition-transform" @click="open=false" aria-label="Close">
          <svg viewBox="0 0 24 24" class="w-5 h-5 stroke-grey-700" fill="none" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
        <h1 class="m-0 text-center text-lg font-bold text-grey-800">建立活動</h1>
        <div></div>
      </header>

      <div class="overflow-auto" style="-webkit-overflow-scrolling: touch">
        <!-- Cover -->
        <div class="p-4 pt-4">
          <label 
            class="block rounded-2xl overflow-hidden border transition-all duration-200 cursor-pointer backdrop-blur-sm"
            :class="form.coverUrl 
              ? 'bg-white border-grey-200 shadow-card' 
              : 'bg-white/70 border-dashed border-grey-300 hover:border-primary-300 hover:shadow-md'"
          >
            <input type="file" accept="image/*" hidden @change="onPickCover" />
            <img v-if="form.coverUrl" :src="form.coverUrl" alt="cover" class="block w-full h-auto aspect-video object-cover" />
            <div v-else class="h-48 flex flex-col items-center justify-center gap-2 text-grey-500 font-semibold">
              <svg viewBox="0 0 24 24" class="w-8 h-8 stroke-current" fill="none" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              <span>上傳封面圖片</span>
            </div>
          </label>
        </div>

        <!-- Form -->
        <form class="px-4 pb-4" @submit.prevent="submit">
          <div class="mb-4">
            <label class="block text-sm font-bold text-grey-800 mb-2">活動名稱</label>
            <input ref="firstInput" v-model="form.title" type="text" autocomplete="off" placeholder="輸入活動名稱" 
              class="w-full border border-grey-200 rounded-xl px-3 py-3 text-grey-800 bg-white outline-none text-base transition-all duration-200 shadow-sm focus:border-primary-500 focus:ring-4 focus:ring-primary-100" />
          </div>

          <!-- Aesthetic stacked date range -->
          <div class="mb-4">
            <label class="block text-sm font-bold text-grey-800 mb-2">日期與時間</label>
            <div class="relative bg-white border border-grey-200 rounded-xl shadow-sm p-1.5 transition-all duration-200 focus-within:border-primary-500 focus-within:ring-4 focus-within:ring-primary-100">
              <input
                class="w-full bg-white text-grey-800 px-3 py-3 text-base rounded-lg outline-none"
                v-model="form.start"
                type="datetime-local"
                aria-label="Start time"
              />
              <span class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 inline-flex items-center justify-center h-5 px-2 text-xs font-bold text-primary-700 bg-primary-50 border border-primary-200 rounded-full shadow-sm pointer-events-none z-10">
                至
              </span>
              <input
                class="w-full bg-white text-grey-800 px-3 py-3 text-base rounded-lg outline-none mt-2"
                v-model="form.end"
                type="datetime-local"
                aria-label="End time"
              />
            </div>
            <p v-if="form.start && form.end && form.end < form.start" class="mt-2 text-xs text-warn-200">結束時間必須晚於開始時間</p>
          </div>

          <div class="mb-4">
            <div class="flex items-center justify-between mb-2">
              <label class="block text-sm font-bold text-grey-800">地點</label>
              <div class="flex gap-2 text-xs">
                <button
                  type="button"
                  @click="locationMode = 'text'"
                  :class="locationMode === 'text' 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-grey-100 text-grey-600 hover:bg-grey-200'"
                  class="px-3 py-1 rounded-full font-semibold transition-colors"
                >
                  選擇地點
                </button>
                <button
                  type="button"
                  @click="locationMode = 'map'"
                  :class="locationMode === 'map' 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-grey-100 text-grey-600 hover:bg-grey-200'"
                  class="px-3 py-1 rounded-full font-semibold transition-colors"
                >
                  繪製路線
                </button>
              </div>
            </div>
            
            <!-- Location select mode -->
            <select 
              v-if="locationMode === 'text'"
              v-model="form.location" 
              class="w-full border border-grey-200 rounded-xl px-3 py-3 text-grey-800 bg-white outline-none text-base transition-all duration-200 shadow-sm focus:border-primary-500 focus:ring-4 focus:ring-primary-100"
            >
              <option value="" disabled>選擇地點</option>
              <option v-for="loc in sportaStore.locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
            </select>
            
            <!-- Map drawing mode -->
            <div v-else>
              <div 
                id="map-container" 
                class="w-full h-80 rounded-xl border border-grey-200 shadow-sm overflow-hidden"
              ></div>
              <div class="mt-3 space-y-2">
                <div class="flex items-center justify-between gap-3">
                  <p class="text-xs text-grey-600 flex-1">
                    <span v-if="pathCoordinates.length === 0">點擊左上角的線條工具開始繪製路線</span>
                    <span v-else class="text-primary-600 font-semibold">✓ 已繪製 {{ pathCoordinates.length }} 個座標點</span>
                  </p>
                  <button
                    v-if="pathCoordinates.length >= 2"
                    type="button"
                    @click="submitLocationApplication"
                    class="bg-primary-500 text-white font-semibold rounded-lg px-4 py-2 text-sm transition-all duration-200 hover:bg-primary-600 active:scale-95 shadow-md disabled:bg-grey-300 disabled:cursor-not-allowed"
                  >
                    {{ submittingLocation ? '提交中...' : locationSubmitSuccess ? '已提交' : '提出位置申請' }}
                  </button>
                </div>
                <p v-if="locationSubmitError" class="text-xs text-warn-200 font-semibold">{{ locationSubmitError }}</p>
                <p v-if="locationSubmitSuccess" class="text-xs text-green-600 font-semibold">✓ 位置申請已成功提交</p>
              </div>
            </div>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-bold text-grey-800 mb-2">活動描述</label>
            <textarea v-model="form.description" rows="3" placeholder="這個活動有什麼特別之處？" 
              class="w-full border border-grey-200 rounded-xl px-3 py-3 text-grey-800 bg-white outline-none text-base transition-all duration-200 shadow-sm resize-vertical focus:border-primary-500 focus:ring-4 focus:ring-primary-100"></textarea>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-bold text-grey-800 mb-2">類別</label>
            <select v-model="form.category"
              class="w-full border border-grey-200 rounded-xl px-3 py-3 text-grey-800 bg-white outline-none text-base transition-all duration-200 shadow-sm focus:border-primary-500 focus:ring-4 focus:ring-primary-100">
              <option value="" disabled>選擇類別</option>
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <p v-if="err" class="text-warn-200 text-sm font-bold mb-4">{{ err }}</p>

          <div class="flex gap-3">
            <button type="button" class="flex-1 bg-white border border-grey-200 text-grey-700 font-semibold rounded-xl py-3 px-4 transition-colors duration-200 hover:bg-grey-50" @click="open=false">取消</button>
            <button type="submit" class="flex-1 bg-primary-500 text-white font-semibold rounded-xl py-3 px-4 transition-colors duration-200 hover:bg-primary-600 disabled:bg-grey-200 disabled:text-grey-400 disabled:cursor-not-allowed">
              {{ loading ? '儲存中…' : '建立活動' }}
            </button>
          </div>

          <div class="safe-bottom"></div>
        </form>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.page-up-enter-active, .page-up-leave-active {
  transition: transform 0.28s cubic-bezier(0.2, 0.7, 0.2, 1), opacity 0.3s ease;
}
.page-up-enter-from, .page-up-leave-to { 
  transform: translateY(100%); 
  opacity: 0.85; 
}

@media (prefers-reduced-motion: reduce) {
  .page-up-enter-active, .page-up-leave-active { 
    transition: none; 
  }
}
</style>
