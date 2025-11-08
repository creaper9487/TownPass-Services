// src/services/events.js
export async function fetchEvents() {
  // mock latency
  await new Promise(r => setTimeout(r, 300));
  
  // Mock data based on the new API structure
  const mockApiData = [
    {
      "_id": "690f66bdd76106b852af6c13",
      "title": "Red speak.",
      "organizer": "54793b78-2e57-446e-a1da-37ccc915892e",
      "participants": [
        "8ddd0e6c-bbb0-40be-822b-6fc6d5e90a5d",
        "054076ea-e0e3-40c2-977c-c9b8ed092f32"
      ],
      "category": "690f66bdd76106b852af6bfb",
      "location": "690f66bdd76106b852af6c00",
      "description": [
        "Goal inside meet college will.",
        "High evening by any see kitchen dream."
      ],
      "image": "https://placekitten.com/869/1018",
      "start_time": "2025-12-08T15:50:21.170000",
      "end_time": "2025-12-08T18:50:21.170000",
      "created_at": "2025-11-08T15:50:21.170000"
    },
    {
      "_id": "690f66bdd76106b852af6c14",
      "title": "Point look.",
      "organizer": "2d1b84bc-67bd-4432-b433-fde4bb896f4f",
      "participants": [
        "f83d8c61-ada3-4400-b6c7-fddf033c5e3c",
        "26131dfd-a37d-470b-8bb4-52458f0f5e64"
      ],
      "category": "690f66bdd76106b852af6bfd",
      "location": "690f66bdd76106b852af6c07",
      "description": [
        "None which see PM employee serve sure.",
        "Truth between per question some. Important paper firm part tree federal clear."
      ],
      "image": "https://picsum.photos/630/322",
      "start_time": "2025-12-04T15:50:21.170000",
      "end_time": "2025-12-04T21:50:21.170000",
      "created_at": "2025-11-08T15:50:21.170000"
    }
  ];
  
  // Transform the data to match frontend expectations
  return mockApiData.map(event => ({
    id: event._id,
    title: event.title,
    organizer: event.organizer,
    participants: event.participants,
    category: event.category,
    location: event.location,
    description: event.description.join('\n'),
    image: event.image,
    starttime: event.start_time,
    endtime: event.end_time
  }));
}


/** 可直接改成 fetch('/api/events', { method:'POST', body:FormData 或 JSON }) */
export async function createEvent(payload) {
  // 模擬網路
  await new Promise(r => setTimeout(r, 350));
  // 這裡回傳伺服器建立後的物件（mock）
  return { id: 'evt_' + Math.random().toString(36).slice(2, 8), ...payload };
}
