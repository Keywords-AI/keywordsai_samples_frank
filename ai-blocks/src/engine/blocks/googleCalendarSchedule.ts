// src/engine/blocks/googleCalendarSchedule.ts
/**
 * Google Calendar Schedule block - Level 1
 * Teaches players how to create calendar events
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const googleCalendarScheduleBlock: Block = {
  type: "googleCalendarSchedule",
  label: "Google Calendar Schedule",
  description: "Create the meeting! This adds a new event to Google Calendar.",
  category: "tool",
  level: 1,
  
  handles: {
    inputs: [
      {
        id: "input",
        label: "Meeting Details",
        type: "suggestion",
        required: true,
      }
    ],
    outputs: [
      {
        id: "output",
        label: "Created Event",
        type: "schedule",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "📝 Takes meeting details (time, title, participants)",
    outputHint: "✅ Outputs confirmation of the created calendar event",
    usageExample: "Connect time suggestions to this block to actually create meetings"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    const meetingDetails = context.input;
    
    // Simulate calendar event creation for the game
    const createdEvent = {
      eventId: "evt_" + Math.random().toString(36).substr(2, 9),
      title: "Team Meeting",
      time: "Tomorrow 10:00 AM - 11:00 AM",
      attendees: ["team@company.com"],
      location: "Conference Room A",
      status: "confirmed",
      link: "https://calendar.google.com/event/...",
      confirmationSent: true
    };
    
    return createExecutionResult(
      context.nodeId,
      meetingDetails,
      createdEvent,
      { blockType: "googleCalendarSchedule", apiCall: true }
    );
  }
}; 