import {useSportaStore} from '@/stores/sporta'

export async function fetchCategories() {
  await new Promise(r => setTimeout(r, 120));
  return ["Running", "Cycling", "Yoga", "Basketball", "Hiking", "Swimming", "Badminton", "Football"];
}

export async function fetchLocations() {
  await new Promise(r => setTimeout(r, 120));
  return ["Taipei City", "New Taipei", "Taoyuan", "Hsinchu", "Taichung", "Tainan", "Kaohsiung", "Keelung"];
}

/** Mock search: apply simple filters locally */
export async function searchEvents({ q = "", category = "", location = "" } = {}) {
  await new Promise(r => setTimeout(r, 200));
  const base = [
    { id: "evt_101", title: "Dadaocheng 5K Fun Run", date: "2025-12-12 06:30", location: "Taipei City", host: "City Run", cover: "https://picsum.photos/seed/funrun/800/480", category: "Running" },
    { id: "evt_102", title: "Riverside Night Ride",  date: "2025-12-15 19:00", location: "New Taipei",  host: "Bike TW",   cover: "https://picsum.photos/seed/ride/800/480",   category: "Cycling" },
    { id: "evt_103", title: "Sunrise Yoga Session",  date: "2025-12-16 06:00", location: "Taipei City", host: "Flow Studio",cover: "https://picsum.photos/seed/sunrise/800/480",category: "Yoga" },
    { id: "evt_104", title: "Weekend Basketball 3x3",date: "2025-12-21 15:30", location: "Taoyuan",     host: "Hoops",     cover: "https://picsum.photos/seed/3x3/800/480",   category: "Basketball" },
    { id: "evt_105", title: "Yangmingshan Hike",     date: "2025-12-22 08:00", location: "Taipei City", host: "Hike Club", cover: "https://picsum.photos/seed/hike/800/480",  category: "Hiking" },
  ];
  return base.filter(e => {
    const okQ = q ? (e.title.toLowerCase().includes(q.toLowerCase())) : true;
    const okC = category ? (e.category === category) : true;
    const okL = location ? (e.location === location) : true;
    return okQ && okC && okL;
  });
}
export async function realSearchEvents({ q = "", category = "", location = "" } = {}) {
  // Get the store instance inside the function
  const sportaStore = useSportaStore();
  
  // Fetch actual event data from the API
  await sportaStore.fetchEvents();
  await sportaStore.fetchCategories();
  await sportaStore.fetchLocations();
  
  const events = sportaStore.events;
  const categories = sportaStore.categories;
  const locations = sportaStore.locations;
  
  console.log('Events:', events);
  console.log('Categories:', categories);
  console.log('Locations:', locations);
  
  // Create lookup maps for category and location names
  const categoryMap = new Map(categories.map(cat => [cat.id, cat.name]));
  const locationMap = new Map(locations.map(loc => [loc.id, loc.name]));
  
  // Map the data structure from sporta.ts to match the expected format
  const base = events.map(e => {
    // Try to resolve category and location names if they are IDs
    let categoryName = e.category
    let locationName = e.location
    
    // Find category name if e.category is an ID
    const category = categories.find(cat => cat.id === e.category)
    if (category) categoryName = category.name
    
    // Find location name if e.location is an ID
    const location = locations.find(loc => loc.id === e.location)
    if (location) locationName = location.name
    
    return {
      id: e.id,
      title: e.title,
      starttime: e.starttime, // Using starttime from sporta.ts eventInfo
      endtime: e.endtime,
      location: locationName, // Resolved location name
      organizer: e.organizer, // Using organizer from sporta.ts eventInfo
      cover: e.image || `https://picsum.photos/seed/${e.id}/800/480`, // Using image from sporta.ts eventInfo (renamed to cover for card component)
      category: categoryName, // Resolved category name
      description: e.description,
      capacity: e.capacity,
      price: e.price
    }
  });
  
  return base.filter(e => {
    const okQ = q ? (e.title.toLowerCase().includes(q.toLowerCase())) : true
    
    // Handle category filtering by ID
    let okC = true
    if (category) {
      // Check if the selected category ID matches the original event category
      const originalEvent = events.find(orig => orig.id === e.id)
      okC = originalEvent ? (originalEvent.category === category) : false
    }
    
    // Handle location filtering by ID  
    let okL = true
    if (location) {
      // Check if the selected location ID matches the original event location
      const originalEvent = events.find(orig => orig.id === e.id)
      okL = originalEvent ? (originalEvent.location === location) : false
    }
    
    return okQ && okC && okL
  })
}