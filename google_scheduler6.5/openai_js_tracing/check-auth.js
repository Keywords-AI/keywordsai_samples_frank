import dotenv from 'dotenv';
import { hasValidCredentials, getOAuth2Client } from './googleAuth.js';
import { checkCalendarAvailability } from './calendarChecker.js';

dotenv.config();

async function checkAuthentication() {
  console.log('🔍 Checking Google Calendar Authentication Status\n');
  console.log('=' .repeat(60));
  
  // Check if we have valid credentials
  const hasAuth = hasValidCredentials();
  console.log(`OAuth2 Credentials: ${hasAuth ? '✅ Valid' : '❌ Missing'}`);
  
  if (hasAuth) {
    const oauth2Client = getOAuth2Client();
    console.log('Access Token:', oauth2Client.credentials.access_token ? '✅ Present' : '❌ Missing');
    console.log('Refresh Token:', oauth2Client.credentials.refresh_token ? '✅ Present' : '❌ Missing');
    
    // Test real calendar access
    console.log('\n📅 Testing Real Calendar Access...');
    try {
      const today = new Date().toISOString().slice(0, 10);
      const calendarData = await checkCalendarAvailability(today, true);
      
      console.log('✅ Real Calendar Access: SUCCESS');
      console.log(`Date: ${calendarData.date}`);
      console.log(`Total Events: ${calendarData.totalEvents}`);
      console.log('Events:', calendarData.events.map(e => `${e.start}-${e.end}: ${e.title}`));
      console.log('Available Slots:', calendarData.availableSlots.map(s => `${s.start}-${s.end}`));
      
    } catch (error) {
      console.log('❌ Real Calendar Access: FAILED');
      console.log('Error:', error.message);
    }
  } else {
    console.log('\n📋 To get real calendar data, run:');
    console.log('node setup-google-auth.js');
  }
  
  console.log('\n' + '=' .repeat(60));
}

checkAuthentication().catch(console.error); 