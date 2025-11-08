<script setup>
import { ref, onMounted } from 'vue'

/**
 * Upgrade hooks (未來加入):
 * - fetchNotifications(): REST / GraphQL / SSE
 * - markAsRead(id)
 * - filter by unread / system / invites
 */

const loading = ref(true)
const notifications = ref([])

function loadMock() {
  const base = [
    {
      id: 1,
      title: '你的活動報名成功',
      message: '你已成功報名「河濱夜跑訓練」。',
      time: '2 小時前',
      unread: true,
    },
    {
      id: 2,
      title: '主辦方發布了新公告',
      message: '「城市瑜珈晨光場次」活動時間略有調整。',
      time: '昨天',
      unread: true,
    },
    {
      id: 3,
      title: '每日簽到獎勵到帳',
      message: '你獲得了 +35 EXP',
      time: '2 天前',
      unread: false,
    },
    {
      id: 4,
      title: '你有一個新事件搭配推薦',
      message: '根據你的興趣，我們推薦你查看「山林慢跑圈」。',
      time: '3 天前',
      unread: false,
    },
  ]
  return base
}

async function fetchNotifications() {
  loading.value = true
  await new Promise(r => setTimeout(r, 350)) // 模擬延遲
  notifications.value = loadMock()
  loading.value = false
}

function markRead(n) {
  if (!n.unread) return
  n.unread = false
}

onMounted(fetchNotifications)
</script>

<template>
  <div class="min-h-full bg-grey-50">
    <header class="flex justify-between items-center px-4 py-4">
      <h1 class="m-0 text-xl font-bold text-grey-800">通知中心</h1>
      <button 
        class="appearance-none border-0 bg-transparent text-primary-500 font-bold text-sm"
        @click="notifications.forEach(n => n.unread=false)"
      >
        全部標為已讀
      </button>
    </header>

    <div class="px-4 pt-2 pb-4 flex flex-col gap-3">
      <div v-if="loading" class="flex flex-col gap-3">
        <div 
          v-for="i in 5" 
          :key="i"
          class="h-20 rounded-2xl bg-grey-100 animate-pulse"
        ></div>
      </div>

      <transition-group name="fade-slide" tag="div">
        <article
          v-for="n in notifications"
          :key="n.id"
          class="bg-white border border-grey-200 rounded-2xl px-4 py-4 pl-3 flex gap-3 shadow-card cursor-pointer transition-all duration-100 ease-in-out active:scale-[0.98] hover:shadow-lg"
          @click="markRead(n)"
        >
          <div 
            class="w-2 rounded-md transition-colors duration-300"
            :class="n.unread ? 'bg-primary-500' : 'bg-transparent'"
          ></div>

          <div class="flex flex-col gap-1">
            <div class="font-bold text-grey-800">{{ n.title }}</div>
            <div class="text-sm text-grey-600">{{ n.message }}</div>
            <div class="text-xs text-grey-400 mt-1">{{ n.time }}</div>
          </div>
        </article>
      </transition-group>
    </div>

    <div class="h-24"></div>
  </div>
</template>

<style scoped>
.fade-slide-enter-active, 
.fade-slide-leave-active {
  transition: all 0.28s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
</style>
