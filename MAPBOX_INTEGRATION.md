# Mapbox Integration Guide

## Overview

The Addtivity.vue component now includes Mapbox GL JS with drawing capabilities for advanced users (exp > 5000).

## Features

- **Conditional Display**: 
  - Users with exp ≤ 5000: See location dropdown
  - Users with exp > 5000: See interactive map with drawing tools

- **Drawing Capabilities**: 
  - Draw lines (routes) on the map
  - Delete drawn routes
  - Automatically capture coordinates when drawing is complete

- **Data Format**: 
  - Coordinates are captured in `[[lon, lat], [lon, lat], ...]` format
  - Sent to backend as `path` field instead of `location`

## Setup Instructions

### 1. Get Mapbox Access Token

1. Visit [Mapbox Account](https://account.mapbox.com/access-tokens/)
2. Sign up or log in
3. Create a new access token or copy an existing one

### 2. Configure Environment Variable

Create a `.env` file in the project root:

```env
VITE_MAPBOX_ACCESS_TOKEN=pk.your_actual_mapbox_token_here
```

### 3. Install Dependencies (Already Done)

```bash
pnpm add mapbox-gl @mapbox/mapbox-gl-draw
pnpm add -D @types/mapbox-gl @types/mapbox__mapbox-gl-draw
```

## How It Works

### For Regular Users (exp ≤ 5000)

```vue
<!-- Shows location dropdown -->
<select v-model="selectedPlace">
  <option>Location 1</option>
  <option>Location 2</option>
</select>
```

Submission payload:
```json
{
  "category": "basketball",
  "people": 5,
  "location": "Location 1"
}
```

### For Advanced Users (exp > 5000)

```vue
<!-- Shows interactive map with drawing tools -->
<div id="map-container"></div>
```

Submission payload:
```json
{
  "category": "basketball",
  "people": 5,
  "path": [
    [121.5654, 25.0330],
    [121.5700, 25.0350],
    [121.5750, 25.0380]
  ]
}
```

## Usage

1. **Drawing a Route**:
   - Click the line tool in the top-left corner
   - Click on the map to add points
   - Double-click or press Enter to finish

2. **Deleting a Route**:
   - Click the trash icon
   - Select the route to delete
   - Click delete

3. **Submitting**:
   - Draw your route
   - Fill in other form fields
   - Click "提交預約"
   - The coordinates are automatically sent to the backend

## Code Structure

### Key Variables

```typescript
const showMapDrawer = computed(() => {
    return (sportaStore.userdata?.exp || 0) > 5000;
});

const pathCoordinates = ref<[number, number][]>([]);
```

### Map Initialization

```typescript
const initializeMap = () => {
    map = new mapboxgl.Map({
        container: 'map-container',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [121.5654, 25.0330], // Taipei
        zoom: 12
    });

    draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
            line_string: true,
            trash: true
        }
    });

    map.addControl(draw, 'top-left');
    map.on('draw.create', handleDrawCreate);
};
```

### Coordinate Extraction

```typescript
const handleDrawCreate = (e: any) => {
    const feature = e.features[0];
    if (feature && feature.geometry.type === 'LineString') {
        pathCoordinates.value = feature.geometry.coordinates;
        console.log('繪製完成，座標點：', pathCoordinates.value);
    }
};
```

## Backend API Expected Format

The backend should handle both formats:

```typescript
// Regular user submission
{
  category: string;
  people: number;
  location: string;
}

// Advanced user submission
{
  category: string;
  people: number;
  path: [number, number][]; // Array of [longitude, latitude]
}
```

## Customization

### Change Map Center
Edit the coordinates in `initializeMap()`:
```typescript
center: [121.5654, 25.0330], // [longitude, latitude]
```

### Change Map Style
```typescript
style: 'mapbox://styles/mapbox/streets-v12', // or satellite-v9, outdoors-v12, etc.
```

### Change EXP Threshold
```typescript
const showMapDrawer = computed(() => {
    return (sportaStore.userdata?.exp || 0) > 5000; // Change this number
});
```

## Troubleshooting

### Map Not Showing
1. Check if `.env` file exists with valid token
2. Verify user exp > 5000
3. Check browser console for errors
4. Ensure container has proper dimensions (h-96 class)

### Drawing Not Working
1. Verify MapboxDraw CSS is imported
2. Check if draw controls are visible in top-left
3. Try clicking the line tool icon before drawing

### Coordinates Not Captured
1. Check console logs when drawing completes
2. Verify `handleDrawCreate` is triggered
3. Ensure geometry type is 'LineString'

## Dependencies

- `mapbox-gl`: ^3.16.0
- `@mapbox/mapbox-gl-draw`: ^1.5.1
- `@types/mapbox-gl`: ^3.4.1
- `@types/mapbox__mapbox-gl-draw`: ^1.4.9

## License

Mapbox GL JS is licensed under the Mapbox Terms of Service.
