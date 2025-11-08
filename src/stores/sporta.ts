import { defineStore } from 'pinia';
import { useConnectionMessage } from '@/composables/useConnectionMessage';

export class eventStruct {
  id!: number;
  title!: string;
  organizer!: string;
  participants!: string[];
  category!: string[];
  date!: number; // Unix timestamp
  location!: string;
  description!: string[]; //short then long
  image!: string;
}

export class participantsStruct {
  id!: number;
  exp!: number;
  subevents!: number[];
  subCat!: string[];
}

export class categoryStruct {
  id!: number;
  name!: string;
  description!: string;
  img!: string;
  isActive!: boolean;
}
export const useSportaStore = defineStore('sporta', {
  state: () => ({
    events: [] as eventStruct[],
    categories: [] as categoryStruct[],
    useMockData: true // Switch to control data source
  }),

  actions: {
    async fetchEvents() {
      try {
        if (this.useMockData) {
          // Use mock data
          const response = await fetch('/mock/sporta/events.json');
          if (!response.ok) {
            throw new Error(`Failed to load mock data! status: ${response.status}`);
          }
          this.events = await response.json();
        } else {
          // Use real API
          const response = await fetch('/api/events');
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          this.events = await response.json();
        }
      } catch (error) {
        console.error('Failed to fetch events:', error);
        // Fallback to empty array if both mock and API fail
        this.events = [];
      }
    },
    async fetchCategories() {
      try {
        if (this.useMockData) {
          // Use mock data
          const response = await fetch('/mock/sporta/categories.json');
          if (!response.ok) {
            throw new Error(`Failed to load mock categories! status: ${response.status}`);
          }
          this.categories = await response.json();
        } else {
          // Use real API
          const response = await fetch('/api/categories');
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          this.categories = await response.json();
        }
      } catch (error) {
        console.error('Failed to fetch categories:', error);
        // Fallback to empty array if both mock and API fail
        this.categories = [];
      }
    },
    async fetchAll() {
      // Convenience method to fetch both events and categories
      await Promise.all([
        this.fetchEvents(),
        this.fetchCategories()
      ]);
    },
    async subEvent(eventId: number, user: participantsStruct) {
      try {
        const response = await fetch(`/api/events/${eventId}/sub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Subscription failed:', error);
      }
    },
    async unSubEvent(eventId: number, user: participantsStruct) {
      try {
        const response = await fetch(`/api/events/${eventId}/unsub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Unsubscription failed:', error);
      }
    },
        async subCat(eventId: number, user: participantsStruct) {
      try {
        const response = await fetch(`/api/events/${eventId}/sub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Subscription failed:', error);
      }
    },
    async unSubCat(eventId: number, user: participantsStruct) {
      try {
        const response = await fetch(`/api/events/${eventId}/unsub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Unsubscription failed:', error);
      }
    },
  },

  getters: {
    eventsByCategory: (state) => {
      return (categories: string | string[]) => {
        const categoryArray = Array.isArray(categories) ? categories : [categories];
        return state.events.filter((event: eventStruct) =>
          categoryArray.some((category) =>
            event.category.some((cat: string) => cat.toLowerCase().includes(category.toLowerCase()))
          )
        );
      };
    },
    upcomingEvents: (state) => {
      const now = Date.now() / 1000; // Convert current time to Unix timestamp
      return state.events
        .filter((event: eventStruct) => event.date >= now)
        .sort((a: eventStruct, b: eventStruct) => a.date - b.date);
    },
    getMyEvents: (state) => {
      // This should return events where the current user is a participant
      // For now, returning all events - you can modify the logic as needed
      return state.events;
    },
    getMySubCats: (state) => {
      // For testing: return first 2 active categories 
      return state.categories.filter((cat: categoryStruct) => cat.isActive).slice(0, 2);
    },
    activeCategories: (state) => {
      return state.categories.filter((cat: categoryStruct) => cat.isActive);
    },
    allCategories: (state) => {
      return state.categories;
    }
  }
});
