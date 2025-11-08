<script setup lang="ts">
import { onMounted, computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSportaStore, eventStruct, participantsStruct } from '@/stores/sporta';

const route = useRoute();
const router = useRouter();
const sportaStore = useSportaStore();
const user: participantsStruct = {
  id: 1,
  exp: 1000,
  subevents: [],
  subCat: []
};
const eventId = computed(() => Number(route.params.id));
const event = ref<eventStruct | null>(null);
const isSubscribed = ref(false);
const isLoading = ref(false);

// 格式化日期
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 返回運動資訊頁面
const goBack = () => {
  router.push('/sporta');
};

// 訂閱/取消訂閱活動
const toggleSubscription = async () => {
  if(!isSubscribed.value){
    sportaStore.subEvent(eventId.value,user);
  }else{
    sportaStore.unSubEvent(eventId.value,user);
  }
};

// 處理圖片載入錯誤
const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  if (target && !target.dataset.fallbackUsed) {
    // 標記已使用fallback，避免無限循環
    target.dataset.fallbackUsed = 'true';
    // 使用現有的運動圖片作為fallback
    target.src = '/images/sporta/jog.png';
  }
};

// 獲取活動詳情
const fetchEventDetail = async () => {
  await sportaStore.fetchEvents();
  const foundEvent = sportaStore.events.find(e => e.id === eventId.value);
  if (foundEvent) {
    event.value = foundEvent;
    // 檢查是否已訂閱 (模擬邏輯)
    isSubscribed.value = Math.random() > 0.5; // 隨機模擬訂閱狀態
  }
};

onMounted(() => {
  fetchEventDetail();
});
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 頂部導航 -->
    <div class="bg-white shadow-sm border-b">
      <div class="max-w-4xl mx-auto px-4 py-3">
        <div class="flex items-center">
          <button 
            @click="goBack"
            class="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            返回運動資訊
          </button>
        </div>
      </div>
    </div>

    <!-- 活動詳情內容 -->
    <div v-if="event" class="max-w-4xl mx-auto px-4 py-6">
      <!-- 活動主圖 -->
      <div class="relative mb-6">
        <img 
          :src="event.image || '/images/sporta/jog.png'" 
          :alt="event.title"
          class="w-full h-64 md:h-80 object-cover rounded-lg shadow-lg"
          @error="handleImageError"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-lg"></div>
        <div class="absolute bottom-4 left-4 text-white">
          <h1 class="text-2xl md:text-3xl font-bold mb-2">{{ event.title }}</h1>
          <p class="text-sm md:text-base opacity-90">{{ event.organizer }}</p>
        </div>
      </div>

      <!-- 活動資訊卡片 -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">活動資訊</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <!-- 時間 -->
          <div class="flex items-start">
            <div class="bg-blue-100 p-2 rounded-lg mr-3">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <div>
              <h3 class="font-medium text-gray-800">活動時間</h3>
              <p class="text-gray-600">{{ formatDate(event.date) }}</p>
            </div>
          </div>

          <!-- 地點 -->
          <div class="flex items-start">
            <div class="bg-green-100 p-2 rounded-lg mr-3">
              <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
            </div>
            <div>
              <h3 class="font-medium text-gray-800">活動地點</h3>
              <p class="text-gray-600">{{ event.location }}</p>
            </div>
          </div>
        </div>

        <!-- 活動分類 -->
        <div class="mb-6">
          <h3 class="font-medium text-gray-800 mb-2">活動分類</h3>
          <div class="flex flex-wrap gap-2">
            <span 
              v-for="category in event.category" 
              :key="category"
              class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
            >
              {{ category }}
            </span>
          </div>
        </div>

        <!-- 參與者 -->
        <div v-if="event.participants.length > 0" class="mb-6">
          <h3 class="font-medium text-gray-800 mb-2">參與者</h3>
          <p class="text-gray-600">目前已有 {{ event.participants.length }} 人報名參加此活動</p>
        </div>
      </div>

      <!-- 活動描述 -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">活動說明</h2>
        <div class="space-y-4">
          <div v-for="(desc, index) in event.description" :key="index">
            <p 
              :class="index === 0 ? 'text-lg font-medium text-gray-800' : 'text-gray-600 leading-relaxed'"
            >
              {{ desc }}
            </p>
          </div>
        </div>
      </div>

      <!-- 底部操作按鈕 -->
      <div class="sticky bottom-4 bg-white rounded-lg shadow-lg p-4">
        <div class="flex gap-3">
          <button 
            @click="goBack"
            class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-3 px-4 round-lg transition-colors"
          >
            返回列表
          </button>
          <button 
            @click="toggleSubscription"
            :disabled="isLoading"
            :class="[
              'flex-1 font-medium py-3 px-4 rounded-lg transition-colors',
              isSubscribed 
                ? 'bg-secondary-500 hover:bg-secondary-600 text-white' 
                : 'bg-main-500 hover:bg-main-600 text-white',
              isLoading ? 'opacity-50 cursor-not-allowed' : ''
            ]"
          >
            <span v-if="isLoading">處理中...</span>
            <span v-else>{{ isSubscribed ? '取消報名' : '立即報名' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 載入中狀態 -->
    <div v-else class="max-w-4xl mx-auto px-4 py-12 text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p class="text-gray-600">載入活動詳情中...</p>
    </div>
  </div>
</template>

<style scoped>
/* 確保圖片錯誤時的回退樣式 */
img[src=""] {
  display: none;
}

/* 為預設圖片提供更好的視覺效果 */
img[src="/images/sporta/jog.png"] {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  object-fit: cover;
}

/* 防止圖片載入時的閃爍 */
img {
  background-color: #f3f4f6;
  transition: opacity 0.3s ease-in-out;
}

/* 添加載入狀態 */
img[data-fallback-used="true"] {
  opacity: 0.8;
}
</style>
