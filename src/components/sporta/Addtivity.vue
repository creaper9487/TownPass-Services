<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import ServiceStep from '@/components/molecules/ServiceStep.vue';
import { useSportaStore } from '@/stores/sporta';
import mapboxgl from 'mapbox-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';

// Import Mapbox CSS
import 'mapbox-gl/dist/mapbox-gl.css';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

const sportaStore = useSportaStore();

// Mapbox Access Token - Set via environment variable
// Create a .env file and add: VITE_MAPBOX_ACCESS_TOKEN=your_token_here
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || 'YOUR_MAPBOX_ACCESS_TOKEN';

// Example progress data - adjust based on your needs
const dropdownOptions = ref(sportaStore.activeCategories);
const selectedOption = ref('');
const PlaceDrpdownOptions = ref(sportaStore.activeLocations);
const selectedPlace = ref('');
const totalSteps = ref(3);
const currentStep = ref(1);
const goingppl = ref(1);

// Mapbox related variables
let map: mapboxgl.Map | null = null;
let draw: MapboxDraw | null = null;
const pathCoordinates = ref<[number, number][]>([]);

// Check if user exp > 5000
const showMapDrawer = computed(() => {
    return (sportaStore.userdata?.exp || 0) > 5000;
});

onMounted(() => {
    if (showMapDrawer.value) {
        initializeMap();
    }
});

onUnmounted(() => {
    if (map) {
        map.off('draw.create', handleDrawCreate);
        map.remove();
    }
});

const initializeMap = () => {
    // Initialize Mapbox map
    map = new mapboxgl.Map({
        container: 'map-container',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [121.5654, 25.0330], // Taipei coordinates
        zoom: 12
    });

    // Initialize MapboxDraw
    draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
            line_string: true, // Allow drawing lines
            trash: true        // Allow deletion
        }
    });

    // Add drawing tool to map
    map.addControl(draw, 'top-left');

    // Listen to draw.create event
    map.on('draw.create', handleDrawCreate);
};

const handleDrawCreate = (e: any) => {
    const feature = e.features[0];

    if (feature && feature.geometry.type === 'LineString') {
        // Extract coordinates array
        pathCoordinates.value = feature.geometry.coordinates;
        console.log('繪製完成，座標點：', pathCoordinates.value);
    }
};

const handleSubmit = async (event: Event) => {
    event.preventDefault();
    
    const payload: any = {
        category: selectedOption.value,
        people: goingppl.value,
    };

    // If map drawer is shown, send path coordinates instead of location
    if (showMapDrawer.value) {
        payload.path = pathCoordinates.value;
    } else {
        payload.location = selectedPlace.value;
    }

    try {
        const response = await fetch('192.168.22.42:8000/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const result = await response.json();
            console.log('提交成功:', result);
            // Optional: Clear the drawing after successful submission
            if (draw) {
                draw.deleteAll();
                pathCoordinates.value = [];
            }
        } else {
            console.error('提交失敗:', response.statusText);
        }
    } catch (error) {
        console.error('提交時發生錯誤:', error);
    }
};
</script>

<template>
    <div class="p-4">
        <div class="my-5">
            <ServiceStep :stepCount="totalSteps" :activeStep="currentStep" />
        </div>
        
        <!-- Your content here -->
         <form>
            <div class="mb-4">
                <label for="dropdown" class="block text-sm font-medium text-gray-700 mb-2">
                    預約類型
                </label>
                <select 
                    id="dropdown"
                    v-model="selectedOption"
                    class="w-full px-3 py-2 border text-black border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="" disabled>Choose an option</option>
                    <option 
                        v-for="option in dropdownOptions" 
                        :key="option.name" 
                        :value="option.name"
                    >
                        {{ option.name }}
                    </option>
                </select>
            </div>
            
            <!-- Location Dropdown (only if exp <= 5000) -->
            <div v-if="!showMapDrawer" class="mb-4">
                <label for="location-dropdown" class="block text-sm font-medium text-gray-700 mb-2">
                    預約地點
                </label>
                <select 
                    id="location-dropdown"
                    v-model="selectedPlace"
                    class="w-full px-3 py-2 border text-black border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="" disabled>Choose an option</option>
                    <option 
                        v-for="option in PlaceDrpdownOptions" 
                        :key="option" 
                        :value="option"
                    >
                        {{ option }}
                    </option>
                </select>
            </div>

            <!-- Map Drawer (only if exp > 5000) -->
            <div v-else class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    繪製路線 (經驗值 > 5000)
                </label>
                <div 
                    id="map-container" 
                    class="w-full h-96 rounded-md border border-gray-300"
                ></div>
                <p class="text-xs text-gray-500 mt-2">
                    使用繪圖工具在地圖上繪製您的活動路線
                </p>
            </div>

            <div class="mb-4">
                <label for="goingppl" class="block text-sm font-medium text-gray-700 mb-2">
                    人數
                </label>
                <input 
                    type="number" 
                    id="goingppl"
                    v-model.number="goingppl"
                    min="1"
                    step="1"
                    class="w-full px-3 py-2 border text-black border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            </div>
            <div class="max-h-1/2 m-1/2 overflow-y-auto">
                <p>定型規定：</p>
                <span class="text-md bg-grey-200 p-6 rounded-lg block whitespace-pre-line">
                    {{ sportaStore.term }}
                </span>
            </div>
            <button 
                type="submit" 
                class=" text-lg mt-4 w-full bg-main-600 text-white py-2 px-4 rounded-md hover:bg-main-700 transition-colors duration-200"
                @click="handleSubmit"
                >
                提交預約
            </button>
         </form>
    </div>
</template>

<style scoped lang="postcss">
/* Add your custom styles here if needed */
</style>