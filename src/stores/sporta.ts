
import { defineStore } from 'pinia';

export class userInfo {
  id: string;
  exp: number;
  subevents: string[];
  subCategories: string[];
}
export class eventInfo {
  id: string;
  title: string;
  organizer: string;
  participants: string[];
  category: string;
  location: string;
  description: string;
  image: string;
  starttime: string;
  endtime: string;
}
export class locationInfo {
  id:string;
  name: string;
  coordinates: number[];
  subscribers: string[];
}
export class categoryInfo {
  id: string;
  name: string;
  subscribers: string[];
}
export const useSportaStore = defineStore('sporta', {
  state: () => ({
    user: {} as userInfo,
    events: [] as eventInfo[],
    locations: [] as locationInfo[],
    categories: [] as categoryInfo[],
    activeCategories: [] as string[],
    userEvent: [] as eventInfo[],
  }),
  actions: {
    async fetchUser(id: string) {
      try {
        const response = await fetch(`http://localhost:8000/api/user/${id}`, {
          method: 'GET'
        });
        this.user = await response.json();
      } catch (error) {
        try {
          const response = await fetch(`http://localhost:8000/api/user/${id}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              id
            })
          });
        } catch (error) {
          console.log(error);
        }
      }
    },
    async fetchEvents() {
      try {
        const response = await fetch('http://localhost:8000/api/events/', {
          method: 'GET'
        });
        this.events = await response.json();
      } catch (error) {
        // Fallback to mock data if API is not available
        console.log('API not available, using mock data');
        // Use dynamic import with type assertion
        const eventsMock = await import('@/utils/eventsmock.js') as any;
        this.events = await eventsMock.fetchEvents();
      }
    },
    async fetchLocations() {
      try {
        const response = await fetch('http://localhost:8000/api/locations/', {
          method: 'GET'
        });
        this.locations = await response.json();
      } catch (error) {
        // Fallback to mock data if API is not available
        console.log('Locations API not available, using mock data');
        this.locations = [
          { id: 'loc_001', name: 'Daan Forest Park', coordinates: [121.5654, 25.0265], subscribers: [] },
          { id: 'loc_002', name: 'Tamsui River Bikeway', coordinates: [121.4654, 25.1765], subscribers: [] },
          { id: 'loc_003', name: 'Xinyi Civic Square', coordinates: [121.5654, 25.0365], subscribers: [] },
        ];
      }
    },
    async fetchCategories() {
      try {
        const response = await fetch('http://localhost:8000/api/categories/', {
          method: 'GET'
        });
        this.categories = await response.json();
      } catch (error) {
        // Fallback to mock data if API is not available
        console.log('Categories API not available, using mock data');
        this.categories = [
          { id: 'cat_001', name: 'Running', subscribers: [] },
          { id: 'cat_002', name: 'Cycling', subscribers: [] },
          { id: 'cat_003', name: 'Yoga', subscribers: [] },
          { id: 'cat_004', name: 'Basketball', subscribers: [] },
          { id: 'cat_005', name: 'Hiking', subscribers: [] },
        ];
      }
    },
    async fetchAllData(id: string) {
      // Skip API calls for now and use mock data directly
      // await this.fetchUser(id);
      // await this.fetchEvents();
      // await this.fetchLocations();
      // await this.fetchCategories();
      this.userEvent = await this.fetchEventByGuy();
    },
    //=============================================================//
    async fetchEventByGuy(): Promise<eventInfo[]> {
      const response = await fetch(`http://localhost:8000/api/events/query?participant=${this.user.id}&limit=10`, {
        method: 'GET'
      });
      return await response.json();
      
      // Using mock data for now
      // const { fetchEvents } = await import('@/utils/eventsmock.js');
      // const mockEvents = await fetchEvents();
      // return mockEvents;
    },
    async SubmitEvent(payload: eventInfo) {
      await fetch('http://localhost:8000/api/events/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    }

  }
});
