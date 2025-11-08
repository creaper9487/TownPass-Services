<script setup>
import { ref, computed, onMounted } from 'vue'

/**
 * Upgrade hooks:
 * - Replace `loadMock()` with real API (REST/GraphQL) in `fetchLeaderboard`
 * - Support pagination via `cursor` in state and `loadMore()`
 * - Add live updates (WebSocket/SSE) to push changes
 * - Add filters (e.g., friends-only, this week, global) via `scope` & `period`
 * - Local cache hydration via IndexedDB if needed
 */

// --------- state ---------
const loading = ref(true)
const error = ref('')
const entries = ref([]) // { id, name, avatar, exp, delta? }

// Mock loader
function loadMock() {
  // Deterministic but "random-looking" avatars & exps
  const base = [
    { id: 1, name: 'Ava',   avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ava',   exp: 28950 },
    { id: 2, name: 'Liam',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Liam',  exp: 27510 },
    { id: 3, name: 'Mia',   avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mia',   exp: 26340 },
    { id: 4, name: 'Noah',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Noah',  exp: 24180 },
    { id: 5, name: 'Emma',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emma',  exp: 23990 },
    { id: 6, name: 'Mason', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mason', exp: 23340 },
    { id: 7, name: 'Luna',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Luna',  exp: 22870 },
    { id: 8, name: 'Evan',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Evan',  exp: 21920 },
    { id: 9, name: 'Zoe',   avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Zoe',   exp: 21340 },
    { id: 10,name: 'Aria',  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Aria',  exp: 20750 },
  ]
  return base.sort((a,b)=>b.exp-a.exp)
}

async function fetchLeaderboard() {
  loading.value = true
  error.value = ''
  try {
    // Replace with real API call
    // const res = await fetch('/api/leaderboard?period=all')
    // const data = await res.json()
    // entries.value = data.items
    await new Promise(r=>setTimeout(r, 320)) // tiny delay for animation
    entries.value = loadMock()
  } catch (e) {
    error.value = 'Failed to load leaderboard.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchLeaderboard)

// --------- derived ---------
const top3 = computed(() => entries.value.slice(0,3))
const rest = computed(() => entries.value.slice(3))

// Progress helper for visual EXP bar (relative to #1)
const maxExp = computed(() => entries.value.length ? entries.value[0].exp : 1)
function pct(exp) { return Math.max(4, Math.round((exp / maxExp.value) * 100)) } // min width for visibility
</script>

<template>
  <div class="lb-page">
    <header class="lb-topbar">
      <h1 class="lb-title">Leaderboard</h1>
      <div class="lb-actions">
        <!-- future: scope/period dropdowns -->
        <button class="icon-btn" title="Refresh" @click="fetchLeaderboard" :disabled="loading">
          <svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 15.3-6.3l1.7-1.7v6h-6l2.2-2.2A7 7 0 1 0 19 12h2a9 9 0 1 1-18 0z"/></svg>
        </button>
      </div>
    </header>

    <!-- Podium -->
    <section class="podium-wrap" aria-label="Top 3">
      <div class="podium">
        <!-- second -->
        <div class="slot second" v-if="top3[1]">
          <div class="avatar">
            <img :src="top3[1].avatar" :alt="top3[1].name" />
          </div>
          <div class="name">{{ top3[1].name }}</div>
          <div class="exp">{{ top3[1].exp.toLocaleString() }} EXP</div>
          <div class="stage silver">
            <span class="rank">2</span>
          </div>
        </div>

        <!-- first -->
        <div class="slot first" v-if="top3[0]">
          <div class="crown" aria-hidden="true">👑</div>
          <div class="avatar glow">
            <img :src="top3[0].avatar" :alt="top3[0].name" />
          </div>
          <div class="name">{{ top3[0].name }}</div>
          <div class="exp">{{ top3[0].exp.toLocaleString() }} EXP</div>
          <div class="stage gold">
            <span class="rank">1</span>
          </div>
          <!-- subtle confetti -->
          <div class="confetti" aria-hidden="true"></div>
        </div>

        <!-- third -->
        <div class="slot third" v-if="top3[2]">
          <div class="avatar">
            <img :src="top3[2].avatar" :alt="top3[2].name" />
          </div>
          <div class="name">{{ top3[2].name }}</div>
          <div class="exp">{{ top3[2].exp.toLocaleString() }} EXP</div>
          <div class="stage bronze">
            <span class="rank">3</span>
          </div>
        </div>
      </div>
    </section>

    <!-- List -->
    <section class="list-wrap" aria-label="Ranks 4+">
      <transition-group name="slide-up" tag="div" class="lb-list">
        <article
          v-for="(e, i) in rest"
          :key="e.id"
          class="row"
        >
          <div class="rank-badge">{{ i + 4 }}</div>
          <img class="row-avatar" :src="e.avatar" :alt="e.name" />
          <div class="row-main">
            <div class="row-name">{{ e.name }}</div>
            <div class="row-bar">
              <div class="bar" :style="{ width: pct(e.exp) + '%' }"></div>
            </div>
          </div>
          <div class="row-exp">{{ e.exp.toLocaleString() }}<span> EXP</span></div>
        </article>
      </transition-group>

      <div v-if="loading" class="skeletons">
        <div class="sk-row" v-for="i in 5" :key="i"></div>
      </div>
      <p v-if="error" class="err">{{ error }}</p>
    </section>

    <div class="safe-bottom"></div>
  </div>
</template>

<style scoped>
/* 手機優化版 */
.lb-page{
  --bg: linear-gradient(135deg,#f7faff 0%,#f2f6ff 60%,#eef6ff 100%);
  --card:#fff; --text:#0f1115; --muted:#667286; --border:#e6e8f0;
  --ring:#3b82f6; --ring-soft:rgba(59,130,246,.16);
  --shadow:0 10px 30px rgba(0,0,0,.06);
  --gold:#ffce54; --silver:#cfd8e3; --bronze:#d4a373; --chip:#eef3ff;

  background:var(--bg);
  /* ✅ 手機全螢幕高度（處理瀏覽器位址列） */
  min-height: 100svh;
  display:grid; grid-template-rows:auto auto 1fr;
  /* ✅ 限制內容最大寬 + 置中，並避免水平捲動 */
  max-width: 720px; margin-inline:auto; overflow-x:hidden;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
@supports (min-height: 100dvh){
  .lb-page{ min-height:100dvh; }
}

/* Topbar */
.lb-topbar{
  display:flex; align-items:center; justify-content:space-between;
  padding: 12px clamp(10px,3vw,16px) 4px;
}
.lb-title{ margin:0; font-weight:800; letter-spacing:.2px;
  font-size: clamp(16px, 4vw, 20px);
}
.lb-actions .icon-btn{
  appearance:none; border:1px solid var(--border); background:var(--card);
  width: clamp(32px, 9vw, 38px); height: clamp(32px, 9vw, 38px);
  border-radius:10px; display:grid; place-items:center;
  box-shadow:0 4px 16px rgba(0,0,0,.05);
}
.icon-btn svg{ width:18px;height:18px; fill:none; stroke:currentColor; stroke-width:1.6; }
.icon-btn:active{ transform:scale(.97); }

/* Podium */
.podium-wrap{ padding: 4px clamp(8px,3vw,16px) 6px; }
.podium{
  display:grid; grid-template-columns: repeat(3, minmax(0,1fr));
  align-items:end; gap: clamp(8px, 2.5vw, 12px);
}
.slot{
  background:var(--card); border:1px solid var(--border); border-radius:16px;
  padding: clamp(8px,2.5vw,12px) clamp(8px,2.5vw,10px) clamp(8px,2.5vw,10px);
  text-align:center; position:relative; box-shadow:var(--shadow);
  animation: pop-in .36s cubic-bezier(.2,.7,.2,1);
}
.slot .avatar{
  /* ✅ 以 clamp 做頭像縮放 */
  width: clamp(52px, 16vw, 64px);
  height: clamp(52px, 16vw, 64px);
  border-radius:50%; overflow:hidden; margin:0 auto 8px;
  border:2px solid #fff; box-shadow:0 4px 14px rgba(0,0,0,.08);
}
.slot .avatar img{ width:100%;height:100%;object-fit:cover; }
.slot .name{ font-weight:800; font-size: clamp(12px,3.6vw,14px); }
.slot .exp{ font-size: clamp(10px,3.2vw,12px); color:var(--muted); margin-top:2px; }

.stage{
  /* ✅ 舞台高度縮放，避免小螢幕過高 */
  height: clamp(44px, 14vw, 58px);
  border-radius:12px; margin-top:10px; display:grid; place-items:center;
  font-weight:900; font-size: clamp(14px,4.2vw,18px);
  letter-spacing:.5px; color:#26313d; box-shadow: inset 0 6px 16px rgba(0,0,0,.05);
}
.stage.gold{ background:linear-gradient(#ffe9a6,#ffd369); border:1px solid #f6c453; }
.stage.silver{ background:linear-gradient(#f1f5fb,#e5ecf7); border:1px solid #dbe3f2; }
.stage.bronze{ background:linear-gradient(#f2dfcc,#e6c3a1); border:1px solid #d6a574; }

.first{ transform: translateY(-4px); }
.first .stage{ height: clamp(56px, 18vw, 76px); }
.second{ transform: translateY(2px); }
.third{ transform: translateY(4px); }

.crown{
  position:absolute; left:50%; transform: translateX(-50%) rotate(-8deg);
  top:-14px; font-size: clamp(16px,5vw,20px);
  filter: drop-shadow(0 4px 6px rgba(0,0,0,.15));
  animation: crown-bounce 1.6s ease-in-out infinite;
}
.glow{ box-shadow: 0 0 0 3px rgba(255,206,84,.35), 0 8px 20px rgba(255,206,84,.25); }

/* Confetti */
.confetti{
  position:absolute; inset:-6px; pointer-events:none;
  --c: conic-gradient(from 0deg,#ff7aa2,#ffd369,#9dd6ff,#b3f1c8,#c7a0ff,#ff7aa2);
  mask: radial-gradient(circle at 50% -20%, transparent 38%, #000 40%);
  background:var(--c); opacity:.12; filter:blur(6px); border-radius:18px;
  animation: confetti-spin 6s linear infinite;
}

/* List */
.list-wrap{ padding: 6px clamp(6px,3vw,12px) 16px; }
.lb-list{ display:flex; flex-direction:column; gap: clamp(8px,2.2vw,10px); }
.row{
  display:grid;
  /* ✅ 以更小的徽章/頭像欄寬，避免擠壓；第三欄用 minmax(0,1fr) 防止溢出 */
  grid-template-columns: clamp(32px,9vw,44px) clamp(32px,9vw,44px) minmax(0,1fr) auto;
  align-items:center; gap: clamp(8px,2.2vw,10px);
  background:var(--card); border:1px solid var(--border); border-radius:14px;
  padding: clamp(8px,2.4vw,10px) clamp(10px,3vw,12px);
  box-shadow:var(--shadow);
}
.rank-badge{
  width: clamp(28px,8.5vw,36px); height: clamp(28px,8.5vw,36px);
  border-radius:10px; display:grid; place-items:center; font-weight:900;
  background:var(--chip); color:#2a3a55; border:1px solid #dfe7fb;
  font-size: clamp(11px,3.4vw,13px);
}
.row-avatar{
  width: clamp(30px,9vw,40px); height: clamp(30px,9vw,40px);
  border-radius:50%; object-fit:cover; border:2px solid #fff;
  box-shadow:0 4px 12px rgba(0,0,0,.06);
}
.row-main{ display:grid; gap:6px; min-width:0; }
.row-name{
  font-weight:800; font-size: clamp(12px,3.6vw,14px);
  /* ✅ 文字溢出處理 */
  overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
}
.row-bar{
  height:8px; background:#eef2f7; border-radius:999px; overflow:hidden;
  border:1px solid #e6eaf2;
}
.bar{
  height:100%; border-radius:999px;
  background: linear-gradient(90deg,#60a5fa,#34d399,#fbbf24);
  animation: grow .5s ease-out both;
}
.row-exp{
  font-weight:800; color:#1f2937; font-size: clamp(11px,3.4vw,13px);
  margin-left: 6px;
}
.row-exp span{ color:#6b7280; font-weight:700; margin-left:4px; }

/* Skeletons */
.skeletons{ padding: 8px 4px; }
.sk-row{
  height: clamp(46px,12vw,56px); border-radius:14px; margin:10px 8px;
  background: linear-gradient(90deg,#eef2f7 25%,#f6f8fb 37%,#eef2f7 63%);
  background-size:400% 100%; animation: shimmer 1.4s infinite;
  border:1px solid var(--border);
}

/* Animations */
@keyframes pop-in{ from{ transform: translateY(10px) scale(.98); opacity:.0 } to{ transform:none; opacity:1 } }
@keyframes crown-bounce{ 0%,100%{ transform: translateX(-50%) translateY(0) rotate(-8deg) } 50%{ transform: translateX(-50%) translateY(-3px) rotate(-8deg) } }
@keyframes confetti-spin{ to{ transform: rotate(360deg) } }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
@keyframes grow { from{ width:0 } }

/* Transition-group (list) */
.slide-up-enter-active{ transition: all .28s cubic-bezier(.2,.7,.2,1); }
.slide-up-enter-from{ opacity:0; transform: translateY(8px); }

/* Misc */
.err{ color:#b42318; font-weight:700; text-align:center; margin-top:8px; }
/* ✅ safe-area 底部間距（iPhone 瀏海與手勢區） */
.safe-bottom{ height: calc(env(safe-area-inset-bottom,0px) + 12px); }

/* --- 兩段極小螢幕保險 --- */
@media (max-width: 390px){
  .first{ transform: translateY(-2px); }
  .second{ transform: translateY(1px); }
  .third{ transform: translateY(2px); }
  .row{ grid-template-columns: 30px 30px minmax(0,1fr) auto; }
}
@media (max-width: 340px){
  .lb-topbar{ padding-inline: 8px; }
  .lb-actions .icon-btn{ width:30px; height:30px; }
  .row{ grid-template-columns: 28px 28px minmax(0,1fr) auto; gap:6px; }
}

</style>
