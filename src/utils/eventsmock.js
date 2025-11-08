// src/services/events.js
export async function fetchEvents() {
  // mock latency
  await new Promise(r => setTimeout(r, 300));
  return [
    {
      id: 'evt_001',
      title: 'Taipei City Run 10K',
      date: '2025-12-14 06:30',
      location: 'Daan Forest Park',
      host: 'Zzyzx Club',
      cover: 'https://picsum.photos/seed/run10k/800/480',
    },
    {
      id: 'evt_002',
      title: 'Riverside Cycling Meetup',
      date: '2025-12-18 07:00',
      location: 'Tamsui River Bikeway',
      host: 'Bike TW',
      cover: 'https://picsum.photos/seed/cycle/800/480',
    },
    {
      id: 'evt_003',
      title: 'Sunset Yoga @ Xinyi',
      date: '2025-12-20 17:30',
      location: 'Xinyi Civic Square',
      host: 'Flow Studio',
      cover: 'https://picsum.photos/seed/yoga/800/480',
    },
  ];
}
