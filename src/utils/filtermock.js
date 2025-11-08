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