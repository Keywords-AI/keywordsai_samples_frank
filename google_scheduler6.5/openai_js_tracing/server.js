import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { extractDateInfo } from './dateExtractor.js';
import { checkCalendarAvailability } from './calendarChecker.js';
import { planSchedule } from './schedulePlanner.js';
import { createCalendarEvent } from './calendarScheduler.js';
import { generateResponse, formatResponse } from './responseGenerator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// Serve the HTML frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// API endpoint for scheduling
app.post('/api/schedule', async (req, res) => {
    try {
        const { request } = req.body;
        
        if (!request) {
            return res.status(400).json({ 
                error: 'Scheduling request is required' 
            });
        }

        console.log('🤖 Received scheduling request:', request);

        // Step 1: Extract date information
        console.log('🔍 Step 1: Extracting date information...');
        const dateInfo = await extractDateInfo(request);
        
        if (!dateInfo.hasScheduleRequest) {
            return res.status(400).json({ 
                error: 'No scheduling request detected. Please try something like "Schedule a meeting for tomorrow at 2pm"' 
            });
        }

        if (!dateInfo.date) {
            return res.status(400).json({ 
                error: 'Could not determine a specific date. Please specify a date like "tomorrow", "next Monday", or "2024-01-15"' 
            });
        }

        // Step 2: Check calendar availability
        console.log('📅 Step 2: Checking calendar availability...');
        const calendarData = await checkCalendarAvailability(dateInfo.date);

        // Step 3: Plan schedule using LLM
        console.log('🤖 Step 3: Planning schedule with LLM...');
        const scheduleData = await planSchedule(request, calendarData, dateInfo);

        // Step 4: Create calendar event
        console.log('📅 Step 4: Creating calendar event...');
        const eventResult = await createCalendarEvent(scheduleData, dateInfo);

        if (!eventResult.success) {
            return res.status(500).json({ 
                error: `Failed to create calendar event: ${eventResult.error}` 
            });
        }

        // Step 5: Generate user-friendly response
        console.log('🤖 Step 5: Generating user-friendly response...');
        const responseData = await generateResponse(request, scheduleData, dateInfo, eventResult);

        console.log('✅ Scheduling workflow completed successfully!');

        // Return the response
        res.json({
            success: true,
            response: responseData,
            eventId: eventResult.eventId,
            eventLink: eventResult.eventLink
        });

    } catch (error) {
        console.error('❌ Error in scheduling workflow:', error);
        res.status(500).json({ 
            error: `Internal server error: ${error.message}` 
        });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        service: 'AI Scheduling Assistant'
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 AI Scheduling Assistant server running on http://localhost:${PORT}`);
    console.log(`📋 Frontend: http://localhost:${PORT}`);
    console.log(`🔌 API: http://localhost:${PORT}/api/schedule`);
    console.log(`💚 Health: http://localhost:${PORT}/api/health`);
}); 