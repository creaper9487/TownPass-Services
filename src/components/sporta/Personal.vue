<script setup lang="ts">
import { computed } from 'vue';
import { useSportaStore, type userInfo } from '@/stores/sporta';
import { useConnectionMessage } from '@/composables/useConnectionMessage';
import { useHandleConnectionData } from '@/composables/useHandleConnectionData';
const sportaStore = useSportaStore();

useConnectionMessage('userinfo', null);

useHandleConnectionData((event: { data: string }) => {
    const result = JSON.parse(event.data);
    sportaStore.user.id = result.data.id
});

sportaStore.fetchAllData(sportaStore.user.id);
</script>
<template>
    <div class="w-screen max-h-screen flex flex-col justify-left items-center">
        <div class="flex justify-start items-center m-8 border-2 w-1/2">
            <h2 class="text-2xl">訂閱活動</h2>
            <div v-for="event in sportaStore.userEvent" :key="event.id">
                <div class="relative w-32 h-32">
                    <img :src="event.image" alt="Event Image" class="w-full h-full object-cover rounded-md"/>
                    <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/50 rounded-md" />
                </div>
            </div>
        </div>
    </div>
</template> 

