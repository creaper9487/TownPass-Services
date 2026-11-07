import { ref } from 'vue';
import type { Router } from 'vue-router';

/**
 * 換頁動畫的方向：往前（進入下一頁）從右滑入，返回時從左滑入。
 * 依造訪過的路徑判斷：回到上一頁就是返回，其餘算往前。
 */
export const direction = ref<'forward' | 'back'>('forward');

let installed = false;
export const installMotion = (router: Router) => {
  if (installed) return;
  installed = true;
  // 安裝時畫面已經在第一頁了，要先把它放進紀錄，否則第一次返回會被當成往前
  const visited: string[] = [router.currentRoute.value.fullPath];
  // afterEach：被導向別頁或取消的換頁不會算進來；在畫面更新前就會執行，新頁面載入時方向已經設好
  router.afterEach((to) => {
    if (!to.path.startsWith('/assistive')) return;
    if (visited.length >= 2 && visited[visited.length - 2] === to.fullPath) {
      direction.value = 'back';
      visited.pop();
    } else {
      direction.value = 'forward';
      visited.push(to.fullPath);
    }
  });
};
