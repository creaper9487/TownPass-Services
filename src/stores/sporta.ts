import { defineStore } from 'pinia';
import { useConnectionMessage } from '@/composables/useConnectionMessage';
import { useHandleConnectionData } from '@/composables/useHandleConnectionData';

// ============================================================================
// Types & Interfaces
// ============================================================================

export class eventStruct {
  id!: number;
  title!: string;
  organizer!: string;
  participants!: string[];
  category!: string[];
  date!: number; // Unix timestamp
  location!: string;
  description!: string[]; // short then long
  image!: string;
}

export class participantsStruct {
  id!: string;
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

// ============================================================================
// Store Definition
// ============================================================================

export const useSportaStore = defineStore('sporta', {
  // ==========================================================================
  // State
  // ==========================================================================
  state: () => ({
    events: [] as eventStruct[],
    categories: [] as categoryStruct[],
    useMockData: true, // Switch to control data source
    userdata: {} as participantsStruct,
    userInfo: null as any // Store for user info from connection
  }),

  // ==========================================================================
  // Actions
  // ==========================================================================
  actions: {
    // ------------------------------------------------------------------------
    // Data Fetching
    // ------------------------------------------------------------------------
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
          const response = await fetch('http://localhost:8000/api/events/');
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
          const response = await fetch('/mock/sports/categories.json');
          if (!response.ok) {
            throw new Error(`Failed to load mock categories! status: ${response.status}`);
          }
          this.categories = await response.json();
        } else {
          // Use real API
          const response = await fetch('http://localhost:8000/api/events/categories');
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

    async fetchUserInfo(userId: string) {
      try {
        const response = await fetch(`/api/user/${userId}`);
        if (!response.ok) {
          const errorMessage = `HTTP error! status: ${response.status}`;
          console.error(
            'Failed to fetch user info:',
            errorMessage,
            'Status Code:',
            response.status
          );
        }
        const data = await response.json();
        this.userdata.exp = data?.exp;
        this.userdata.subevents = data?.subevents;
        this.userdata.subCat = data?.subCat;
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        const response = await fetch(`/api/user/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: userId, exp: 0, subevents: [], subCat: [] })
        }).catch(error => {console.error('Failed to create user data:', error);});
      }
    },

    async fetchAll() {
      useConnectionMessage('userinfo', null);
      
      const handleUserInfoResponse = (event: { data: string }) => {
        try {
          console.log('Received user info response:', event.data);
          const result = JSON.parse(event.data);
          if (result.name === 'userinfo') {
            this.userInfo = result.data;
            console.log('User info received:', result.data);
            // Extract user ID and update userdata
            if (result.data?.id) {
              this.userdata.id = result.data.id;
              console.log('User ID set:', result.data.id);
            }
          }
        } catch (error) {
          console.error('Error parsing user info:', error);
        }
      };

      // Set up the message handler
      useHandleConnectionData(handleUserInfoResponse);
      
      // Wait a bit for the userinfo response to arrive
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Fetch both events and categories
      await Promise.all([
        this.fetchEvents(),
        this.fetchCategories(),
        this.fetchUserInfo(this.userdata?.id)
      ]);
    },

    // ------------------------------------------------------------------------
    // Event Subscriptions
    // ------------------------------------------------------------------------
    async subEvent(eventId: number, user: participantsStruct) {
      try {
        const response = await fetch(`http://localhost:8000/api/events/${eventId}/sub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Subscription failed:', error);
      }

      this.userdata.subevents.push(eventId);

      try {
        const response = await fetch(`/api/user/${user.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.userdata)
        });
      } catch (error) {
        console.error('Failed to update user data:', error);
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

      // Remove eventId from user's subscribed events
      const eventIndex = this.userdata.subevents.indexOf(eventId);
      if (eventIndex > -1) {
        this.userdata.subevents.splice(eventIndex, 1);
      }

      try {
        const response = await fetch(`/api/user/${user.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.userdata)
        });
      } catch (error) {
        console.error('Failed to update user data:', error);
      }
    },

    // ------------------------------------------------------------------------
    // Category Subscriptions
    // ------------------------------------------------------------------------
    async subCat(categoryId: number, user: participantsStruct) {
      try {
        const response = await fetch(`http://localhost:8000/api/categories/${categoryId}/sub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Category subscription failed:', error);
      }

      // Add categoryId to user's subscribed categories (assuming we store category IDs as strings)
      const category = this.categories.find((cat) => cat.id === categoryId);
      if (category && !this.userdata.subCat.includes(category.name)) {
        this.userdata.subCat.push(category.name);
      }

      try {
        const response = await fetch(`/api/user/${user.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.userdata)
        });
      } catch (error) {
        console.error('Failed to update user data:', error);
      }
    },

    async unSubCat(categoryId: number, user: participantsStruct) {
      try {
        const response = await fetch(`localhost:8000/api/categories/${categoryId}/unsub`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user.id)
        });
      } catch (error) {
        console.error('Category unsubscription failed:', error);
      }

      // Remove category from user's subscribed categories
      const category = this.categories.find((cat) => cat.id === categoryId);
      if (category) {
        const categoryIndex = this.userdata.subCat.indexOf(category.name);
        if (categoryIndex > -1) {
          this.userdata.subCat.splice(categoryIndex, 1);
        }
      }

      try {
        const response = await fetch(`/api/user/${user.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.userdata)
        });
      } catch (error) {
        console.error('Failed to update user data:', error);
      }
    }
  },

  // ==========================================================================
  // Getters
  // ==========================================================================
  getters: {
    // ------------------------------------------------------------------------
    // Event Getters
    // ------------------------------------------------------------------------
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

    // ------------------------------------------------------------------------
    // Category Getters
    // ------------------------------------------------------------------------
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
