import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { flows } from '@/utils/assistive/services';
import type { ServiceId } from '@/utils/assistive/types';
import { useAssistiveStore } from '@/stores/assistive';
import { isEmail, isLandline, isMobile } from '@/utils/assistive/validators';

export const stepRoute = (service: ServiceId, step: string) => ({
  name: `assistive-${step}`,
  params: { service }
});

/**
 * 借用的聯絡人資料已經由台北通帳號帶好、格式也都對：不用再停一頁讓使用者按「下一步」，
 * 直接到確認資料（那裡可以按「修改」回來改）。評估、維修要填市話與性別，帳號沒有這些，照常停在這頁。
 */
export const borrowContactReady = (store: ReturnType<typeof useAssistiveStore>) => {
  const a = store.applicant;
  return (
    !!a.name.trim() &&
    isMobile(a.mobile) &&
    (!a.phone.trim() || isLandline(a.phone)) &&
    (!a.email.trim() || isEmail(a.email))
  );
};

/** 依目前路由所在的服務與步驟，提供「第 n 步／共 m 步」與前後頁導覽 */
export const useAssistiveFlow = () => {
  const route = useRoute();
  const router = useRouter();
  const store = useAssistiveStore();

  const service = computed(() => route.params.service as ServiceId);
  const step = computed(() => String(route.meta.step || ''));

  /** 這一步可以略過（使用者正停在這一步時不算） */
  const skippable = (s: string) =>
    s !== step.value && s === 'contact' && service.value === 'borrow' && borrowContactReady(store);

  // 略過的步驟不計入步數，也不會在「下一步／上一步」停下來
  const steps = computed(() => (flows[service.value] ?? []).filter((s) => !skippable(s)));
  const index = computed(() => steps.value.indexOf(step.value));

  const prevStep = computed(() => (index.value > 0 ? steps.value[index.value - 1] : null));
  const nextStep = computed(() => steps.value[index.value + 1] ?? null);

  const goNext = () => nextStep.value && router.push(stepRoute(service.value, nextStep.value));
  const goPrev = () =>
    prevStep.value
      ? router.push(stepRoute(service.value, prevStep.value))
      : router.push({ name: 'assistive-home' });

  return {
    service,
    step,
    /** 顯示用步數：完成頁不計入 */
    current: computed(() => index.value + 1),
    total: computed(() => Math.max(steps.value.length - 1, 1)),
    prevStep,
    nextStep,
    goNext,
    goPrev
  };
};
