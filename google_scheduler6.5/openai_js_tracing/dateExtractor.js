import { Agent, run } from '@openai/agents';

// Agent to extract date information from user input
export const dateExtractorAgent = new Agent({
  name: 'Date Extractor',
  instructions: `
    You are a date extraction specialist. Your job is to:
    1. Parse user input to identify scheduling requests
    2. Extract the date and time information
    3. Return a structured response with the extracted information
    
    Return your response in this exact JSON format:
    {
      "hasScheduleRequest": true/false,
      "date": "YYYY-MM-DD" or null,
      "time": "HH:MM" or null,
      "title": "event title" or null,
      "description": "event description" or null
    }
    
    IMPORTANT DATE CALCULATION RULES:
    - Use the provided current date as reference
    - "tomorrow" = current date + 1 day
    - "next week" = current date + 7 days
    - "next Monday" = next Monday from current date
    - Always calculate relative dates based on the provided current date
    
    Examples:
    - Current date: 2025-06-22, "tomorrow" → "2025-06-23"
    - Current date: 2025-06-22, "next Monday" → "2025-06-30"
    - Current date: 2025-06-22, "next week" → "2025-06-29"
    
    Time conversion:
    - "2pm" → "14:00"
    - "10am" → "10:00"
    - "noon" → "12:00"
    - "midnight" → "00:00"
    
    Always use the provided current date and time as reference for relative dates.
  `,
});

function getCurrentDateTimeInfo() {
  const now = new Date();
  
  // Use local time instead of UTC for date calculations
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const date = `${year}-${month}-${day}`; // Local date YYYY-MM-DD
  
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const time = `${hours}:${minutes}`; // Local time HH:MM
  
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  
  // Calculate tomorrow's date in local time
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowYear = tomorrow.getFullYear();
  const tomorrowMonth = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const tomorrowDay = String(tomorrow.getDate()).padStart(2, '0');
  const tomorrowDate = `${tomorrowYear}-${tomorrowMonth}-${tomorrowDay}`;
  
  return { date, time, timeZone, tomorrowDate };
}

export async function extractDateInfo(userInput) {
  try {
    const { date, time, timeZone, tomorrowDate } = getCurrentDateTimeInfo();
    const context = `[Current date: ${date}, Current time: ${time}, Time zone: ${timeZone}, Tomorrow: ${tomorrowDate}]
User input: ${userInput}

Please extract scheduling information from the user input. Use the current date (${date}) as reference for calculating relative dates like "tomorrow" (${tomorrowDate}).`;
    
    const result = await run(dateExtractorAgent, context);
    const extractedData = JSON.parse(result.finalOutput);
    return extractedData;
  } catch (error) {
    console.error('Error extracting date info:', error);
    return {
      hasScheduleRequest: false,
      date: null,
      time: null,
      title: null,
      description: null
    };
  }
} 