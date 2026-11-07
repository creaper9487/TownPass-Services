import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { flows } from '@/utils/assistive/services';
import type { ServiceId } from '@/utils/assistive/types';

export const stepRoute = (service: ServiceId, step: string) => ({
  name: `assistive-${step}`,
  params: { service }
});

/** 依目前路由所在的服務與步驟，提供「第 n 步／共 m 步」與前後頁導覽 */
export const useAssistiveFlow = () => {
  const route = useRoute();
  const router = useRouter();

  const service = computed(() => route.params.service as ServiceId);
  const step = computed(() => String(route.meta.step || ''));
  const steps = computed(() => flows[service.value] ?? []);
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
