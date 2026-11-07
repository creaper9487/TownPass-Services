<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import { submitReservation } from '@/utils/assistive/api';
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
const p = store.pickup;

const sending = ref(false);
const failed = ref(false);

const win = computed(() => store.windowFor(center.value));
const deadlineLabel = computed(() => `${formatDate(win.value.deadline)}前`);
const datesLabel = computed(() => win.value.openDates.map(formatDate).join('、'));
const pickupText = computed(() => `${deadlineLabel.value}，可前往 ${datesLabel.value}`);
const pickupSentence = computed(
  () => `取貨期限 ${deadlineLabel.value}，可前往 ${datesLabel.value}。`
);
const mask = (id: string) => (id.length === 10 ? `${id.slice(0, 3)}****${id.slice(7)}` : id);
const genderText = (g: string) => (g === 'M' ? '男' : g === 'F' ? '女' : '');

type Row = [string, string];
const sections = computed<{ title: string; step: string; rows: Row[] }[]>(() => {
  const list: { title: string; step: string; rows: Row[] }[] = [];
  const first = isBorrow.value ? 'items' : 'need';
  list.push({
    title: '服務內容',
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
    title: '聯絡人',
    step: 'contact',
    rows: [
      ['姓名', a.name],
      ['手機', a.mobile],
      ...(a.phone ? ([['市話', a.phone]] as Row[]) : []),
      ...(a.gender && !isBorrow.value ? ([['性別', genderText(a.gender)]] as Row[]) : []),
      ...(a.email ? ([['E-mail', a.email]] as Row[]) : [])
    ]
  });
  if (flow.service.value === 'assess' || flow.service.value === 'repair') {
    list.push({
      title: '輔具使用者',
      step: 'user',
      rows: [
        ['使用者', a.isSelf ? `${u.name}（本人）` : u.name],
        ['身分證字號', mask(u.idNo)],
        ['戶籍地', u.registeredDistrict],
        ['居住地', `${u.livingCounty}${u.livingDistrict}`],
        ...(u.remark
          ? ([[flow.service.value === 'repair' ? '維修需求' : '備註', u.remark]] as Row[])
          : [])
      ]
    });
  }
  if (flow.service.value === 'recycle') {
    list.push({
      title: '收取地點',
      step: 'pickup',
      rows: [
        ['地址', `臺北市${p.district}${p.address}`],
        ['電梯', p.hasElevator === 'yes' ? '有' : '沒有'],
        ['回收證明', p.needCertificate ? '需要' : '不需要'],
        ...(p.remark ? ([['備註', p.remark]] as Row[]) : [])
      ]
    });
  }
  return list;
});

const submit = async () => {
  if (sending.value) return;
  sending.value = true;
  failed.value = false;
  try {
    const reservation = await submitReservation({
      service: flow.service.value,
      centerId: center.value.id,
      summary: store.summary,
      contactName: a.name,
      mobile: a.mobile,
      pickup: isBorrow.value ? win.value : undefined
    });
    store.finishSubmit(reservation);
    await router.replace(stepRoute(flow.service.value, 'done'));
  } catch {
    failed.value = true;
  } finally {
    sending.value = false;
  }
};
</script>

<template>
  <AStepPage
    title="確認資料"
    lead="確認無誤再送出。"
    :step="flow.current.value"
    :total="flow.total.value"
  >
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
          class="grid grid-cols-[5rem_1fr] gap-3 py-3 text-base first:pt-1"
        >
          <dt class="text-grey-700">{{ k }}</dt>
          <dd class="whitespace-pre-line break-words">{{ v }}</dd>
        </div>
      </dl>
    </ASection>

    <ASection>
      <p class="text-base">
        <template v-if="isBorrow">
          預約成功後，請攜帶身分證正本到中心取貨。{{ pickupSentence }}
        </template>
        <template v-else>
          送出後，中心會在開館時間回電確認，<strong>確認後才算申請完成</strong>。
        </template>
      </p>
      <AErrorText v-if="failed">送出失敗，請檢查網路後再試一次。</AErrorText>
    </ASection>

    <template #footer>
      <p class="mb-3 text-center text-sm text-grey-700">
        送出即表示同意提供上述資料給{{ center.name }}，用於辦理本次服務。
      </p>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="flow.goPrev()">上一步</BaseButton>
        <BaseButton :aria-busy="sending" @click="submit">
          {{ sending ? '送出中…' : isBorrow ? '送出預約' : '送出申請' }}
        </BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
