// src/engine/blocks/googleCalendarGet.ts
/**
 * Google Calendar Get block - Level 1
 * Teaches players how to retrieve calendar information
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const googleCalendarGetBlock: Block = {
  type: "googleCalendarGet",
  label: "Google Calendar Get",
  description: "Check the calendar! This gets current events and availability from Google Calendar.",
  category: "tool",
  level: 1,
  
  handles: {
    inputs: [
      {
        id: "input",
        label: "Time Range",
        type: "data",
        required: false,
      }
    ],
    outputs: [
      {
        id: "output",
        label: "Calendar Data",
        type: "schedule",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "📅 Takes time range or uses default (next 7 days)",
    outputHint: "📋 Outputs current events, busy times, and free slots",
    usageExample: "Use this to check availability before suggesting meeting times"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    // Simulate calendar data for the game
    const calendarData = {
      events: [
        {
          title: "Team Standup",
          time: "Today 9:00 AM - 9:30 AM",
          status: "busy"
        },
        {
          title: "Client Call",
          time: "Tomorrow 2:00 PM - 3:00 PM", 
          status: "busy"
        }
      ],
      freeSlots: [
        "Today 10:00 AM - 12:00 PM",
        "Tomorrow 10:00 AM - 2:00 PM",
        "Tomorrow 4:00 PM - 5:00 PM"
      ],
      summary: {
        totalEvents: 2,
        busyHours: 1.5,
        freeHours: 6.5
      }
    };
    
    return createExecutionResult(
      context.nodeId,
      context.input,
      calendarData,
      { blockType: "googleCalendarGet", apiCall: true }
    );
  }
}; 