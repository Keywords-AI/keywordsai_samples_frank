// src/engine/blocks/contextVariable.ts
/**
 * Context Variable block - Level 1
 * Teaches players how to store information for their workflow
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const contextVariableBlock: Block = {
  type: "contextVariable", 
  label: "Context Variable",
  description: "Store important information that your workflow can use (like user preferences or settings).",
  category: "input",
  level: 1,
  
  handles: {
    inputs: [],
    outputs: [
      {
        id: "output",
        label: "Stored Data",
        type: "data",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "💾 No input needed - this stores pre-defined information",
    outputHint: "📋 Outputs stored data (like user preferences, API keys, or settings)",
    usageExample: "Use this to provide your workflow with context about the user"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
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
  }
}; 