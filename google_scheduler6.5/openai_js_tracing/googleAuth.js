import { google } from 'googleapis';
import dotenv from 'dotenv';
import http from 'http';
import url from 'url';
import fs from 'fs';
import path from 'path';

dotenv.config();

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.GOOGLE_REDIRECT_URI
);

// Token storage file
const TOKEN_FILE = path.join(process.cwd(), 'google-tokens.json');

// Scopes needed for Google Calendar
const SCOPES = [
  'https://www.googleapis.com/auth/calendar.readonly',
  'https://www.googleapis.com/auth/calendar.events'
];

// Load tokens from file
function loadTokens() {
  try {
    if (fs.existsSync(TOKEN_FILE)) {
      const tokens = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8'));
      oauth2Client.setCredentials(tokens);
      console.log('✅ Loaded saved OAuth2 tokens');
      return true;
    }
  } catch (error) {
    console.log('❌ Error loading saved tokens:', error.message);
  }
  return false;
}

// Save tokens to file
function saveTokens(tokens) {
  try {
    fs.writeFileSync(TOKEN_FILE, JSON.stringify(tokens, null, 2));
    console.log('✅ Saved OAuth2 tokens to file');
  } catch (error) {
    console.log('❌ Error saving tokens:', error.message);
  }
}

export function getAuthUrl() {
  return oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent'
  });
}

export function getTokensFromCode(code) {
  return oauth2Client.getToken(code);
}

export function setCredentials(tokens) {
  oauth2Client.setCredentials(tokens);
  saveTokens(tokens); // Save tokens when setting them
}

export function getOAuth2Client() {
  return oauth2Client;
}

// Simple server to handle OAuth callback
export function startAuthServer() {
  return new Promise((resolve, reject) => {
    const server = http.createServer(async (req, res) => {
      const queryObject = url.parse(req.url, true).query;
      
      if (queryObject.code) {
        try {
          const { tokens } = await getTokensFromCode(queryObject.code);
          setCredentials(tokens);
          
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body>
                <h1>Authentication Successful!</h1>
                <p>You can now close this window and return to your application.</p>
                <script>window.close();</script>
              </body>
            </html>
          `);
          
          server.close();
          resolve(tokens);
        } catch (error) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end(`<h1>Authentication Failed</h1><p>${error.message}</p>`);
          server.close();
          reject(error);
        }
      } else {
        res.writeHead(400, { 'Content-Type': 'text/html' });
        res.end('<h1>No authorization code received</h1>');
        server.close();
        reject(new Error('No authorization code received'));
      }
    });
    
    server.listen(3000, () => {
      console.log('Auth server listening on port 3000');
    });
  });
}

// Complete authentication flow
export async function authenticate() {
  try {
    console.log('🔐 Starting Google OAuth2 authentication...');
    
    // Try to load existing tokens first
    if (loadTokens() && hasValidCredentials()) {
      console.log('✅ Using existing OAuth2 tokens');
      return oauth2Client.credentials;
    }
    
    // Generate auth URL
    const authUrl = getAuthUrl();
    console.log('\n📋 Please visit this URL to authorize the application:');
    console.log(authUrl);
    console.log('\n⏳ Waiting for authorization...');
    
    // Start server to handle callback
    const tokens = await startAuthServer();
    
    console.log('✅ Authentication successful!');
    console.log('Access token received and stored.');
    
    return tokens;
  } catch (error) {
    console.error('❌ Authentication failed:', error.message);
    throw error;
  }
}

// Check if we have valid credentials
export function hasValidCredentials() {
  const credentials = oauth2Client.credentials;
  return credentials && credentials.access_token;
}

// Refresh token if needed
export async function refreshTokenIfNeeded() {
  try {
    const credentials = oauth2Client.credentials;
    if (credentials && credentials.refresh_token) {
      await oauth2Client.refreshAccessToken();
      console.log('✅ Access token refreshed');
      // Save the refreshed tokens
      saveTokens(oauth2Client.credentials);
    }
  } catch (error) {
    console.error('❌ Failed to refresh token:', error.message);
    throw error;
  }
}

// Initialize by loading saved tokens
loadTokens(); 