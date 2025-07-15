// src/engine/blocks/factory.ts
/**
 * Block Factory - Creates block instances based on configuration
 * This makes blocks more configurable and reusable
 */

import { Block } from "./index";
import { BlockConfig, getBlockConfig } from "@/config/blocks";
import { ExecutionContext, ExecutionResult } from "../graph";

/**
 * Block factory that creates blocks from configuration
 */
export class BlockFactory {
  private static executorMap: Map<string, (context: ExecutionContext) => Promise<ExecutionResult>> = new Map();

  /**
   * Register a block executor function
   */
  static registerExecutor(blockId: string, executor: (context: ExecutionContext) => Promise<ExecutionResult>) {
    this.executorMap.set(blockId, executor);
  }

  /**
   * Create a block instance from configuration
   */
  static createBlock(blockId: string): Block | null {
    const config = getBlockConfig(blockId);
    if (!config) {
      console.warn(`Block configuration not found for: ${blockId}`);
      return null;
    }

    const executor = this.executorMap.get(blockId);
    if (!executor) {
      console.warn(`Block executor not found for: ${blockId}`);
      return null;
    }

    return {
      type: config.id,
      label: config.label,
      description: config.description,
      category: config.category,
      level: config.level,
      handles: {
        inputs: config.handles.inputs.map(input => ({
          id: input.id,
          label: input.label,
          type: input.type as 'text' | 'data' | 'schedule' | 'suggestion' | 'any',
          required: input.required
        })),
        outputs: config.handles.outputs.map(output => ({
          id: output.id,
          label: output.label,
          type: output.type as 'text' | 'data' | 'schedule' | 'suggestion' | 'any',
          required: output.required
        }))
      },
      hints: config.hints,
      execute: executor
    };
  }

  /**
   * Get all available blocks
   */
  static getAllBlocks(): Block[] {
    const blocks: Block[] = [];
    for (const [blockId, executor] of this.executorMap.entries()) {
      const block = this.createBlock(blockId);
      if (block) {
        blocks.push(block);
      }
    }
    return blocks;
  }

  /**
   * Get blocks by category
   */
  static getBlocksByCategory(category: Block['category']): Block[] {
    return this.getAllBlocks().filter(block => block.category === category);
  }

  /**
   * Get blocks by level
   */
  static getBlocksByLevel(level: number): Block[] {
    return this.getAllBlocks().filter(block => block.level <= level);
  }

  /**
   * Check if a block exists
   */
  static exists(blockId: string): boolean {
    return this.executorMap.has(blockId);
  }
}

/**
 * Helper function to create execution results
 */
export function createExecutionResult(
  nodeId: string,
  input: any,
  output: any,
  metadata: Record<string, any> = {}
): ExecutionResult {
  return {
    nodeId,
    input,
    output,
    metadata: {
      timestamp: Date.now(),
      duration: 50, // Simplified for game
      ...metadata,
      executionId: Math.random().toString(36).substring(2, 15)
    }
  };
}

/**
 * Block executor registry - maps block IDs to their execution functions
 */
export const BlockExecutors = {
  // Input block executors
  userInput: async (context: ExecutionContext): Promise<ExecutionResult> => {
    // Simulate user input for the game
    const sampleInputs = [
      "Schedule a meeting with the team next week",
      "Find me a good time for a doctor appointment", 
      "Create a summary of today's events",
      "Plan my weekend activities"
    ];
    
    const userRequest = sampleInputs[Math.floor(Math.random() * sampleInputs.length)];
    
    return createExecutionResult(
      context.nodeId,
      null,
      userRequest,
      { blockType: "userInput" }
    );
  },

  contextVariable: async (context: ExecutionContext): Promise<ExecutionResult> => {
    // Simulate stored context data for the game
    const contextData = {
      userPreferences: {
        workingHours: "9:00 AM - 5:00 PM",
        timeZone: "Eastern Time",
        preferredMeetingLength: "30 minutes"
      },
      userInfo: {
        name: "Alex",
        role: "Project Manager",
        team: "Product Development"
      }
    };
    
    return createExecutionResult(
      context.nodeId,
      null,
      contextData,
      { blockType: "contextVariable" }
    );
  },

  // Transform block executors
  contextMerge: async (context: ExecutionContext): Promise<ExecutionResult> => {
    const mergedData = {
      originalInput: context.input,
      enrichedContext: "Merged with stored context data",
      timestamp: new Date().toISOString()
    };
    
    return createExecutionResult(
      context.nodeId,
      context.input,
      mergedData,
      { blockType: "contextMerge" }
    );
  },

  // LLM block executors
  llmParse: async (context: ExecutionContext): Promise<ExecutionResult> => {
    const inputText = context.input;
    
    // Simulate AI analysis for the game
    const analysis = {
      intent: "schedule_meeting",
      entities: {
        action: "schedule",
        object: "meeting", 
        timeframe: "tomorrow",
        participants: "team"
      },
      requirements: {
        needsCalendar: true,
        needsTimeSlot: true,
        duration: "1 hour"
      },
      confidence: 0.95
    };
    
    return createExecutionResult(
      context.nodeId,
      inputText,
      analysis,
      { blockType: "llmParse", aiProcessing: true }
    );
  },

  llmSuggestTime: async (context: ExecutionContext): Promise<ExecutionResult> => {
    const inputData = context.input;
    
    // Simulate AI time suggestions
    const suggestions = {
      recommendedTimes: [
        "Tomorrow at 2:00 PM",
        "Tomorrow at 3:30 PM",
        "Thursday at 10:00 AM"
      ],
      reasoning: "Based on calendar availability and preferences",
      confidence: 0.92
    };
    
    return createExecutionResult(
      context.nodeId,
      inputData,
      suggestions,
      { blockType: "llmSuggestTime", aiProcessing: true }
    );
  },

  // Tool block executors
  googleCalendarGet: async (context: ExecutionContext): Promise<ExecutionResult> => {
    const queryParams = context.input;
    
    // Simulate calendar data retrieval
    const calendarData = {
      events: [
        {
          id: "event1",
          title: "Team Standup",
          start: "2024-01-15T09:00:00Z",
          end: "2024-01-15T09:30:00Z"
        },
        {
          id: "event2",
          title: "Project Review",
          start: "2024-01-15T14:00:00Z",
          end: "2024-01-15T15:00:00Z"
        }
      ],
      availability: "Multiple time slots available"
    };
    
    return createExecutionResult(
      context.nodeId,
      queryParams,
      calendarData,
      { blockType: "googleCalendarGet", apiCall: true }
    );
  },

  googleCalendarSchedule: async (context: ExecutionContext): Promise<ExecutionResult> => {
    const eventDetails = context.input;
    
    // Simulate calendar event creation
    const createdEvent = {
      id: "event_" + Math.random().toString(36).substring(2, 15),
      title: "Scheduled Meeting",
      start: "2024-01-16T14:00:00Z",
      end: "2024-01-16T15:00:00Z",
      status: "confirmed"
    };
    
    return createExecutionResult(
      context.nodeId,
      eventDetails,
      createdEvent,
      { blockType: "googleCalendarSchedule", apiCall: true }
    );
  },

  // Output block executors
  userOutput: async (context: ExecutionContext): Promise<ExecutionResult> => {
    const finalResult = context.input;
    
    // Simulate formatted output for the user
    const formattedOutput = {
      message: "Meeting scheduled successfully!",
      details: finalResult,
      timestamp: new Date().toISOString()
    };
    
    return createExecutionResult(
      context.nodeId,
      finalResult,
      formattedOutput,
      { blockType: "userOutput", isComplete: true }
    );
  }
};

// Register all block executors
Object.entries(BlockExecutors).forEach(([blockId, executor]) => {
  BlockFactory.registerExecutor(blockId, executor);
}); 