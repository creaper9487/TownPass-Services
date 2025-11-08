<template>
  <div class="min-h-screen bg-grey-50 py-8">
    <div class="container mx-auto px-4">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-grey-800 mb-4">運動活動與賽事</h1>
        <p class="text-lg text-grey-600">探索社區中精彩的運動賽事和活動</p>
      </div>

      <!-- Category Filter -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-grey-700 mb-4">篩選分類</h2>
        
        <!-- Search Input -->
        <div class="mb-4">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜尋分類..."
              class="w-full px-4 py-2 pl-10 pr-4 border border-grey-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-grey-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
        </div>

        <!-- Categories with Images (Personal.vue style) -->
        <div class="mb-6">
          <div class="flex flex-row overflow-x-auto gap-4 pb-4">
            <div 
              v-for="category in filteredCategoryObjects" 
              :key="category.id" 
              class="flex-shrink-0 w-64 p-3 border rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-shadow duration-200"
              :class="[
                selectedCategoryObjects.some(sel => sel.id === category.id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-grey-300 hover:border-grey-400'
              ]"
              @click="toggleCategoryObject(category)"
            >
              <div class="relative">
                <img :src="category.img" alt="Category Image" class="w-full h-32 object-cover mb-2 rounded" />
                <span class="bg-gradient-to-br from-transparent to-black absolute inset-0 rounded" />
                <!-- Selection indicator -->
                <div 
                  v-if="selectedCategoryObjects.some(sel => sel.id === category.id)"
                  class="absolute top-2 right-2 bg-primary-500 text-white rounded-full w-6 h-6 flex items-center justify-center"
                >
                  ✓
                </div>
              </div>
              <p class="font-medium text-center">{{ category.name }}</p>
              <p class="text-sm text-grey-600 text-center line-clamp-2">{{ category.description }}</p>
            </div>
          </div>
        </div>

        <!-- Selected Categories Summary -->
        <div v-if="selectedCategoryObjects.length > 0" class="mb-4">

          <div class="flex flex-wrap gap-1">
            <span
              v-for="category in selectedCategoryObjects"
              :key="category.id"
              class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-blue-800"
            >
              {{ category.name }}
              <button
                @click="removeCategoryObject(category)"
                class="ml-1 hover:text-primary-600"
              >
                ×
              </button>
            </span>
          </div>
        </div>
      </div>

      <!-- Events Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div
          v-for="event in filteredEvents"
          :key="event.id"
          class="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 cursor-pointer"
          @click="viewEventDetails(event)"
        >
          <!-- Event Image -->
          <div class="relative h-48 bg-gradient-to-r from-primary-400 to-purple-500 overflow-hidden">
            <img
              :src="getEventImage(event)"
              :alt="event.title"
              class="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
              @error="(e) => handleImageError(e, event)"
            />
            <!-- Gradient overlay for better text readability -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
            <div class="absolute top-4 right-4">
              <span class="bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-medium text-grey-800 shadow-lg">
                {{ formatDate(event.date) }}
              </span>
            </div>
            <!-- Category badge -->
            <div class="absolute top-4 left-4">
              <span class="bg-primary-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium shadow-lg">
                {{ event.category[0] }}
              </span>
            </div>
          </div>

          <!-- Event Content -->
          <div class="p-6">
            <!-- Event Title -->
            <h3 class="text-xl font-bold text-grey-800 mb-2 line-clamp-2">{{ event.title }}</h3>
            
            <!-- Event Organizer -->
            <p class="text-sm text-grey-600 mb-3 flex items-center">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
              </svg>
              主辦單位：{{ event.organizer }}
            </p>

            <!-- Event Location -->
            <p class="text-sm text-grey-600 mb-3 flex items-center">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              地點：{{ event.location }}
            </p>

            <!-- Event Description -->
            <p class="text-grey-700 mb-4 line-clamp-3">{{ event.description[0] }}</p>

            <!-- Categories -->
            <div class="mb-4">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="category in event.category.slice(0, 3)"
                  :key="category"
                  class="inline-block bg-primary-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                >
                  {{ category }}
                </span>
                <span
                  v-if="event.category.length > 3"
                  class="inline-block bg-grey-100 text-grey-600 text-xs px-2 py-1 rounded-full"
                >
                  +{{ event.category.length - 3 }} more
                </span>
              </div>
            </div>

            <!-- Participants -->
            <div class="mb-4">
              <p class="text-sm text-grey-600 mb-2 flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m3 5.197H9m3 0a4 4 0 11-8 0m8 0v3H9v-3m8 0V9a2 2 0 00-2-2H9a2 2 0 00-2 2v12.5"></path>
                </svg>
                參與者：{{ event.participants.length }} 人
              </p>
            </div>

            <!-- Event Status -->
            <div class="mb-4">
              <span
                :class="[
                  'inline-block px-3 py-1 rounded-full text-sm font-medium',
                  getEventStatus(event.date).class
                ]"
              >
                {{ getEventStatus(event.date).text }}
              </span>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3">
              <button
                class="flex-1 bg-primary-500 hover:bg-primary-600 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                @click.stop="viewEventDetails(event)"
              >
                查看詳情
              </button>
              <button
                v-if="getEventStatus(event.date).canRegister"
                class="flex-1 bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                @click.stop="registerForEvent(event)"
              >
                立即報名
              </button>
              <button
                v-else-if="!getEventStatus(event.date).isPast"
                class="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
                disabled
                @click.stop
              >
                報名已截止
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredEvents.length === 0" class="text-center py-12">
        <div class="max-w-md mx-auto">

          <h3 class="text-xl font-medium text-grey-900 mb-2">沒有找到符合條件的活動</h3>
          <p class="text-grey-500">請嘗試選擇不同的分類或稍後再查看新活動。</p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSportaStore, type categoryStruct } from '@/stores/sporta'
import { useConnectionMessage } from '@/composables/useConnectionMessage'

const router = useRouter()
const sportaStore = useSportaStore()
const selectedCategories = ref<string[]>([])
const selectedCategoryObjects = ref<categoryStruct[]>([])
const searchQuery = ref('')
const loading = ref(true)

// Get unique categories from all events
const availableCategories = computed(() => {
  const categories = new Set<string>()
  sportaStore.events.forEach(event => {
    event.category.forEach(cat => categories.add(cat))
  })
  return Array.from(categories).sort()
})

// Get active category objects from store
const availableCategoryObjects = computed(() => {
  return sportaStore.activeCategories
})

// Filter categories based on search query
const filteredCategories = computed(() => {
  if (!searchQuery.value) {
    return availableCategories.value
  }
  return availableCategories.value.filter(category =>
    category.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// Filter category objects based on search query
const filteredCategoryObjects = computed(() => {
  if (!searchQuery.value) {
    return availableCategoryObjects.value
  }
  return availableCategoryObjects.value.filter(category =>
    category.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    category.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// Filter events based on selected categories
const filteredEvents = computed(() => {
  if (selectedCategoryObjects.value.length === 0) {
    return sportaStore.events
  }
  
  return sportaStore.events.filter(event =>
    selectedCategoryObjects.value.some(selectedCategory =>
      event.category.some(eventCategory =>
        eventCategory.toLowerCase().includes(selectedCategory.name.toLowerCase())
      )
    )
  )
})

// Format Unix timestamp to readable date
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Determine event status
const getEventStatus = (timestamp: number) => {
  const now = Date.now() / 1000
  const eventTime = timestamp
  const timeDiff = eventTime - now
  const daysUntilEvent = timeDiff / (24 * 60 * 60)

  if (timeDiff < 0) {
    return {
      text: '活動已結束',
      class: 'bg-grey-200 text-grey-700',
      isPast: true,
      canRegister: false
    }
  } else if (daysUntilEvent <= 1) {
    return {
      text: '報名已截止',
      class: 'bg-red-200 text-red-700',
      isPast: false,
      canRegister: false
    }
  } else if (daysUntilEvent <= 7) {
    return {
      text: '即將截止報名',
      class: 'bg-yellow-200 text-yellow-700',
      isPast: false,
      canRegister: true
    }
  } else {
    return {
      text: '開放報名中',
      class: 'bg-green-200 text-green-700',
      isPast: false,
      canRegister: true
    }
  }
}

// Handle image load errors
const handleImageError = (event: Event, eventData?: any) => {
  const img = event.target as HTMLImageElement
  // Use a gradient background as fallback
  img.style.display = 'none'
  if (img.parentElement) {
    img.parentElement.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
}

// Get event image with fallback
const getEventImage = (event: any) => {
  // Return the image path or a placeholder
  return event.image || '/images/sporta/placeholder.jpg'
}

// Event actions
const viewEventDetails = (event: any) => {
  console.log('檢視活動詳情:', event.title)
  // Navigate to event detail page
  router.push(`/sporta/event/${event.id}`)
}

const registerForEvent = (event: any) => {
  console.log('報名活動:', event.title)
  // Handle event registration logic
  try {
    // 模擬用戶資料 (實際應用中應從用戶商店獲取)
    const user = {
      id: 1,
      exp: 100,
      subevents: [],
      subCat: []
    }
    
    // 調用store的訂閱功能
    sportaStore.subEvent(event.id)
    
    // 提供用戶反饋
    alert(`已成功報名活動：${event.title}`)
  } catch (error) {
    console.error('報名失敗:', error)
    alert('報名失敗，請稍後再試')
  }
}

// Category management functions
const toggleAllCategories = () => {
  selectedCategories.value = []
  selectedCategoryObjects.value = []
  searchQuery.value = ''
}

const toggleCategory = (category: string) => {
  const index = selectedCategories.value.indexOf(category)
  if (index > -1) {
    selectedCategories.value.splice(index, 1)
  } else {
    selectedCategories.value.push(category)
  }
}

const removeCategory = (category: string) => {
  const index = selectedCategories.value.indexOf(category)
  if (index > -1) {
    selectedCategories.value.splice(index, 1)
  }
}

const toggleCategoryObject = (category: categoryStruct) => {
  const index = selectedCategoryObjects.value.findIndex(cat => cat.id === category.id)
  if (index > -1) {
    selectedCategoryObjects.value.splice(index, 1)
  } else {
    selectedCategoryObjects.value.push(category)
  }
}

const removeCategoryObject = (category: categoryStruct) => {
  const index = selectedCategoryObjects.value.findIndex(cat => cat.id === category.id)
  if (index > -1) {
    selectedCategoryObjects.value.splice(index, 1)
  }
}

// Load events and categories on component mount
onMounted(async () => {
  try {
    await sportaStore.fetchAll()  // This fetches both events and categories
  } catch (error) {
    console.error('Failed to load data:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Custom scrollbar for horizontal category scroll */
.overflow-x-auto::-webkit-scrollbar {
  height: 8px;
}

.overflow-x-auto::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.overflow-x-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.overflow-x-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>

