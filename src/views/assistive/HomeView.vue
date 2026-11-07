<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import AStepPage from '@/components/assistive/AStepPage.vue';
import AServiceCard from '@/components/assistive/AServiceCard.vue';
import ClosureNotice from '@/components/assistive/ClosureNotice.vue';
import ALanguageSwitch from '@/components/assistive/ALanguageSwitch.vue';
import welfareIcon from '@/assets/images/assistive/icon-welfare.svg';
import assessIcon from '@/assets/images/assistive/icon-assess.svg';
import { useAssistiveStore } from '@/stores/assistive';
import { serviceShortTitle } from '@/utils/assistive/services';
import { t, tx, zhAttr } from '@/i18n/assistive';
import { catalog, variantInfo } from '@/utils/assistive/catalog';
import { centerById, centerShort, formatDate } from '@/utils/assistive/centers';
import {
  effectiveStatus,
  fetchStock,
  listArrivals,
  listReservations,
  loadArrivals,
  statusText,
  type ArrivalNotice
} from '@/utils/assistive/api';
import { useAssistiveStockPolling } from '@/composables/useAssistiveStockPolling';
import { articles, excerptOf } from '@/utils/assistive/education';
import type { Category, Reservation, Stock } from '@/utils/assistive/types';

const store = useAssistiveStore();
const stock = ref<Record<string, Stock>>({});
const stockLoaded = ref(false);
const stockFailed = ref(false);
const reservations = ref<Reservation[]>([]);
const arrivals = ref<ArrivalNotice[]>(listArrivals());
const activityLoaded = ref(false);

const featuredNames = ['輪椅', '助行器', '拐杖', '洗澡椅'];
const featured = computed(() => {
  const chosen = featuredNames
    .map((name) => catalog.value.find((category) => category.name === name))
    .filter((category): category is Category => !!category);
  return chosen.length ? chosen : catalog.value.slice(0, 4);
});
const stockOf = (category: Category) =>
  category.variants.reduce((sum, variant) => sum + (stock.value[variant.id]?.stock ?? 0), 0);

const arrived = computed(() =>
  [...arrivals.value]
    .filter((notice) => notice.status === 'arrived')
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0]
);
const waitingCount = computed(() => arrivals.value.filter((notice) => notice.status !== 'arrived').length);
const activeReservations = computed(() =>
  reservations.value
    .filter((reservation) => ['booked', 'submitted', 'confirmed'].includes(effectiveStatus(reservation)))
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
);
const currentReservation = computed(() => activeReservations.value[0]);
const activityCount = computed(() => activeReservations.value.length + arrivals.value.length);
const reservationItem = (reservation: Reservation) =>
  (reservation.itemIds?.[0] && variantInfo(reservation.itemIds[0])?.name) ||
  reservation.summary[0] ||
  serviceShortTitle(reservation.service);
const reservationCenter = (reservation: Reservation) => {
  const center = centerById(reservation.centerId);
  return center ? centerShort(center) : '';
};
const latestArticle = computed(() => [...articles].sort((a, b) => b.iso.localeCompare(a.iso))[0]);

onMounted(() => {
  void store.loadCalendars();
  void fetchStock()
    .then((items) => {
      stock.value = items;
      stockLoaded.value = true;
    })
    .catch(() => { stockFailed.value = true; });
  void Promise.allSettled([listReservations(), loadArrivals()]).then(([booking, notices]) => {
    if (booking.status === 'fulfilled') reservations.value = booking.value;
    if (notices.status === 'fulfilled') arrivals.value = notices.value;
    activityLoaded.value = true;
  });
});
useAssistiveStockPolling((items) => {
  stock.value = items;
  stockLoaded.value = true;
  stockFailed.value = false;
});
</script>

<template>
  <AStepPage :title="t('app.title')" hide-header>
    <div class="flex flex-col gap-4 bg-grey-50 px-4 py-4 pb-8">
      <ClosureNotice v-if="store.closureNotices.length" :items="store.closureNotices" compact />

      <section aria-labelledby="home-borrow-title" class="rounded-xl bg-gradient-to-tl from-primary-700 to-primary-800 p-4 text-white">
        <div class="flex items-start justify-between gap-3">
          <h2 id="home-borrow-title" class="tp-h3-semibold">{{ serviceShortTitle('borrow') }}</h2>
          <RouterLink
            :to="{ name: 'assistive-items', params: { service: 'borrow' } }"
            class="a11y-focus shrink-0 rounded-lg border border-white/60 px-3 py-2 text-sm font-semibold"
            @click="store.begin('borrow')"
          >
            {{ t('home.allDevices') }}
          </RouterLink>
        </div>
        <p class="mt-1 text-sm text-white/90">{{ t('home.borrowLead') }}</p>
        <div class="mt-4 grid grid-cols-2 gap-2">
          <RouterLink
            v-for="category in featured"
            :key="category.id"
            :to="{ name: 'assistive-variants', params: { service: 'borrow', categoryId: category.id } }"
            class="a11y-focus flex min-h-20 flex-col justify-between rounded-lg bg-white p-3 text-grey-800"
            @click="store.begin('borrow')"
          >
            <span class="font-semibold">{{ tx(category.name) }}</span>
            <span class="mt-2 flex items-center justify-between gap-1 text-sm text-primary-700">
              <span v-if="stockLoaded">{{ t('borrow.stockLeft', { n: stockOf(category) }) }}</span>
              <span v-else-if="stockFailed">{{ t('home.viewModels') }}</span>
              <span v-else>{{ t('common.loading') }}</span>
              <span aria-hidden="true">›</span>
            </span>
          </RouterLink>
        </div>
        <RouterLink
          v-if="store.service === 'borrow' && store.variants.length"
          :to="{ name: 'assistive-center', params: { service: 'borrow' } }"
          class="a11y-focus mt-3 flex min-h-12 items-center justify-between rounded-lg border border-white/70 px-3 text-sm font-semibold"
        >
          <span>{{ t('home.continueBorrow', { n: store.variants.length }) }}</span>
          <span aria-hidden="true">→</span>
        </RouterLink>
      </section>

      <section aria-labelledby="home-activity-title" class="tp-card rounded-xl p-4">
        <div class="flex items-center justify-between gap-3">
          <h2 id="home-activity-title" class="tp-h3-semibold">{{ t('home.activity') }}</h2>
          <RouterLink :to="{ name: 'assistive-reservations' }" class="a11y-focus shrink-0 text-sm font-semibold text-primary-700 underline">
            {{ t('home.viewAll') }}<span v-if="activityCount"> ({{ activityCount }})</span>
          </RouterLink>
        </div>

        <RouterLink
          v-if="arrived"
          :to="{ name: 'assistive-borrow-quick', params: { service: 'borrow', variantId: arrived.variantId } }"
          class="a11y-focus mt-3 flex min-h-16 items-center justify-between gap-3 rounded-lg bg-secondary-50 p-3"
        >
          <span class="min-w-0">
            <span class="block font-semibold">{{ t('home.arrived', { name: variantInfo(arrived.variantId)?.name ?? arrived.label }) }}</span>
            <span class="mt-1 block text-sm text-grey-700">{{ t('home.arrivedAction') }}</span>
          </span>
          <span aria-hidden="true" class="text-primary-700">→</span>
        </RouterLink>

        <RouterLink
          v-if="currentReservation"
          :to="{ name: 'assistive-reservation', params: { id: currentReservation.id } }"
          class="a11y-focus mt-3 flex min-h-16 items-center justify-between gap-3 rounded-lg bg-grey-50 p-3"
        >
          <span class="min-w-0">
            <span class="block font-semibold">{{ reservationItem(currentReservation) }}</span>
            <span class="mt-1 block text-sm text-grey-700">
              {{ statusText(currentReservation) }}
              <template v-if="reservationCenter(currentReservation)"> · {{ reservationCenter(currentReservation) }}</template>
            </span>
            <span v-if="currentReservation.pickupDeadline" class="mt-1 block text-sm text-grey-700">
              {{ t('home.pickupDeadline', { date: formatDate(new Date(currentReservation.pickupDeadline)) }) }}
            </span>
          </span>
          <span aria-hidden="true" class="text-primary-700">→</span>
        </RouterLink>
        <p v-if="waitingCount" class="mt-3 text-sm text-grey-700">
          {{ t('home.waitingArrivals', { n: waitingCount }) }}
        </p>
        <p v-if="activityLoaded && !arrived && !currentReservation && !waitingCount" class="mt-3 text-sm text-grey-700">
          {{ t('home.noActivity') }}
        </p>
      </section>

      <nav :aria-label="t('home.menu')" class="flex flex-col gap-2">
        <AServiceCard
          :title="t('home.welfare')"
          :description="t('home.welfareLead')"
          :icon="welfareIcon"
          :to="{ name: 'assistive-welfare' }"
        />
        <AServiceCard
          :title="serviceShortTitle('assess')"
          :description="t('home.assessLead')"
          :icon="assessIcon"
          :to="{ name: 'assistive-need', params: { service: 'assess' } }"
          @click="store.begin('assess')"
        />
      </nav>

      <section v-if="latestArticle" aria-labelledby="home-education-title" class="tp-card rounded-xl p-4">
        <div class="flex items-center justify-between gap-3">
          <h2 id="home-education-title" class="tp-h3-semibold">{{ t('home.education') }}</h2>
          <RouterLink :to="{ name: 'assistive-education' }" class="a11y-focus shrink-0 text-sm font-semibold text-primary-700 underline">
            {{ t('home.viewAll') }}
          </RouterLink>
        </div>
        <RouterLink
          :to="{ name: 'assistive-education-article', params: { id: latestArticle.id } }"
          class="a11y-focus mt-3 block rounded-lg bg-grey-50 p-3"
        >
          <span class="block font-semibold text-primary-700" :lang="zhAttr">{{ latestArticle.name }}</span>
          <span class="mt-1 block text-sm text-grey-700" :lang="zhAttr">{{ latestArticle.date }}</span>
          <span class="mt-2 line-clamp-2 block text-sm text-grey-700" :lang="zhAttr">{{ excerptOf(latestArticle, 42) }}</span>
        </RouterLink>
      </section>

      <ALanguageSwitch />
    </div>
  </AStepPage>
</template>
