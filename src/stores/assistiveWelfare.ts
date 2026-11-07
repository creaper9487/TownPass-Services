import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import { FIRST_QUESTION, RESULT, nextQuestion } from '@/utils/assistive/welfare';

/** 福利查詢作答進度：只存在這次開啟的頁面，不寫入裝置，也不送出。 */
export const useAssistiveWelfareStore = defineStore('assistiveWelfare', () => {
  const answers = ref<Record<string, string>>({});
  /** 依序走過的題目編號，用來回上一題 */
  const trail = ref<string[]>([]);
  const finished = ref(false);

  const age = computed(() => Number(answers.value[FIRST_QUESTION] ?? 0));

  const reset = () => {
    answers.value = {};
    trail.value = [FIRST_QUESTION];
    finished.value = false;
  };

  /** 記下這題的答案，回傳要去的下一題（或 'result'）。改答前面的題目時，後面的答案會清掉。 */
  const answer = (qid: string, value: string) => {
    const at = trail.value.indexOf(qid);
    if (at >= 0) {
      for (const later of trail.value.slice(at + 1)) delete answers.value[later];
      trail.value = trail.value.slice(0, at + 1);
    }
    answers.value[qid] = value;
    const next = nextQuestion(qid, answers.value, Number(answers.value[FIRST_QUESTION] ?? 0));
    finished.value = next === RESULT;
    if (next !== RESULT) trail.value.push(next);
    return next;
  };

  const previous = (qid: string) => {
    const at = trail.value.indexOf(qid);
    return at > 0 ? trail.value[at - 1] : null;
  };

  return { answers, trail, finished, age, reset, answer, previous };
});
