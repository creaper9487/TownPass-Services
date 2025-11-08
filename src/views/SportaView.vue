<script setup lang="ts">
import { ref } from 'vue';
import { useSportaStore } from '@/stores/sporta';
import Personal from '@/components/sporta/Personal.vue';
import Activity from '@/components/sporta/Activity.vue';
import Addtivity from '@/components/sporta/Addtivity.vue';
import { useConnectionMessage } from '@/composables/useConnectionMessage';
const testvar = useConnectionMessage("userinfo",null);
console.log("testvar:",testvar);
const sportaStore = useSportaStore();
const page = ref(0);
</script>

<template>
  <div class="min-h-screen bg-gray-50 ">
    
    <nav class="bg-white shadow-sm border-b font-bold sticky top-0 z-40">
      <div class="max-w-6xl mx-auto">
        <div class="flex justify-center">
          <div class="flex space-x-8">
            <button 
              @click="page = 0"
              :class="[
                'px-4 py-4 text-sm  border-b-4 transition-colors duration-200',
                page === 0 
                  ? 'text-main-600 border-main-600' 
                  : 'text-gray-600 border-transparent hover:text-gray-800 hover:border-gray-300'
              ]"
            >
              我的活動
            </button>
            <button 
              @click="page = 1"
              :class="[
                'px-4 py-4 text-sm  border-b-4 transition-colors duration-200',
                page === 1 
                  ? 'text-main-600 border-main-600' 
                  : 'text-gray-600 border-transparent hover:text-gray-800 hover:border-gray-300'
              ]"
            >
              活動列表
            </button>
            <button 
              @click="page = 2"
              :class="[
                'px-4 py-4 text-sm  border-b-4 transition-colors duration-200',
                page === 2 
                  ? 'text-main-600 border-main-600' 
                  : 'text-gray-600 border-transparent hover:text-gray-800 hover:border-gray-300'
              ]"
            >
              建立活動
            </button>
          </div>
        </div>
      </div>
    </nav>
    <!-- Main Content -->
    <main>
      <Personal v-if="page === 0"/>
      <Activity v-if="page === 1"/>
      <Addtivity v-if="page === 2"/>
      <!-- Navigation Header -->
    </main>
  </div>
</template>