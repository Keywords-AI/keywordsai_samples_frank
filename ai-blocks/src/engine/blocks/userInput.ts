// src/engine/blocks/userInput.ts
/**
 * User Input block - Level 1
 * Teaches players how to provide input to workflows
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const userInputBlock: Block = {
  type: "userInput",
  label: "User Input",
  description: "Start here! This is where users give instructions to your workflow.",
  category: "input",
  level: 1,
  
  handles: {
    inputs: [], // No inputs - this is the starting point
    outputs: [
      {
        id: "output",
        label: "User Request",
        type: "text",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "💭 No input needed - this is where the user types their request",
    outputHint: "📝 Outputs user's text request (like 'Schedule a meeting tomorrow')",
    usageExample: "Connect this to LLM Parse to analyze what the user wants"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
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
  }
}; 