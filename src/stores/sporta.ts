
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
    activeCategories: [] as string[]
  }),
  actions: {
    async fetchUser(id: string) {
      try {
        const response = await fetch(`localhost:8000/api/user/${id}`, {
          method: 'GET'
        });
        this.user = await response.json();
      } catch (error) {
        try {
          const response = await fetch(`localhost:8000/api/user/${id}`, {
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
      const response = await fetch('localhost:8000/api/events', {
        method: 'GET'
      });
      this.events = await response.json();
    },
    async fetchLocations() {
      const response = await fetch('localhost:8000/api/locations', {
        method: 'GET'
      });
      this.locations = await response.json();
    },
    async fetchCategories() {
      const response = await fetch('localhost:8000/api/categories', {
        method: 'GET'
      });
      this.categories = await response.json();
    },
    async fetchAllData(id: string) {
      await this.fetchUser(id);
      await this.fetchEvents();
      await this.fetchLocations();
      await this.fetchCategories();
    },
    //=============================================================//
    async fetchEventByGuy(): Promise<eventInfo[]> {
      const response = await fetch(`localhost:8000/api/events/query?participant=${this.user.id}&limit=10`, {
        method: 'GET'
      });
      return await response.json();
    }
  }
});
