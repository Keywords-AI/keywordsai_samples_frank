// src/engine/blocks/llmParse.ts
/**
 * LLM Parse block - Level 1  
 * Teaches players how AI can understand and analyze text
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const llmParseBlock: Block = {
  type: "llmParse",
  label: "LLM Parse",
  description: "The workflow analyzer! This analyzes text and understands what the user wants.",
  category: "llm", 
  level: 1,
  
  handles: {
    inputs: [
      {
        id: "input",
        label: "Text to Analyze",
        type: "text",
        required: true,
      }
    ],
    outputs: [
      {
        id: "output", 
        label: "AI Analysis",
        type: "data",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "📝 Takes user text (like 'Schedule a meeting tomorrow')",
    outputHint: "🧠 Outputs AI analysis with intent, entities, and requirements",
    usageExample: "Connect User Input → LLM Parse to understand what users want"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
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
  }
}; 