import dotenv from 'dotenv';
import readline from 'readline';
import { extractDateInfo } from './dateExtractor.js';
import { checkCalendarAvailability } from './calendarChecker.js';
import { planSchedule } from './schedulePlanner.js';
import { createCalendarEvent, deleteCalendarEvent } from './calendarScheduler.js';
import { generateResponse, formatResponse } from './responseGenerator.js';

dotenv.config();

async function runSchedulingWorkflow(userInput) {
  console.log('🤖 Starting AI Scheduling Workflow...\n');
  console.log(`📝 User Request: "${userInput}"\n`);

  try {
    // Step 1: Extract date and scheduling information
    console.log('🔍 Step 1: Extracting date information...');
    const startTime1 = Date.now();
    const dateInfo = await extractDateInfo(userInput);
    const endTime1 = Date.now();
    
    console.log(`✅ Date Info: ${JSON.stringify(dateInfo)}`);
    console.log(`⏱️  Duration: ${endTime1 - startTime1}ms`);

    if (!dateInfo.hasScheduleRequest) {
      return "I don't see a scheduling request in your message. Please try something like 'Schedule a meeting for tomorrow at 2pm'.";
    }

    if (!dateInfo.date) {
      return "I couldn't determine a specific date from your request. Please specify a date like 'tomorrow', 'next Monday', or '2024-01-15'.";
    }

    // Step 2: Check calendar availability
    console.log('\n📅 Step 2: Checking calendar availability...');
    const startTime2 = Date.now();
    const calendarData = await checkCalendarAvailability(dateInfo.date);
    const endTime2 = Date.now();
    
    console.log(`✅ Calendar Data: ${JSON.stringify({
      date: calendarData.date,
      totalEvents: calendarData.totalEvents,
      events: calendarData.events.map(e => `${e.start}-${e.end}: ${e.title}`),
      availableSlots: calendarData.availableSlots.map(s => `${s.start}-${s.end}`)
    })}`);
    console.log(`⏱️  Duration: ${endTime2 - startTime2}ms`);

    // Step 3: Plan the schedule using LLM
    console.log('\n🤖 Step 3: Planning schedule with LLM...');
    const startTime3 = Date.now();
    const scheduleData = await planSchedule(userInput, calendarData, dateInfo);
    const endTime3 = Date.now();
    
    console.log(`✅ LLM Schedule Plan:`);
    console.log(`   - Suggested Time: ${scheduleData.suggestedTime}`);
    console.log(`   - Duration: ${scheduleData.duration} minutes`);
    console.log(`   - Title: ${scheduleData.title}`);
    console.log(`   - Reasoning: ${scheduleData.reasoning}`);
    console.log(`⏱️  Duration: ${endTime3 - startTime3}ms`);

    // Step 4: Create calendar event
    console.log('\n📅 Step 4: Creating calendar event...');
    const startTime4 = Date.now();
    const eventResult = await createCalendarEvent(scheduleData, dateInfo);
    const endTime4 = Date.now();
    
    if (eventResult.success) {
      console.log('✅ Event created successfully!');
      console.log(`   - Event ID: ${eventResult.eventId}`);
      console.log(`   - Event Link: ${eventResult.eventLink}`);
    } else {
      console.log('❌ Event creation failed:', eventResult.error);
    }
    console.log(`⏱️  Duration: ${endTime4 - startTime4}ms`);

    // Step 5: Generate user-friendly response
    console.log('\n🤖 Step 5: Generating user-friendly response...');
    const startTime5 = Date.now();
    const responseData = await generateResponse(userInput, scheduleData, dateInfo, eventResult);
    const endTime5 = Date.now();
    
    console.log(`⏱️  Duration: ${endTime5 - startTime5}ms`);
    
    // Display the final response
    console.log('\n📤 Final Response:');
    const formattedResponse = formatResponse(responseData, 'console');
    console.log(formattedResponse);
    
    // Performance summary
    const totalDuration = endTime5 - startTime1;
    console.log('\n📊 Performance Summary:');
    console.log(`- Total Duration: ${totalDuration}ms`);
    console.log(`- Step 1 (Date Extraction): ${endTime1 - startTime1}ms`);
    console.log(`- Step 2 (Calendar Check): ${endTime2 - startTime2}ms`);
    console.log(`- Step 3 (Schedule Planning): ${endTime3 - startTime3}ms`);
    console.log(`- Step 4 (Event Creation): ${endTime4 - startTime4}ms`);
    console.log(`- Step 5 (Response Generation): ${endTime5 - startTime5}ms`);
    
    console.log('\n🎉 Workflow completed successfully!');
    
    return {
      success: true,
      eventResult: eventResult,
      responseData: responseData,
      performance: {
        totalDuration: totalDuration,
        step1: endTime1 - startTime1,
        step2: endTime2 - startTime2,
        step3: endTime3 - startTime3,
        step4: endTime4 - startTime4,
        step5: endTime5 - startTime5
      }
    };

  } catch (error) {
    console.error('❌ Error in scheduling workflow:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Interactive mode with readline
async function startInteractiveMode() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log('🚀 AI Scheduling Assistant - Interactive Mode\n');
  console.log('📋 Available Commands:');
  console.log('• Type your scheduling request (e.g., "Schedule a meeting for tomorrow at 2pm")');
  console.log('• Type "demo" to run example requests');
  console.log('• Type "quit" or "exit" to close the application');
  console.log('=' .repeat(60));

  const askQuestion = () => {
    rl.question('\n🤖 Enter your scheduling request: ', async (input) => {
      const trimmedInput = input.trim().toLowerCase();
      
      if (trimmedInput === 'quit' || trimmedInput === 'exit') {
        console.log('\n👋 Thanks for using the AI Scheduling Assistant! Goodbye!');
        rl.close();
        return;
      }
      
      if (trimmedInput === 'demo') {
        await runDemoMode();
        askQuestion();
        return;
      }
      
      if (trimmedInput === '') {
        console.log('Please enter a scheduling request or type "demo" for examples.');
        askQuestion();
        return;
      }
      
      console.log('\n' + '=' .repeat(60));
      const result = await runSchedulingWorkflow(input);
      
      if (result.success) {
        console.log('\n✅ Request completed successfully!');
      } else {
        console.log(`\n❌ Request failed: ${result.error}`);
      }
      
      console.log('=' .repeat(60));
      askQuestion();
    });
  };

  askQuestion();
}

// Demo mode with example requests
async function runDemoMode() {
  console.log('\n🧪 Running Demo Mode...\n');
  
  const demoInputs = [
    "Schedule a team meeting for tomorrow at 10am",
    "Schedule lunch for today at 12:30pm",
    "Schedule a doctor appointment for next week"
  ];

  for (const input of demoInputs) {
    console.log(`\n📝 Demo Request: "${input}"`);
    console.log('-'.repeat(50));
    
    const result = await runSchedulingWorkflow(input);
    
    if (result.success) {
      console.log('\n✅ Demo completed successfully!');
    } else {
      console.log(`\n❌ Demo failed: ${result.error}`);
    }
    
    console.log('=' .repeat(60));
    
    // Wait a moment between demos
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  console.log('\n🎉 Demo mode completed!');
}

// Main execution
async function main() {
  console.log('🚀 AI Scheduling Assistant with OpenAI Agents\n');
  console.log('📋 This system can:');
  console.log('• Understand natural language scheduling requests');
  console.log('• Check your real Google Calendar availability');
  console.log('• Use AI to suggest optimal times and avoid conflicts');
  console.log('• Create real events in your Google Calendar');
  console.log('• Provide friendly, helpful responses with next steps');
  console.log('=' .repeat(60));

  // Check if environment is properly configured
  if (!process.env.OPENAI_API_KEY) {
    console.error('❌ Error: OPENAI_API_KEY not found in environment variables');
    console.log('Please make sure your .env file is properly configured.');
    return;
  }

  if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET) {
    console.error('❌ Error: Google OAuth2 credentials not found');
    console.log('Please make sure your .env file includes Google OAuth2 credentials.');
    return;
  }

  console.log('✅ Environment configuration verified');
  console.log('✅ Starting interactive mode...\n');

  // Start interactive mode
  await startInteractiveMode();
}

// Run the application
main().catch(console.error); 