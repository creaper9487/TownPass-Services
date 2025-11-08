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
  <div class="ntf-page">

    <header class="top">
      <h1>通知中心</h1>
      <button class="mark-all" @click="notifications.forEach(n => n.unread=false)">
        全部標為已讀
      </button>
    </header>

    <div class="list">
      <div v-if="loading" class="sk-wrap">
        <div class="sk" v-for="i in 5" :key="i"></div>
      </div>

      <transition-group name="fade-slide" tag="div">
        <article
          v-for="n in notifications"
          :key="n.id"
          class="item"
          :class="{ unread: n.unread }"
          @click="markRead(n)"
        >
          <div class="indicator"></div>

          <div class="content">
            <div class="title">{{ n.title }}</div>
            <div class="msg">{{ n.message }}</div>
            <div class="time">{{ n.time }}</div>
          </div>
        </article>
      </transition-group>
    </div>

    <div class="safe-bottom"></div>

  </div>
</template>

<style scoped>
.ntf-page {
  --bg: #f7f8fc;
  --card: #ffffff;
  --border: #e6e8f0;
  --text: #0f1115;
  --muted: #64748b;
  background: var(--bg);
  min-height: 100%;
  display: grid;
  grid-template-rows: auto 1fr;
}

/* Top bar */
.top {
  display:flex; justify-content:space-between; align-items:center;
  padding: 14px 16px;
}
.top h1 { margin:0; font-size:18px; font-weight:800; }
.mark-all {
  appearance:none; border:0; background:transparent;
  color:#0ea5e9; font-weight:700; font-size:14px;
}

/* List */
.list { padding: 8px 12px 16px; display:flex; flex-direction:column; gap:14px; }

.item {
  background: var(--card);
  border:1px solid var(--border);
  border-radius:16px;
  padding: 14px 16px 14px 12px;
  display:flex; gap:12px;
  box-shadow: 0 6px 20px rgba(0,0,0,.05);
  cursor:pointer;
  transition: transform .1s ease, box-shadow .2s ease;
}
.item:active { transform: scale(.98); }

.indicator {
  width:8px; border-radius:6px; background:transparent;
  transition: background .3s ease;
}
.item.unread .indicator { background:#0ea5e9; }

.content {
  display:flex; flex-direction:column; gap:4px;
}
.title { font-weight:800; }
.msg { font-size:14px; color:var(--muted); }
.time { font-size:12px; color:#9ca3af; margin-top:2px; }

/* Skeletons */
.sk-wrap { display:flex; flex-direction:column; gap:12px; }
.sk {
  height:64px; border-radius:16px; border:1px solid var(--border);
  background:linear-gradient(90deg,#eef2f7 25%,#f7f8fb 50%,#eef2f7 75%);
  background-size:400% 100%; animation: shimmer 1.3s infinite;
}
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* Animations */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all .28s cubic-bezier(.2,.7,.2,1);
}
.fade-slide-enter-from {
  opacity:0; transform: translateY(6px);
}

/* Safe Bottom */
.safe-bottom { height: calc(env(safe-area-inset-bottom, 0px) + 12px); }
</style>
