import { Agent, run } from '@openai/agents';

// Agent to plan the best schedule based on real calendar availability
export const schedulePlannerAgent = new Agent({
  name: 'Schedule Planner',
  instructions: `
    You are an intelligent scheduling assistant. Your job is to:
    1. Analyze the user's request and real calendar availability
    2. Suggest the best time slot for the event
    3. Consider conflicts, preferences, and optimal timing
    4. Return structured scheduling information
    
    Return your response in this exact JSON format:
    {
      "suggestedTime": "HH:MM",
      "duration": "60" (in minutes),
      "title": "event title",
      "description": "event description",
      "reasoning": "explanation of why this time was chosen",
      "conflicts": [],
      "alternativeTimes": ["HH:MM", "HH:MM"]
    }
    
    Consider:
    - User's preferred time if specified
    - Available time slots from calendar
    - Duration of the event (default to 60 minutes)
    - Conflicts with existing events
    - Business hours (9 AM - 6 PM)
    - Optimal timing (avoid very early/late times unless requested)
    
    Examples:
    - If user wants "meeting at 2pm" but 2pm is busy, suggest next available slot
    - If no specific time given, suggest the first available slot in business hours
    - If all slots are busy, suggest alternative times or next available day
  `,
});

export async function planSchedule(userRequest, calendarData, dateInfo) {
  try {
    const prompt = `
User Request: "${userRequest}"
Extracted Date Info: ${JSON.stringify(dateInfo, null, 2)}
Calendar Data for ${calendarData.date}: ${JSON.stringify(calendarData, null, 2)}

Please analyze this information and suggest the best time to schedule the event.
Consider the user's preferences, available time slots, and any conflicts.
`;

    const result = await run(schedulePlannerAgent, prompt);
    const scheduleData = JSON.parse(result.finalOutput);
    return scheduleData;
  } catch (error) {
    console.error('Error planning schedule:', error);
    // Fallback to simple logic
    return generateFallbackSchedule(calendarData, dateInfo);
  }
}

// Fallback schedule generation if LLM fails
function generateFallbackSchedule(calendarData, dateInfo) {
  const availableSlots = calendarData.availableSlots || [];
  const events = calendarData.events || [];
  
  // Find first available slot
  let suggestedTime = '10:00'; // Default
  let reasoning = 'Default time slot selected';
  
  if (availableSlots.length > 0) {
    const firstSlot = availableSlots[0];
    suggestedTime = firstSlot.start;
    reasoning = `Selected first available slot: ${firstSlot.start}-${firstSlot.end}`;
  }
  
  // Check for conflicts with requested time
  const conflicts = [];
  if (dateInfo.time) {
    const requestedTime = dateInfo.time;
    const isConflict = events.some(event => {
      const eventStart = event.start;
      const eventEnd = event.end;
      return requestedTime >= eventStart && requestedTime < eventEnd;
    });
    
    if (isConflict) {
      conflicts.push(`Requested time ${requestedTime} conflicts with existing event`);
    } else {
      suggestedTime = requestedTime;
      reasoning = `User's preferred time ${requestedTime} is available`;
    }
  }
  
  return {
    suggestedTime: suggestedTime,
    duration: '60',
    title: dateInfo.title || 'Scheduled Event',
    description: dateInfo.description || null,
    reasoning: reasoning,
    conflicts: conflicts,
    alternativeTimes: availableSlots.slice(1, 3).map(slot => slot.start)
  };
}

// Function to validate if a suggested time is actually available
export function validateSuggestedTime(scheduleData, calendarData) {
  const suggestedTime = scheduleData.suggestedTime;
  const duration = parseInt(scheduleData.duration) || 60;
  
  // Check if the suggested time conflicts with existing events
  const conflicts = calendarData.events.filter(event => {
    const eventStart = event.start;
    const eventEnd = event.end;
    const suggestedEnd = addMinutes(suggestedTime, duration);
    
    return timeRangesOverlap(suggestedTime, suggestedEnd, eventStart, eventEnd);
  });
  
  if (conflicts.length > 0) {
    return {
      isValid: false,
      conflicts: conflicts,
      message: `Suggested time conflicts with: ${conflicts.map(e => e.title).join(', ')}`
    };
  }
  
  return {
    isValid: true,
    conflicts: [],
    message: 'Suggested time is available'
  };
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