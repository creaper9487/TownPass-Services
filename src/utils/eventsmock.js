// src/services/events.js
export async function fetchEvents() {
  // mock latency
  await new Promise(r => setTimeout(r, 300));
  return [
    {
      id: 'evt_001',
      title: 'Taipei City Run 10K',
      organizer: 'Zzyzx Club',
      participants: [],
      category: 'Running',
      location: 'Daan Forest Park',
      description: 'Join us for a 10K run in the city!',
      cover: 'https://picsum.photos/seed/run10k/800/480',
      starttime: '2025-12-14 06:30',
      endtime: '2025-12-14 09:00',
    },
    {
      id: 'evt_002',
      title: 'Riverside Cycling Meetup',
      organizer: 'Bike TW',
      participants: [],
      category: 'Cycling',
      location: 'Tamsui River Bikeway',
      description: 'Explore the riverside on two wheels!',
      cover: 'https://picsum.photos/seed/cycle/800/480',
      starttime: '2025-12-18 07:00',
      endtime: '2025-12-18 10:00',
    },
    {
      id: 'evt_003',
      title: 'Sunset Yoga @ Xinyi',
      organizer: 'Flow Studio',
      participants: [],
      category: 'Yoga',
      location: 'Xinyi Civic Square',
      description: 'Relax and stretch with sunset views.',
      cover: 'https://picsum.photos/seed/yoga/800/480',
      starttime: '2025-12-20 17:30',
      endtime: '2025-12-20 19:00',
    },
  ];
}
