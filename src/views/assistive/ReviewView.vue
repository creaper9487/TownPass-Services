<script setup lang="ts">
import { computed, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import ASection from '@/components/assistive/ASection.vue';
import AErrorText from '@/components/assistive/AErrorText.vue';
import AItemCard from '@/components/assistive/AItemCard.vue';
import { selectedInfo, type VariantInfo } from '@/utils/assistive/catalog';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveFlow, stepRoute } from '@/composables/useAssistiveFlow';
import { newIdempotencyKey, submitReservation, unsubscribeArrival } from '@/utils/assistive/api';
import { centerName, formatDate, hoursText, openDaysText } from '@/utils/assistive/centers';
import { serviceTitle } from '@/utils/assistive/services';
import { t, trSummary, tx, zhAttr } from '@/i18n/assistive';
import { ensurePush } from '@/utils/assistive/push';
import { ApiError } from '@/utils/assistive/remote';

const store = useAssistiveStore();
const flow = useAssistiveFlow();
const router = useRouter();

const isBorrow = computed(() => flow.service.value === 'borrow');
const center = computed(() => store.center!);
const a = store.applicant;
const u = store.user;

const sending = ref(false);
const failed = ref(false);
// 後端的錯誤碼對應不同的說明：沒庫存了、取貨期限內沒開館、欄位資料不符
const failureKey = ref('review.error');

const win = computed(() => store.windowFor(center.value));
const datesLabel = computed(() => win.value.openDates.map(formatDate).join(t('review.dateSep')));
// 期限內沒有開館日時只寫期限，不留下「可前往」後面接空白
const pickupText = computed(() =>
  win.value.openDates.length
    ? t('review.pickup', { deadline: formatDate(win.value.deadline), dates: datesLabel.value })
    : t('review.pickupNoDates', { deadline: formatDate(win.value.deadline) })
);
const mask = (id: string) => (id.length === 10 ? `${id.slice(0, 3)}****${id.slice(7)}` : id);
const genderText = (g: string) => (g === 'M' ? tx('男') : g === 'F' ? tx('女') : '');

// 值可以是一段文字，或逐行的文字（address 這類官方中文要標 lang）。
type Line = { text: string; zh?: boolean };
type Row = [string, string | Line[]];
type Section = { title: string; step: string; rows: Row[]; items?: VariantInfo[] };
const sections = computed<Section[]>(() => {
  const list: Section[] = [];
  const first = isBorrow.value ? 'cart' : 'need';
  list.push({
    title: isBorrow.value ? t('review.section.borrow') : t('review.section.service'),
    step: first,
    // 借用的輔具改用照片＋品名＋規格的卡片，不再把幾項資料串成一行
    items: isBorrow.value ? store.variants.map(selectedInfo) : undefined,
    rows: [
      [t('review.row.service'), serviceTitle(flow.service.value)],
      ...(isBorrow.value
        ? ([] as Row[])
        : ([[t('review.row.item'), store.summary.map(trSummary).join('\n')]] as Row[])),
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
    // 之後的進度（中心確認、取貨提醒、逾期）會推播：要在預約之前就登記好這支手機。
    await ensurePush();
    const created = await submitReservation({
      service: flow.service.value,
      centerId: center.value.id,
      requests: store.requests,
      contact: a,
      subject: flow.service.value === 'assess' ? u : undefined,
      pickup: isBorrow.value ? win.value : undefined,
      idempotencyKey
    });
    const booked = isBorrow.value ? store.variants.map((v) => v.id) : [];
    store.finishSubmit(created[0]);
    // 預約到的品項如果登記過到貨通知，那筆登記已經用完了：收掉，免得「已到貨，去預約」還留在清單和通知列。
    // 只是整理，失敗不影響預約。
    booked.forEach((id) => unsubscribeArrival(id).catch(() => undefined));
    // 送出成功的告知就是接著顯示的完成頁，不另外發通知。
    await router.replace(stepRoute(flow.service.value, 'done'));
  } catch (e) {
    failureKey.value =
      e instanceof ApiError
        ? e.code === 'OUT_OF_STOCK'
          ? 'review.errorStock'
          : e.code === 'PICKUP_WINDOW_CLOSED'
            ? 'review.errorWindow'
            : e.status === 422
              ? 'review.errorInvalid'
              : 'review.error'
        : 'review.error';
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
      <div v-if="s.items?.length" class="mt-3 border-b border-grey-100 pb-3">
        <p class="text-base text-grey-700">{{ t('review.row.device') }}</p>
        <ul class="mt-2 flex flex-col gap-3">
          <li v-for="item in s.items" :key="item.id"><AItemCard :item="item" /></li>
        </ul>
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
      <AErrorText>{{ t(failureKey) }}</AErrorText>
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
