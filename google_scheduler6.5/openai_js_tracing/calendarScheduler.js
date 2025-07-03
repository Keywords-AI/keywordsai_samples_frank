import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';

// Load OAuth2 tokens
function loadTokens() {
  try {
    const tokenPath = path.join(process.cwd(), 'google-tokens.json');
    if (fs.existsSync(tokenPath)) {
      const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
      return tokens;
    }
  } catch (error) {
    console.error('Error loading tokens:', error);
  }
  return null;
}

// Create Google Calendar API client
function createCalendarClient() {
  const tokens = loadTokens();
  if (!tokens) {
    throw new Error('No OAuth2 tokens found. Please run setup-google-auth.js first.');
  }

  const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
  );

  oauth2Client.setCredentials(tokens);
  return google.calendar({ version: 'v3', auth: oauth2Client });
}

// Create a calendar event
export async function createCalendarEvent(scheduleData, dateInfo) {
  try {
    console.log('📅 Creating calendar event...');
    
    const calendar = createCalendarClient();
    
    // Get user's timezone
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    
    // Parse the date and time
    const eventDate = dateInfo.date; // YYYY-MM-DD format
    const eventTime = scheduleData.suggestedTime; // HH:MM format
    
    // Create start and end times
    const startDateTime = `${eventDate}T${eventTime}:00`;
    const endDateTime = addMinutesToDateTime(startDateTime, parseInt(scheduleData.duration) || 60);
    
    // Prepare event details
    const event = {
      summary: scheduleData.title || 'Scheduled Event',
      description: scheduleData.description || `Event scheduled by AI assistant. Reasoning: ${scheduleData.reasoning}`,
      start: {
        dateTime: startDateTime,
        timeZone: userTimeZone, // Use user's actual timezone
      },
      end: {
        dateTime: endDateTime,
        timeZone: userTimeZone, // Use user's actual timezone
      },
      reminders: {
        useDefault: false,
        overrides: [
          {
            method: 'email',
            minutes: 24 * 60, // 24 hours before
          },
          {
            method: 'popup',
            minutes: 15, // 15 minutes before
          },
        ],
      },
    };
    
    console.log(`Creating event: ${event.summary}`);
    console.log(`Start: ${startDateTime} (${userTimeZone})`);
    console.log(`End: ${endDateTime} (${userTimeZone})`);
    console.log(`Duration: ${scheduleData.duration} minutes`);
    console.log(`Timezone: ${userTimeZone}`);
    
    // Create the event
    const response = await calendar.events.insert({
      calendarId: 'primary',
      resource: event,
    });
    
    const createdEvent = response.data;
    
    console.log('✅ Event created successfully!');
    console.log(`Event ID: ${createdEvent.id}`);
    console.log(`Event Link: ${createdEvent.htmlLink}`);
    
    return {
      success: true,
      eventId: createdEvent.id,
      eventLink: createdEvent.htmlLink,
      event: createdEvent,
      scheduleData: scheduleData,
      dateInfo: dateInfo
    };
    
  } catch (error) {
    console.error('❌ Error creating calendar event:', error.message);
    
    if (error.code === 401) {
      console.error('Authentication error. Please refresh your OAuth2 tokens.');
    } else if (error.code === 403) {
      console.error('Permission error. Please check your Google Calendar permissions.');
    }
    
    return {
      success: false,
      error: error.message,
      scheduleData: scheduleData,
      dateInfo: dateInfo
    };
  }
}

// Helper function to add minutes to a datetime string
function addMinutesToDateTime(dateTimeString, minutes) {
  const date = new Date(dateTimeString);
  date.setMinutes(date.getMinutes() + minutes);
  
  // Format the result in the same timezone as the input
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const mins = String(date.getMinutes()).padStart(2, '0');
  const secs = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${mins}:${secs}`;
}

// Function to delete a calendar event (for testing/cleanup)
export async function deleteCalendarEvent(eventId) {
  try {
    console.log(`🗑️  Deleting calendar event: ${eventId}`);
    
    const calendar = createCalendarClient();
    
    await calendar.events.delete({
      calendarId: 'primary',
      eventId: eventId,
    });
    
    console.log('✅ Event deleted successfully!');
    return { success: true };
    
  } catch (error) {
    console.error('❌ Error deleting calendar event:', error.message);
    return { success: false, error: error.message };
  }
}

// Function to list recent events (for verification)
export async function listRecentEvents(maxResults = 10) {
  try {
    console.log('📋 Listing recent calendar events...');
    
    const calendar = createCalendarClient();
    
    const response = await calendar.events.list({
      calendarId: 'primary',
      timeMin: new Date().toISOString(),
      maxResults: maxResults,
      singleEvents: true,
      orderBy: 'startTime',
    });
    
    const events = response.data.items || [];
    
    console.log(`Found ${events.length} upcoming events:`);
    events.forEach((event, index) => {
      const start = event.start.dateTime || event.start.date;
      const end = event.end.dateTime || event.end.date;
      console.log(`${index + 1}. ${event.summary} (${start} to ${end})`);
    });
    
    return events;
    
  } catch (error) {
    console.error('❌ Error listing calendar events:', error.message);
    return [];
  }
}

// Function to check if an event already exists at a specific time
export async function checkEventExists(dateTime, duration = 60) {
  try {
    const calendar = createCalendarClient();
    
    const startTime = new Date(dateTime);
    const endTime = new Date(startTime.getTime() + duration * 60000);
    
    const response = await calendar.events.list({
      calendarId: 'primary',
      timeMin: startTime.toISOString(),
      timeMax: endTime.toISOString(),
      singleEvents: true,
    });
    
    const events = response.data.items || [];
    return events.length > 0;
    
  } catch (error) {
    console.error('❌ Error checking event existence:', error.message);
    return false;
  }
} 