<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useSportaStore, eventStruct, categoryStruct } from '@/stores/sporta';

const sportaStore = useSportaStore();
// 使用 computed 讓資料響應式更新
const myEvents = computed(() => sportaStore.getMyEvents);
const mySubCats = computed(() => sportaStore.getMySubCats);
const userExp = computed(() => sportaStore.userdata.exp || 0);
const maxExp = 10000;
const expPercentage = computed(() => Math.min((userExp.value / maxExp) * 100, 100));

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
        
        <!-- Experience Indicator -->
        <div class="mb-6 p-4 border rounded-lg shadow-sm bg-gradient-to-r from-blue-50 to-purple-50">
            <div class="flex justify-between items-center mb-2">
                <h3 class="text-lg font-semibold text-gray-800">Experience Level</h3>
                <span class="text-sm font-medium text-gray-600">{{ userExp }} / {{ maxExp }} EXP</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                    class="h-full bg-gradient-to-r from-main-300 to-main-600 rounded-full transition-all duration-500 ease-out"
                    :style="{ width: expPercentage + '%' }"
                ></div>
            </div>
            <div class="flex justify-between text-xs text-gray-500 mt-1">
                <span>Beginner</span>
                <span>Expert</span>
            </div>
        </div>

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