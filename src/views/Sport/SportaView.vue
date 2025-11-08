<script setup lang="ts">
import { ref } from 'vue'
import HomeView from '@/views/Sport/HomeSportView.vue'
import SearchView from './SearchView.vue'
import { computed } from 'vue';
import { useSportaStore, type userInfo } from '@/stores/sporta';
import { useConnectionMessage } from '@/composables/useConnectionMessage';
import { useHandleConnectionData } from '@/composables/useHandleConnectionData';
const sportaStore = useSportaStore();

useConnectionMessage('userinfo', null);

useHandleConnectionData((event: { data: string }) => {
    const result = JSON.parse(event.data);
    sportaStore.user.id = result.data.id
});

sportaStore.fetchAllData(sportaStore.user.id);
const tabs = [
  { key: 'home',     label: 'Home',     icon: 'home' },
  { key: 'search',   label: 'Search',   icon: 'search' },
  { key: 'add',      label: 'Add',      icon: 'plus' },
  { key: 'notify',   label: 'Alerts',   icon: 'bell' },
  { key: 'star',     label: 'Saved',    icon: 'star' },
]
const current = ref('home')
function setTab(k) { current.value = k }
</script>

<template>
  <div class="bg-stage"></div>

  <div class="phone-shell">
    <main class="screen">
      <div class="avatar-dot"></div>

      <!-- 分頁內容 -->
      <HomeView v-if="current==='home'" />
      <SearchView v-else-if="current==='search'" />
      <!-- 其他分頁留白，未來補： -->
      <section v-else class="content-card"><p>Coming soon…</p></section>
    </main>

    <!-- 底部導覽（與上一版相同） -->
    <nav class="glass-nav">
      <div class="nav-inner">
        <button
          v-for="t in tabs"
          :key="t.key"
          class="nav-btn"
          :class="{ active: current === t.key, 'is-plus': t.key==='add' }"
          @click="setTab(t.key)"
          :aria-label="t.label"
        >
          <svg v-if="t.icon==='home'" viewBox="0 0 24 24" class="icon"><path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/></svg>
          <svg v-else-if="t.icon==='search'" viewBox="0 0 24 24" class="icon"><path d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15z"/></svg>
          <svg v-else-if="t.icon==='plus'" viewBox="0 0 24 24" class="icon"><path d="M12 5v14M5 12h14"/></svg>
          <svg v-else-if="t.icon==='bell'" viewBox="0 0 24 24" class="icon"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 6 3 8H3c0-2 3-1 3-8m6 13a3 3 0 0 1-3-3h6a3 3 0 0 1-3 3z"/></svg>
          <svg v-else viewBox="0 0 24 24" class="icon"><path d="m12 17.3-5.6 3 1.1-6.3L3 9.7l6.3-.9L12 3l2.7 5.8 6.3.9-4.5 4.3 1.1 6.3z"/></svg>
        </button>
      </div>
    </nav>
  </div>
</template>


<style scoped>
:root {
  --bg-1: #0f1115;
  --bg-2: #171a21;
  --glass: rgba(255,255,255,.14);
  --glass-strong: rgba(255,255,255,.18);
  --glass-border: rgba(255,255,255,.28);
  --text: #e7e9ee;
  --muted: #b8bfcc;
  --accent: #ffd43b;
  --danger: #d77a7a;
  --blur: 18px;
}

/* 暗色已為預設；若要支援淺色，依需求覆寫 */
@media (prefers-color-scheme: light) {
  :root {
    --bg-1: #e7ebf3;
    --bg-2: #d9dfec;
    --glass: rgba(255,255,255,.45);
    --glass-strong: rgba(255,255,255,.5);
    --glass-border: rgba(0,0,0,.08);
    --text: #0f1115;
    --muted: #606771;
  }
}

* { box-sizing: border-box; }
html, body, #app { height: 100%; }
body {
  margin: 0;
  background: radial-gradient(1200px 1200px at 20% -10%, var(--bg-2), transparent),
              radial-gradient(1200px 1200px at 80% 110%, var(--bg-2), transparent),
              var(--bg-1);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  font: 16px/1.4 system-ui, -apple-system, Segoe UI, Roboto, Noto Sans TC, "Helvetica Neue", Arial, "Apple Color Emoji", "Segoe UI Emoji";
}

/* 背景舞台加上淡噪點 */
.bg-stage::before,
.bg-stage::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
}
.bg-stage::before {
  background: radial-gradient(600px 600px at 80% 10%, rgba(255,255,255,.06), transparent),
              radial-gradient(800px 800px at 10% 90%, rgba(255,255,255,.04), transparent);
}
.bg-stage::after {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 80 80'%3E%3Ccircle cx='1' cy='1' r='1' fill='white' fill-opacity='.05'/%3E%3C/svg%3E");
  opacity: .7;
  mix-blend-mode: overlay;
}

/* 置中展示（可刪，此層只是讓桌機看起來像手機） */
.phone-shell {
  position: relative;
  margin: 0 auto;
  max-width: 440px;
  min-height: 100dvh;
}

/* 內容畫面 */
.screen {
  position: relative;
  min-height: 100dvh;
  padding: calc(env(safe-area-inset-top, 0px) + 16px) 16px
           calc(env(safe-area-inset-bottom, 0px) + 96px);
  display: block;
}

/* 左上圓點 */
.avatar-dot {
  width: 40px; height: 40px; border-radius: 9999px;
  background: color-mix(in oklab, var(--danger) 88%, white 0%);
  box-shadow: 0 10px 24px rgba(215,122,122,.35);
  border: 1px solid rgba(255,255,255,.3);
  margin: 4px 0 16px 4px;
}

/* 玻璃卡片 */
.content-card {
  margin: 12px 4px;
  padding: 16px 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, var(--glass-strong), var(--glass));
  border: 1px solid var(--glass-border);
  box-shadow:
    0 10px 30px rgba(0,0,0,.35),
    inset 0 1px 0 rgba(255,255,255,.25);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
}
.content-card h1, .content-card h2 { margin: 2px 0 8px; }
.content-card p { color: var(--muted); margin: 0; }

/* 底部玻璃導覽 */
.glass-nav {
  position: fixed;
  left: 0; right: 0;
  bottom: 0;
  display: flex; justify-content: center;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
.nav-inner {
  width: min(480px, 100%);
  margin: 0 12px 10px;
  padding: 10px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,.18), rgba(255,255,255,.1));
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
  box-shadow:
    0 20px 40px rgba(0,0,0,.45),
    inset 0 1px 0 rgba(255,255,255,.25);
}

.nav-btn {
  -webkit-tap-highlight-color: transparent;
  appearance: none;
  border: 0;
  background: rgba(255,255,255,.16);
  width: 54px; height: 54px;
  margin: 0 6px;
  border-radius: 14px;
  display: inline-flex; align-items: center; justify-content: center;
  transition: transform .15s ease, background .2s ease, box-shadow .2s ease;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.25);
}
.nav-btn .icon {
  width: 22px; height: 22px;
  fill: none; stroke: currentColor; stroke-width: 1.6;
  color: #0e0f12; /* 深色 icon 基底 */
  filter: drop-shadow(0 1px 0 rgba(255,255,255,.4));
}
.nav-btn.active { background: rgba(255,255,255,.72); }
.nav-btn.active .icon { color: #111315; }
.nav-btn:active { transform: scale(.96); }

.nav-btn.is-plus { background: rgba(255,105,97,.18); border: 1px solid rgba(255,105,97,.35); }
.nav-btn.is-plus.active { background: rgba(255,105,97,.7); }
.nav-btn.is-plus .icon { color: #ff6b6b; }

/* 星星高亮（展示用：當前為 star 時） */
.nav-btn:nth-last-child(1).active .icon { color: var(--accent); }

/* 避免捲動彈性導致導覽列跳動 */
@supports (overflow: overlay) {
  .screen { overscroll-behavior-y: none; }
}

</style>