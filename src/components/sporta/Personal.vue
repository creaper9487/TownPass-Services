<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useSportaStore, eventStruct, categoryStruct } from '@/stores/sporta';

const sportaStore = useSportaStore();
// 使用 computed 讓資料響應式更新
const myEvents = computed(() => sportaStore.getMyEvents);
const mySubCats = computed(() => sportaStore.getMySubCats);

onMounted(async () => {
    console.log('Personal.vue: 開始載入資料');
    await sportaStore.fetchAll();
    console.log('Personal.vue: 資料載入完成');
    console.log('Categories:', sportaStore.categories);
    console.log('Events:', sportaStore.events);
    console.log('My subcats:', mySubCats.value);
    console.log('My events:', myEvents.value);
});
</script>

<template>
    <div class="p-4">
        <h2 class="text-2xl font-bold mb-4 w-full justify-center flex bg-main-300 py-6 text-black">我的 Sporta</h2>
        <div class="mb-6">
            <h3 class="text-lg font-semibold mb-2" v-bind:key="myEvents.length">My Subscribed Categories</h3>
            <div class="flex flex-row relative">
                <div v-for="category in mySubCats" :key="category.id" class="w-fit p-3 border rounded-lg shadow-sm">
                    <div class="relative">
                        <img :src="category.img" alt="Category Image" class="w-64 h-32 object-cover mb-2 rounded" />
                        <span class="bg-gradient-to-br from-transparent to-black absolute inset-0 rounded" />
                    </div>
                    <p>{{ category.name }}</p>
                </div>
            </div>
        </div>

        <div>
            <h3 class="text-lg font-semibold mb-2">My Events</h3>
            <div class="space-y-2">
                <div v-for="event in myEvents" :key="event.id" class="p-3 border rounded-lg shadow-sm">
                    <h4 class="font-medium">{{ event.title }}</h4>
                    <p class="text-sm text-gray-600">{{ event.organizer }}</p>
                    <p class="text-sm">{{ event.location }}</p>
                </div>
            </div>
        </div>
    </div>
</template>