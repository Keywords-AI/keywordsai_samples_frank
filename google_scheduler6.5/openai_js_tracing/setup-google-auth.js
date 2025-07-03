import dotenv from 'dotenv';
import { authenticate, hasValidCredentials } from './googleAuth.js';

dotenv.config();

async function setupGoogleAuth() {
  console.log('🔧 Google Calendar OAuth2 Setup\n');
  console.log('=' .repeat(60));
  
  // Check if environment variables are set
  if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET) {
    console.log('❌ Missing Google OAuth2 credentials in .env file');
    console.log('\n📋 Please add the following to your .env file:');
    console.log('GOOGLE_CLIENT_ID=your_client_id_here');
    console.log('GOOGLE_CLIENT_SECRET=your_client_secret_here');
    console.log('GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback');
    console.log('CALENDAR_ID=your_email@gmail.com');
    console.log('\n🔗 Get these from: https://console.cloud.google.com/');
    return;
  }
  
  console.log('✅ Environment variables found');
  console.log(`Client ID: ${process.env.GOOGLE_CLIENT_ID.substring(0, 20)}...`);
  console.log(`Calendar ID: ${process.env.CALENDAR_ID || 'primary'}`);
  
  // Check if already authenticated
  if (hasValidCredentials()) {
    console.log('\n✅ Already authenticated with Google Calendar');
    console.log('You can now run calendar tests with real data');
    return;
  }
  
  console.log('\n🔐 Starting authentication process...');
  
  try {
    await authenticate();
    console.log('\n🎉 Setup complete! You can now access your Google Calendar.');
    console.log('\n📝 Next steps:');
    console.log('1. Run: node test-calendar-checker.js');
    console.log('2. Or run the full workflow: node main.js');
  } catch (error) {
    console.error('\n❌ Setup failed:', error.message);
    console.log('\n💡 Troubleshooting:');
    console.log('1. Make sure your OAuth2 credentials are correct');
    console.log('2. Check that Google Calendar API is enabled');
    console.log('3. Verify the redirect URI matches your .env file');
  }
}

// Run the setup
setupGoogleAuth().catch(console.error); 