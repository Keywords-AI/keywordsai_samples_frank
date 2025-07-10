// src/levels/level1/config.ts
/**
 * Level 1 Configuration - Meeting Scheduler Workflow
 */

import { LevelConfig, LevelAnswer } from "../types";

/**
 * Level 1 Primary Answer: Context-Aware Meeting Scheduler
 * User Input → Context Variable → Context Merge → LLM Parse → Google Calendar Get → LLM Suggest Time → Google Calendar Schedule → LLM Text Output
 */
export const LEVEL_1_PRIMARY_ANSWER: LevelAnswer = {
  requiredBlocks: ["userInput", "contextVariable", "contextMerge", "llmParse", "googleCalendarGet", "llmSuggestTime", "googleCalendarSchedule", "userOutput"],
  requiredConnections: [
    { from: "userInput", to: "contextMerge" },
    { from: "contextVariable", to: "contextMerge" },
    { from: "contextMerge", to: "llmParse" },
    { from: "llmParse", to: "googleCalendarGet" },
    { from: "googleCalendarGet", to: "llmSuggestTime" },
    { from: "llmSuggestTime", to: "googleCalendarSchedule" },
    { from: "googleCalendarSchedule", to: "userOutput" }
  ],
  minBlocks: 8,
  maxBlocks: 8,
  description: "A complete workflow that understands relative dates like 'tomorrow', checks existing calendar, avoids conflicts, and creates events with proper context."
};

// Removed alternative answer - Level 1 now has only ONE perfect solution

/**
 * Level 1 Complete Configuration
 */
export const LEVEL_1_CONFIG: LevelConfig = {
  id: 1,
  title: "Meeting Scheduler",
  description: "Build a workflow using all blocks that can understand meeting requests and automatically schedule them in Google Calendar.",
  availableBlocks: [
    "userInput",
    "contextVariable",
    "contextMerge",
    "llmParse", 
    "googleCalendarGet",
    "llmSuggestTime",
    "googleCalendarSchedule",
    "userOutput"
  ],
  answers: [
    LEVEL_1_PRIMARY_ANSWER
  ],
  objectives: [
    "Understand how workflows process user input",
    "Learn about connecting different AI services",
    "Practice building end-to-end workflows",
    "Master the concept of data flow between blocks"
  ],
  difficulty: 1
}; 