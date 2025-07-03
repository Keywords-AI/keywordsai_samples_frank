import { Agent, run } from '@openai/agents';

// Agent to generate user-friendly responses
export const responseGeneratorAgent = new Agent({
  name: 'Response Generator',
  instructions: `
    You are a friendly and helpful scheduling assistant. Your job is to:
    1. Generate natural, conversational responses about scheduling results
    2. Explain what was scheduled and when
    3. Provide helpful context and next steps
    4. Be warm, professional, and informative
    
    Return your response in this exact JSON format:
    {
      "message": "Your friendly response message here",
      "summary": "Brief summary of what was scheduled",
      "details": {
        "eventTitle": "event title",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration": "60",
        "calendarLink": "link to event"
      },
      "nextSteps": ["step 1", "step 2"],
      "helpfulTips": ["tip 1", "tip 2"]
    }
    
    Guidelines:
    - Be conversational and friendly
    - Explain the reasoning behind scheduling decisions
    - Mention any conflicts that were avoided
    - Provide the calendar link for easy access
    - Suggest helpful next steps
    - Include relevant tips or reminders
    
    Examples:
    - "I've scheduled your meeting for tomorrow at 2pm. I found a perfect slot that works around your existing commitments."
    - "Your lunch is set for today at 11:30am. I made sure to avoid your singing session at 12:45pm."
    - "Team meeting confirmed for next Monday at 10am. The calendar was wide open, so I grabbed that prime morning slot."
    
    Always be helpful and provide value in your response!
  `,
});

export async function generateResponse(userRequest, scheduleData, dateInfo, eventResult) {
  try {
    const prompt = `
User Request: "${userRequest}"
Extracted Date Info: ${JSON.stringify(dateInfo, null, 2)}
LLM Schedule Plan: ${JSON.stringify(scheduleData, null, 2)}
Event Creation Result: ${JSON.stringify(eventResult, null, 2)}

Please generate a friendly, helpful response explaining what was scheduled and providing useful information to the user.
`;

    const result = await run(responseGeneratorAgent, prompt);
    const responseData = JSON.parse(result.finalOutput);
    return responseData;
  } catch (error) {
    console.error('Error generating response:', error);
    // Fallback to simple response
    return generateFallbackResponse(userRequest, scheduleData, dateInfo, eventResult);
  }
}

// Fallback response generation if LLM fails
function generateFallbackResponse(userRequest, scheduleData, dateInfo, eventResult) {
  const eventTitle = scheduleData.title || 'Scheduled Event';
  const date = dateInfo.date;
  const time = scheduleData.suggestedTime;
  const duration = scheduleData.duration || '60';
  
  let message = `I've successfully scheduled "${eventTitle}" for ${date} at ${time}. `;
  
  if (eventResult.success) {
    message += `The event has been added to your calendar with a ${duration}-minute duration. `;
    if (scheduleData.reasoning) {
      message += `I chose this time because ${scheduleData.reasoning.toLowerCase()}. `;
    }
    message += `You can view the event in your calendar.`;
  } else {
    message += `However, there was an issue creating the calendar event: ${eventResult.error}. Please try again.`;
  }
  
  return {
    message: message,
    summary: `Scheduled ${eventTitle} for ${date} at ${time}`,
    details: {
      eventTitle: eventTitle,
      date: date,
      time: time,
      duration: duration,
      calendarLink: eventResult.eventLink || null
    },
    nextSteps: [
      "Check your calendar to confirm the event",
      "Set any additional reminders if needed",
      "Share the event with attendees if required"
    ],
    helpfulTips: [
      "The event includes automatic reminders 24 hours and 15 minutes before",
      "You can modify the event details directly in Google Calendar",
      "Consider adding meeting notes or agenda to the event description"
    ]
  };
}

// Function to format response for different output types
export function formatResponse(responseData, outputType = 'console') {
  switch (outputType) {
    case 'console':
      return formatConsoleResponse(responseData);
    case 'json':
      return JSON.stringify(responseData, null, 2);
    case 'simple':
      return responseData.message;
    default:
      return responseData;
  }
}

// Format response for console output
function formatConsoleResponse(responseData) {
  const lines = [];
  
  // Main message
  lines.push(`\n🤖 ${responseData.message}`);
  
  // Summary
  lines.push(`\n📋 Summary: ${responseData.summary}`);
  
  // Details
  lines.push('\n📅 Event Details:');
  lines.push(`   • Title: ${responseData.details.eventTitle}`);
  lines.push(`   • Date: ${responseData.details.date}`);
  lines.push(`   • Time: ${responseData.details.time}`);
  lines.push(`   • Duration: ${responseData.details.duration} minutes`);
  if (responseData.details.calendarLink) {
    lines.push(`   • Calendar Link: ${responseData.details.calendarLink}`);
  }
  
  // Next steps
  if (responseData.nextSteps && responseData.nextSteps.length > 0) {
    lines.push('\n✅ Next Steps:');
    responseData.nextSteps.forEach((step, index) => {
      lines.push(`   ${index + 1}. ${step}`);
    });
  }
  
  // Helpful tips
  if (responseData.helpfulTips && responseData.helpfulTips.length > 0) {
    lines.push('\n💡 Helpful Tips:');
    responseData.helpfulTips.forEach((tip, index) => {
      lines.push(`   • ${tip}`);
    });
  }
  
  return lines.join('\n');
}

// Function to generate error responses
export function generateErrorResponse(error, userRequest) {
  return {
    message: `I'm sorry, but I encountered an issue while trying to schedule your request: "${userRequest}". ${error.message}`,
    summary: "Scheduling failed due to an error",
    details: {
      eventTitle: null,
      date: null,
      time: null,
      duration: null,
      calendarLink: null
    },
    nextSteps: [
      "Please try again with a different time or date",
      "Check your calendar manually for conflicts",
      "Contact support if the issue persists"
    ],
    helpfulTips: [
      "Make sure your request includes a clear date and time",
      "Try using specific times like '2pm' instead of 'afternoon'",
      "Check that your Google Calendar is accessible"
    ]
  };
}

// Function to generate confirmation response
export function generateConfirmationResponse(scheduleData, dateInfo) {
  return {
    message: `I'm ready to schedule "${scheduleData.title}" for ${dateInfo.date} at ${scheduleData.suggestedTime}. Should I proceed with creating this calendar event?`,
    summary: `Ready to schedule ${scheduleData.title}`,
    details: {
      eventTitle: scheduleData.title,
      date: dateInfo.date,
      time: scheduleData.suggestedTime,
      duration: scheduleData.duration,
      calendarLink: null
    },
    nextSteps: [
      "Confirm to create the calendar event",
      "Modify the details if needed",
      "Cancel if you want to try a different time"
    ],
    helpfulTips: [
      "The event will include automatic reminders",
      "You can always modify the event after creation",
      "The suggested time avoids any calendar conflicts"
    ]
  };
} 