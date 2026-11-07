<script setup lang="ts">
import { computed, ref } from 'vue';
import BaseButton from '@/components/atoms/BaseButton.vue';
import { useAssistiveStore } from '@/stores/assistive';
import { useAssistiveNative } from '@/composables/useAssistiveNative';
import { useAssistiveLocate } from '@/composables/useAssistiveLocate';
import { kmBetween } from '@/utils/assistive/centers';
import catalogJson from '@/data/assistive-catalog.json';
import type { RentalStore } from '@/utils/assistive/types';

const props = defineProps<{ stores: RentalStore[] }>();
const store = useAssistiveStore();
const native = useAssistiveNative();
const { locate, locating, message } = useAssistiveLocate();
const showAll = ref(false);

const categoryName = (id: string) =>
  (catalogJson as { id: string; name: string }[]).find((c) => c.id === id)?.name ?? '';

const rows = computed(() => {
  const loc = store.location;
  const list = props.stores.map((s) => ({
    ...s,
    km:
      loc && s.lat !== undefined && s.lng !== undefined
        ? kmBetween(loc.lat, loc.lng, s.lat, s.lng)
        : null
  }));
  return loc ? list.sort((a, b) => (a.km ?? Infinity) - (b.km ?? Infinity)) : list;
});
const visible = computed(() => (showAll.value ? rows.value : rows.value.slice(0, 5)));
const canSortByDistance = computed(() => props.stores.some((s) => s.lat !== undefined));

const mapUrl = (s: RentalStore) =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.address.replace(/\s/g, ''))}`;
</script>

<template>
  <section aria-labelledby="rental-title">
    <h3 id="rental-title" class="tp-h3-semibold">附近的民間租賃特約門市</h3>
    <p class="mt-1 text-sm text-grey-700">
      北市輔具租賃特約門市，可以直接洽詢有沒有現貨。{{ store.location ? '已依距離排序。' : '' }}
    </p>
    <BaseButton
      v-if="!store.location && canSortByDistance"
      outline
      class="mt-3 w-full"
      :aria-busy="locating"
      @click="locate"
    >
      依目前位置排序
    </BaseButton>
    <p v-if="message" role="status" class="mt-2 text-sm text-grey-700">{{ message }}</p>
    <ul class="mt-3 flex flex-col gap-3">
      <li v-for="s in visible" :key="s.id" class="rounded-lg bg-white p-3">
        <p class="tp-h3-semibold">{{ s.name }}</p>
        <p class="mt-1 text-sm">{{ s.address }}</p>
        <p v-if="s.km !== null" class="mt-1 text-sm text-grey-700">
          距離約 {{ s.km.toFixed(1) }} 公里
        </p>
        <p v-if="s.categories.length" class="mt-1 text-sm text-grey-700">
          可提供：{{ s.categories.map(categoryName).filter(Boolean).join('、') }}
        </p>
        <div class="mt-3 grid grid-cols-2 gap-2">
          <BaseButton outline @click="native.callPhone(s.phone)">
            撥打電話<span class="sr-only">：{{ s.name }}</span>
          </BaseButton>
          <BaseButton outline @click="native.openMap(mapUrl(s))">
            導航前往<span class="sr-only">：{{ s.name }}</span>
          </BaseButton>
        </div>
      </li>
    </ul>
    <button
      v-if="rows.length > 5 && !showAll"
      type="button"
      class="a11y-focus mt-3 min-h-11 text-base font-semibold text-primary-700 underline"
      @click="showAll = true"
    >
      顯示全部 {{ rows.length }} 家
    </button>
  </section>
</template>
