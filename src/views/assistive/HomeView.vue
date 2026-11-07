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
import { serviceShortTitle, serviceTitle } from '@/utils/assistive/services';
import { t, zhAttr } from '@/i18n/assistive';
import { catalog, variantInfo } from '@/utils/assistive/catalog';
import { centerById, centerShort, formatDate } from '@/utils/assistive/centers';
import {
  effectiveStatus,
  listArrivals,
  listReservations,
  loadArrivals,
  statusText,
  type ArrivalNotice
} from '@/utils/assistive/api';
import { articles, excerptOf } from '@/utils/assistive/education';
import type { Reservation } from '@/utils/assistive/types';

const store = useAssistiveStore();
const reservations = ref<Reservation[]>([]);
const arrivals = ref<ArrivalNotice[]>(listArrivals());
const activityLoaded = ref(false);

// 借用卡片放官方品項照片（輪椅、助行器、拐杖）
const photos = computed(() =>
  catalog.value
    .filter((c) => ['輪椅', '助行器', '拐杖'].some((n) => c.name.startsWith(n)))
    .map((c) => c.image)
    .filter((img): img is string => !!img)
);

const arrived = computed(
  () =>
    [...arrivals.value]
      .filter((notice) => notice.status === 'arrived')
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0]
);
const waitingCount = computed(
  () => arrivals.value.filter((notice) => notice.status !== 'arrived').length
);
const activeReservations = computed(() =>
  reservations.value
    .filter((reservation) =>
      ['booked', 'submitted', 'confirmed'].includes(effectiveStatus(reservation))
    )
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
  void Promise.allSettled([listReservations(), loadArrivals()]).then(([booking, notices]) => {
    if (booking.status === 'fulfilled') reservations.value = booking.value;
    if (notices.status === 'fulfilled') arrivals.value = notices.value;
    activityLoaded.value = true;
  });
});
</script>

<template>
  <AStepPage :title="t('app.title')" hide-header>
    <div class="flex flex-col gap-4 bg-grey-50 px-4 py-4 pb-8">
      <ClosureNotice v-if="store.closureNotices.length" :items="store.closureNotices" />

      <nav :aria-label="serviceTitle('borrow')">
        <AServiceCard
          class="a-rise"
          hero
          :title="serviceTitle('borrow')"
          :photos="photos"
          :to="{ name: 'assistive-rules', params: { service: 'borrow' } }"
          @click="store.begin('borrow')"
        />
      </nav>

      <section aria-labelledby="home-activity-title" class="tp-card rounded-xl p-4">
        <div class="flex flex-wrap items-center justify-between gap-x-3">
          <h2 id="home-activity-title" class="tp-h3-semibold">{{ t('home.activity') }}</h2>
          <RouterLink
            :to="{ name: 'assistive-reservations' }"
            class="a11y-focus -my-1 flex min-h-11 items-center text-sm font-semibold text-primary-700 underline"
          >
            {{ t('home.viewAll') }}<span v-if="activityCount"> ({{ activityCount }})</span>
          </RouterLink>
        </div>

        <RouterLink
          v-if="arrived"
          :to="{
            name: 'assistive-borrow-quick',
            params: { service: 'borrow', variantId: arrived.variantId }
          }"
          class="a11y-focus mt-3 flex min-h-16 items-center justify-between gap-3 rounded-lg bg-secondary-50 p-3"
        >
          <span class="min-w-0">
            <span class="block font-semibold">
              {{
                t('home.arrived', { name: variantInfo(arrived.variantId)?.name ?? arrived.label })
              }}
            </span>
            <span class="mt-1 block text-sm text-grey-700">
              {{ t('reservations.arrivalReserve') }}
            </span>
          </span>
          <span aria-hidden="true" class="text-primary-700">→</span>
        </RouterLink>

        <RouterLink
          v-if="currentReservation"
          :to="{ name: 'assistive-reservation', params: { id: currentReservation.id } }"
          class="a11y-focus mt-3 flex min-h-16 flex-wrap items-center justify-between gap-3 rounded-lg bg-grey-50 p-3"
        >
          <span class="min-w-0 flex-1 basis-32">
            <span class="block font-semibold">{{ reservationItem(currentReservation) }}</span>
            <span
              v-if="reservationCenter(currentReservation)"
              class="mt-1 block text-sm text-grey-700"
            >
              {{ t('reservations.centerLine', { center: reservationCenter(currentReservation) }) }}
            </span>
            <span class="tp-tag mt-2">{{ statusText(currentReservation) }}</span>
          </span>
          <span v-if="currentReservation.pickupDeadline" class="text-right">
            <span class="block text-sm text-grey-700">{{ t('pickup.deadline') }}</span>
            <span class="block text-base font-semibold">
              {{ formatDate(new Date(currentReservation.pickupDeadline)) }}
            </span>
          </span>
        </RouterLink>
        <p v-if="waitingCount" class="mt-3 text-sm text-grey-700">
          {{ t('home.waitingArrivals', { n: waitingCount }) }}
        </p>
        <p
          v-if="activityLoaded && !arrived && !currentReservation && !waitingCount"
          class="mt-3 text-sm text-grey-700"
        >
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

      <section
        v-if="latestArticle"
        aria-labelledby="home-education-title"
        class="tp-card rounded-xl p-4"
      >
        <div class="flex flex-wrap items-center justify-between gap-x-3">
          <h2 id="home-education-title" class="tp-h3-semibold">{{ t('home.education') }}</h2>
          <RouterLink
            :to="{ name: 'assistive-education' }"
            class="a11y-focus -my-1 flex min-h-11 items-center text-sm font-semibold text-primary-700 underline"
          >
            {{ t('home.viewAll') }}
          </RouterLink>
        </div>
        <RouterLink
          :to="{ name: 'assistive-education-article', params: { id: latestArticle.id } }"
          class="a11y-focus mt-3 block rounded-lg bg-grey-50 p-3"
        >
          <span class="block font-semibold text-primary-700" :lang="zhAttr">
            {{ latestArticle.name }}
          </span>
          <span class="mt-1 block text-sm text-grey-700" :lang="zhAttr">
            {{ latestArticle.date }}
          </span>
          <span class="mt-2 line-clamp-2 block text-sm text-grey-700" :lang="zhAttr">
            {{ excerptOf(latestArticle, 42) }}
          </span>
        </RouterLink>
      </section>

      <ALanguageSwitch />
    </div>
  </AStepPage>
</template>
