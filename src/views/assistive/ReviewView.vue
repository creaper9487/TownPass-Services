<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import { newIdempotencyKey, submitReservation } from '@/utils/assistive/api';
import { formatDate, hoursText, openDaysText } from '@/utils/assistive/centers';
import { services } from '@/utils/assistive/services';

const store = useAssistiveStore();
const flow = useAssistiveFlow();
const router = useRouter();

const info = computed(() => services[flow.service.value]);
const isBorrow = computed(() => flow.service.value === 'borrow');
const center = computed(() => store.center!);
const a = store.applicant;
const u = store.user;

const sending = ref(false);
const failed = ref(false);

const win = computed(() => store.windowFor(center.value));
const deadlineLabel = computed(() => `${formatDate(win.value.deadline)}前`);
const datesLabel = computed(() => win.value.openDates.map(formatDate).join('、'));
const pickupText = computed(() => `${deadlineLabel.value}，可前往 ${datesLabel.value}`);
const mask = (id: string) => (id.length === 10 ? `${id.slice(0, 3)}****${id.slice(7)}` : id);
const genderText = (g: string) => (g === 'M' ? '男' : g === 'F' ? '女' : '');

type Row = [string, string];
const sections = computed<{ title: string; step: string; rows: Row[] }[]>(() => {
  const list: { title: string; step: string; rows: Row[] }[] = [];
  const first = isBorrow.value ? 'cart' : 'need';
  list.push({
    title: isBorrow.value ? '本次預約項目' : '服務內容',
    step: first,
    rows: [
      ['服務', info.value.title],
      [isBorrow.value ? '輔具' : '項目', store.summary.join('\n')],
      [
        '辦理中心',
        `${center.value.name}\n${center.value.address}\n${openDaysText(center.value)} ${hoursText(center.value)}`
      ],
      ...(isBorrow.value ? ([['取貨期限', pickupText.value]] as Row[]) : [])
    ]
  });
  list.push({
    title: '聯絡人資料',
    step: 'contact',
    rows: [
      ['姓名', a.name],
      ...(a.phone ? ([['電話', a.phone]] as Row[]) : []),
      ['手機', a.mobile],
      ...(a.gender && !isBorrow.value ? ([['性別', genderText(a.gender)]] as Row[]) : []),
      ...(isBorrow.value && a.email ? ([['E-mail', a.email]] as Row[]) : [])
    ]
  });
  if (flow.service.value === 'assess') {
    list.push({
      title: '輔具使用者資料',
      step: 'user',
      rows: [
        ['姓名', u.name],
        ['身分證字號', mask(u.idNo)],
        ['戶籍地行政區', u.registeredDistrict],
        ...(u.livingDistrict ? ([['居住地行政區', `臺北市${u.livingDistrict}`]] as Row[]) : []),
        ...(a.email ? ([['E-mail', a.email]] as Row[]) : []),
        ...(u.remark ? ([['備註', u.remark]] as Row[]) : [])
      ]
    });
  }
  return list;
});

// 同一次送出（含失敗重試）共用同一把金鑰，後端才不會重複建立預約。
const idempotencyKey = newIdempotencyKey();

const submit = async () => {
  if (sending.value) return;
  sending.value = true;
  failed.value = false;
  try {
    const created = await submitReservation({
      service: flow.service.value,
      centerId: center.value.id,
      requests: store.requests,
      contact: a,
      subject: flow.service.value === 'assess' ? u : undefined,
      pickup: isBorrow.value ? win.value : undefined,
      idempotencyKey
    });
    store.finishSubmit(created[0]);
    await router.replace(stepRoute(flow.service.value, 'done'));
  } catch {
    failed.value = true;
  } finally {
    sending.value = false;
  }
};
</script>

<template>
  <AStepPage title="確認資料" :step="flow.current.value" :total="flow.total.value">
    <ASection v-for="s in sections" :key="s.title">
      <div class="flex items-center justify-between">
        <h2 class="tp-h3-semibold text-primary-700">{{ s.title }}</h2>
        <RouterLink
          :to="stepRoute(flow.service.value, s.step)"
          class="a11y-focus -mr-2 flex min-h-11 items-center px-2 text-base font-semibold text-primary-700 underline"
        >
          修改<span class="sr-only">{{ s.title }}</span>
        </RouterLink>
      </div>
      <dl class="mt-2 divide-y divide-grey-100">
        <div
          v-for="[k, v] in s.rows"
          :key="k"
          class="grid grid-cols-[7rem_1fr] gap-3 py-3 text-base first:pt-1"
        >
          <dt class="text-grey-700">{{ k }}</dt>
          <dd class="whitespace-pre-line break-words">{{ v }}</dd>
        </div>
      </dl>
    </ASection>

    <ASection v-if="failed">
      <AErrorText>送出失敗，請檢查網路後再試一次。</AErrorText>
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="flow.goPrev()">上一步</BaseButton>
        <BaseButton :aria-busy="sending" @click="submit">
          {{ sending ? '送出中…' : isBorrow ? '送出預約' : '送出申請' }}
        </BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
