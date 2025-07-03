import { google } from 'googleapis';
import dotenv from 'dotenv';
import { getOAuth2Client, hasValidCredentials, refreshTokenIfNeeded } from './googleAuth.js';

dotenv.config();

// Initialize Google Calendar API
const calendar = google.calendar('v3');

// Mock calendar data for demo purposes
function getMockCalendarData(date) {
  const mockEvents = [
    { start: '09:00', end: '10:00', title: 'Morning Standup', description: 'Daily team sync' },
    { start: '14:00', end: '15:00', title: 'Team Meeting', description: 'Weekly planning' },
    { start: '16:00', end: '17:00', title: 'Code Review', description: 'Review pull requests' }
  ];
  
  return {
    date: date,
    events: mockEvents,
    availableSlots: [
      { start: '10:00', end: '14:00' },
      { start: '15:00', end: '16:00' },
      { start: '17:00', end: '18:00' }
    ],
    totalEvents: mockEvents.length,
    isBusy: mockEvents.length > 0
  };
}

// Real Google Calendar integration
async function getRealCalendarData(date) {
  try {
    console.log(`Fetching real calendar data for ${date}...`);
    
    // Check if we have valid credentials
    if (!hasValidCredentials()) {
      throw new Error('No valid OAuth2 credentials. Please authenticate first.');
    }
    
    // Refresh token if needed
    await refreshTokenIfNeeded();
    
    const oauth2Client = getOAuth2Client();
    
    const response = await calendar.events.list({
      auth: oauth2Client,
      calendarId: process.env.CALENDAR_ID || 'primary',
      timeMin: new Date(date + 'T00:00:00Z').toISOString(),
      timeMax: new Date(date + 'T23:59:59Z').toISOString(),
      singleEvents: true,
      orderBy: 'startTime',
    });
    
    const events = response.data.items.map(event => ({
      start: event.start.dateTime ? new Date(event.start.dateTime).toTimeString().slice(0, 5) : '00:00',
      end: event.end.dateTime ? new Date(event.end.dateTime).toTimeString().slice(0, 5) : '23:59',
      title: event.summary || 'Untitled Event',
      description: event.description || null
    }));
    
    // Calculate available slots (simplified logic)
    const availableSlots = calculateAvailableSlots(events);
    
    return {
      date: date,
      events: events,
      availableSlots: availableSlots,
      totalEvents: events.length,
      isBusy: events.length > 0
    };
    
  } catch (error) {
    console.error('Error fetching real calendar data:', error);
    throw error;
  }
}

// Helper function to calculate available time slots
function calculateAvailableSlots(events) {
  const businessHours = { start: '09:00', end: '18:00' };
  const slots = [];
  
  // Simple algorithm: find gaps between events
  let currentTime = businessHours.start;
  
  events.forEach(event => {
    if (event.start > currentTime) {
      slots.push({ start: currentTime, end: event.start });
    }
    currentTime = event.end;
  });
  
  // Add final slot if there's time left
  if (currentTime < businessHours.end) {
    slots.push({ start: currentTime, end: businessHours.end });
  }
  
  return slots;
}

// Main function to check calendar availability
export async function checkCalendarAvailability(date, useRealAPI = true) {
  try {
    console.log(`Checking calendar availability for ${date}...`);
    
    if (useRealAPI && process.env.GOOGLE_CLIENT_ID) {
      return await getRealCalendarData(date);
    } else {
      console.log('Using mock calendar data for demo purposes');
      return getMockCalendarData(date);
    }
    
  } catch (error) {
    console.error('Error checking calendar:', error);
    // Fallback to mock data on error
    console.log('Falling back to mock data due to error');
    return getMockCalendarData(date);
  }
}

// Function to check if a specific time slot is available
export function isTimeSlotAvailable(calendarData, requestedTime, duration = 60) {
  if (!calendarData.events || calendarData.events.length === 0) {
    return true; // No events, so any time is available
  }
  
  const requestedStart = requestedTime;
  const requestedEnd = addMinutes(requestedStart, duration);
  
  // Check for conflicts with existing events
  for (const event of calendarData.events) {
    if (timeRangesOverlap(requestedStart, requestedEnd, event.start, event.end)) {
      return false;
    }
  }
  
  return true;
}

// Helper function to add minutes to time
function addMinutes(time, minutes) {
  const [hours, mins] = time.split(':').map(Number);
  const totalMinutes = hours * 60 + mins + parseInt(minutes);
  const newHours = Math.floor(totalMinutes / 60);
  const newMins = totalMinutes % 60;
  return `${newHours.toString().padStart(2, '0')}:${newMins.toString().padStart(2, '0')}`;
}

// Helper function to check if two time ranges overlap
function timeRangesOverlap(start1, end1, start2, end2) {
  return start1 < end2 && start2 < end1;
} 