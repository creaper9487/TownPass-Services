import { useConnectionMessage } from '@/composables/useConnectionMessage';
import { defineStore } from 'pinia';

export class userInfo {
  userID: string;
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
    user: {
      userID:"7f3562f4-bb3f-4ec7-89b9-da3b4b5ff250"
    } as userInfo,
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
          const response = await fetch(`http://localhost:8000/api/user/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              "user_id": id
            })
          });
          this.user = await response.json();
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
        const rawEvents = await response.json();
        
        // Transform the data to match frontend design
        this.events = rawEvents.map((event: any) => ({
          id: event._id,
          title: event.title,
          organizer: event.organizer,
          participants: event.participants,
          category: event.category,
          location: event.location,
          description: Array.isArray(event.description) ? event.description.join('\n') : event.description,
          image: event.image,
          starttime: event.start_time,
          endtime: event.end_time
        }));
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
      // Fetch all data including events
      await this.fetchUser(id);
      await this.fetchEvents();
      await this.fetchLocations();
      await this.fetchCategories();
      console.log(this.user);
      this.userEvent = await this.fetchEventByGuy();
    },
    //=============================================================//
    async fetchEventByGuy(): Promise<eventInfo[]> {
      try {
        const response = await fetch(`http://localhost:8000/api/events/query?participant=${this.user.userID}&limit=10`, {
          method: 'GET'
        });
        const rawEvents = await response.json();
        
        // Transform the data to match frontend design
        return rawEvents.map((event: any) => ({
          id: event._id,
          title: event.title,
          organizer: event.organizer,
          participants: event.participants,
          category: event.category,
          location: event.location,
          description: Array.isArray(event.description) ? event.description.join('\n') : event.description,
          image: event.image,
          starttime: event.start_time,
          endtime: event.end_time
        }));
      } catch (error) {
        // Using mock data for now
        const { fetchEvents } = await import('@/utils/eventsmock.js');
        const mockEvents = await fetchEvents();
        return mockEvents;
      }
    },
    async SubmitEvent(payload: eventInfo) {
      await fetch('http://localhost:8000/api/events/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    },
    async subEvent(eid: string) {
      try {
        const response = await fetch(`http://localhost:8000/api/events/${eid}/sub`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            "userID": this.user.userID
          })
        });
        
        if (response.ok) {
          // Update local state to reflect the subscription
          const eventIndex = this.events.findIndex(event => event.id === eid);
          if (eventIndex !== -1 && !this.events[eventIndex].participants.includes(this.user.userID)) {
            this.events[eventIndex].participants.push(this.user.userID);
          }
        }
      } catch (error) {
        console.error('Error subscribing to event:', error);
        throw error;
      }
    },
    async unsubEvent(eid: string) {
      try {
        const response = await fetch(`http://localhost:8000/api/events/${eid}/unsub`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            "userID": this.user.userID
          })
        });
        
        if (response.ok) {
          // Update local state to reflect the unsubscription
          const eventIndex = this.events.findIndex(event => event.id === eid);
          if (eventIndex !== -1) {
            const participantIndex = this.events[eventIndex].participants.indexOf(this.user.userID);
            if (participantIndex > -1) {
              this.events[eventIndex].participants.splice(participantIndex, 1);
            }
          }
        }
      } catch (error) {
        console.error('Error unsubscribing from event:', error);
        throw error;
      }
    },
    async submitLocation(payload: { name: string; coordinates: [number, number] }) {
      try {
        const response = await fetch("http://localhost:8000/api/locations/", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to create location: ${response.statusText}`);
        }
        
        const newLocation = await response.json();
        
        // Update local state with the new location
        this.locations.push({
          id: newLocation._id,
          name: newLocation.name,
          coordinates: newLocation.coordinates,
          subscribers: newLocation.subscribers || []
        });
        
        return newLocation;
      } catch (error) {
        console.error('Error submitting location:', error);
        throw error;
      }
    },
    async subscribeLocation(locationId: string) {
      try {
        const response = await fetch(`http://localhost:8000/api/locations/${locationId}/sub`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            "userID": this.user.userID
          })
        });
        
        if (!response.ok) {
          throw new Error(`Failed to subscribe to location: ${response.statusText}`);
        }
        
        const updatedLocation = await response.json();
        
        // Update local state
        const locationIndex = this.locations.findIndex(loc => loc.id === locationId);
        if (locationIndex !== -1) {
          this.locations[locationIndex].subscribers = updatedLocation.subscribers || [];
        }
        
        return updatedLocation;
      } catch (error) {
        console.error('Error subscribing to location:', error);
        throw error;
      }
    },
    async unsubscribeLocation(locationId: string) {
      try {
        const response = await fetch(`http://localhost:8000/api/locations/${locationId}/unsub`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            "userID": this.user.userID
          })
        });
        
        if (!response.ok) {
          throw new Error(`Failed to unsubscribe from location: ${response.statusText}`);
        }
        
        const updatedLocation = await response.json();
        
        // Update local state
        const locationIndex = this.locations.findIndex(loc => loc.id === locationId);
        if (locationIndex !== -1) {
          this.locations[locationIndex].subscribers = updatedLocation.subscribers || [];
        }
        
        return updatedLocation;
      } catch (error) {
        console.error('Error unsubscribing from location:', error);
        throw error;
      }
    },
    async grabDecodelocation(id: string) {
      try{
        const response = await fetch(`http://localhost:8000/api/locations/${id}`, {});
        const data = await response.json();
        console.log(data, "AAAAAAAAAAAAAAAAA");
        return data.name;
      }catch(error){
        console.error('Error fetching location:', error);
        return id; // Fallback to ID if fetch fails
      }
    },
    async grabDecodecategory(id: string) {
      try{
        const response = await fetch(`http://localhost:8000/api/categories/${id}`, {});
        const data = await response.json();
        console.log(data, "BBBBBBBBBBBBBBBBB");
        return data.name;
      }catch(error){
        console.error('Error fetching category:', error);
        return id; // Fallback to ID if fetch fails
      }
    },
    async fetchOrgar(oid: string) {
      try{
        const response = await fetch(`http://localhost:8000/api/organizer-ratings/${oid}`, {});
        const data = await response.json();
        return data.average_rating;
      }catch(error){
        console.error('Error fetching organizer:', error);
        // return oid; // Fallback to ID if fetch fails
      }
    },
    async rateOrganizer(uid: string,oid:string, rating: number,eventid:string) {
      try{
        const response = await fetch(`http://localhost:8000/api/organizer-ratings/${oid}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            rater_id: uid,
            rating: rating,
            event_id: eventid,
            organizer_id: oid

          })
        });
        const data = await response.json();
        return data.average_rating;
      }catch(error){
        console.error('Error fetching organizer:', error);
        // return oid; // Fallback to ID if fetch fails
      }
    }
  }
});
