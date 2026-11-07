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
import { centerName, formatDate, hoursText, openDaysText } from '@/utils/assistive/centers';
import { serviceTitle } from '@/utils/assistive/services';
import { t, trSummary, tx, zhAttr } from '@/i18n/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { ensurePush } from '@/utils/assistive/push';

const store = useAssistiveStore();
const flow = useAssistiveFlow();
const router = useRouter();
const native = useAssistiveNative();

const isBorrow = computed(() => flow.service.value === 'borrow');
const center = computed(() => store.center!);
const a = store.applicant;
const u = store.user;

const sending = ref(false);
const failed = ref(false);

const win = computed(() => store.windowFor(center.value));
const datesLabel = computed(() => win.value.openDates.map(formatDate).join(t('review.dateSep')));
const pickupText = computed(() =>
  t('review.pickup', { deadline: formatDate(win.value.deadline), dates: datesLabel.value })
);
const mask = (id: string) => (id.length === 10 ? `${id.slice(0, 3)}****${id.slice(7)}` : id);
const genderText = (g: string) => (g === 'M' ? tx('男') : g === 'F' ? tx('女') : '');

// 值可以是一段文字，或逐行的文字（address 這類官方中文要標 lang）。
type Line = { text: string; zh?: boolean };
type Row = [string, string | Line[]];
const sections = computed<{ title: string; step: string; rows: Row[] }[]>(() => {
  const list: { title: string; step: string; rows: Row[] }[] = [];
  const first = isBorrow.value ? 'cart' : 'need';
  list.push({
    title: isBorrow.value ? t('review.section.borrow') : t('review.section.service'),
    step: first,
    rows: [
      [t('review.row.service'), serviceTitle(flow.service.value)],
      [
        isBorrow.value ? t('review.row.device') : t('review.row.item'),
        store.summary.map(trSummary).join('\n')
      ],
      [
        t('review.row.center'),
        [
          { text: centerName(center.value) },
          { text: center.value.address, zh: true },
          { text: `${openDaysText(center.value)} ${hoursText(center.value)}` }
        ]
      ],
      ...(isBorrow.value ? ([[t('review.row.pickup'), pickupText.value]] as Row[]) : [])
    ]
  });
  list.push({
    title: t('review.section.contact'),
    step: 'contact',
    rows: [
      [t('review.row.name'), a.name],
      ...(a.phone ? ([[t('review.row.phone'), a.phone]] as Row[]) : []),
      [t('review.row.mobile'), a.mobile],
      ...(a.gender && !isBorrow.value
        ? ([[t('review.row.gender'), genderText(a.gender)]] as Row[])
        : []),
      ...(isBorrow.value && a.email ? ([[t('review.row.email'), a.email]] as Row[]) : [])
    ]
  });
  if (flow.service.value === 'assess') {
    list.push({
      title: t('review.section.user'),
      step: 'user',
      rows: [
        [t('review.row.name'), u.name],
        [t('review.row.idNo'), mask(u.idNo)],
        [t('review.row.registered'), tx(u.registeredDistrict)],
        ...(u.livingDistrict
          ? ([
              [t('review.row.living'), t('review.living', { district: tx(u.livingDistrict) })]
            ] as Row[])
          : []),
        ...(a.email ? ([[t('review.row.email'), a.email]] as Row[]) : []),
        ...(u.remark ? ([[t('review.row.remark'), u.remark]] as Row[]) : [])
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
    // 借用成功時後端會推播「預約成功」：要在預約之前就登記好這支手機，不然收不到這一則。
    const pushed = await ensurePush();
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
    // 借用已登記推播時由後端推播；評估、維修要等中心確認才有後續通知，送出當下仍由本機通知告知。
    const isBorrowService = flow.service.value === 'borrow';
    if (!(isBorrowService && pushed)) {
      native.notify(
        isBorrowService ? '輔具借用預約成功' : '輔具申請已送出',
        `預約編號 ${created[0].id}，請至預約紀錄查看詳情。`
      );
    }
    await router.replace(stepRoute(flow.service.value, 'done'));
  } catch {
    failed.value = true;
  } finally {
    sending.value = false;
  }
};
</script>

<template>
  <AStepPage :title="t('review.title')" :step="flow.current.value" :total="flow.total.value">
    <ASection v-for="s in sections" :key="s.title">
      <div class="flex items-center justify-between">
        <h2 class="tp-h3-semibold text-primary-700">{{ s.title }}</h2>
        <RouterLink
          :to="stepRoute(flow.service.value, s.step)"
          class="a11y-focus -mr-2 flex min-h-11 items-center px-2 text-base font-semibold text-primary-700 underline"
        >
          <span aria-hidden="true">{{ t('review.edit') }}</span>
          <span class="sr-only">{{ t('review.editSection', { title: s.title }) }}</span>
        </RouterLink>
      </div>
      <dl class="mt-2 divide-y divide-grey-100">
        <div
          v-for="[k, v] in s.rows"
          :key="k"
          class="grid grid-cols-[7rem_1fr] gap-3 py-3 text-base first:pt-1"
        >
          <dt class="text-grey-700">{{ k }}</dt>
          <dd class="whitespace-pre-line break-words">
            <template v-if="typeof v === 'string'">{{ v }}</template>
            <template v-else>
              <span
                v-for="(line, i) in v"
                :key="i"
                class="block"
                :lang="line.zh ? zhAttr : undefined"
              >
                {{ line.text }}
              </span>
            </template>
          </dd>
        </div>
      </dl>
    </ASection>

    <ASection v-if="failed">
      <AErrorText>{{ t('review.error') }}</AErrorText>
    </ASection>

    <template #footer>
      <div class="grid grid-cols-2 gap-2">
        <BaseButton outline @click="flow.goPrev()">{{ t('common.prev') }}</BaseButton>
        <BaseButton :aria-busy="sending" @click="submit">
          {{
            sending
              ? t('review.sending')
              : isBorrow
                ? t('review.submitBorrow')
                : t('review.submitAssess')
          }}
        </BaseButton>
      </div>
    </template>
  </AStepPage>
</template>
