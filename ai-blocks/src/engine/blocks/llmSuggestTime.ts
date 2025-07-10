// src/engine/blocks/llmSuggestTime.ts
/**
 * LLM Suggest Time block - Level 1
 * Teaches players how AI can suggest optimal times for meetings
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const llmSuggestTimeBlock: Block = {
  type: "llmSuggestTime",
  label: "LLM Suggest Time",
  description: "Smart scheduling! This workflow component finds the best times for meetings based on requirements.",
  category: "llm",
  level: 1,
  
  handles: {
    inputs: [
      {
        id: "input",
        label: "Meeting Requirements",
        type: "data",
        required: true,
      }
    ],
    outputs: [
      {
        id: "output",
        label: "Time Suggestions",
        type: "suggestion",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "📅 Takes meeting requirements (duration, participants, preferences)",
    outputHint: "⏰ Outputs workflow-generated time suggestions with reasoning",
    usageExample: "Connect LLM Parse → LLM Suggest Time to get optimal meeting times"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    const requirements = context.input;
    
    // Simulate AI time suggestions for the game
    const suggestions = {
      recommendedTimes: [
        {
          time: "Tomorrow 10:00 AM",
          reason: "Mid-morning when energy is high",
          confidence: 0.95
        },
        {
          time: "Tomorrow 2:00 PM", 
          reason: "Post-lunch availability window",
          confidence: 0.87
        },
        {
          time: "Day after tomorrow 11:00 AM",
          reason: "Avoids common meeting conflicts",
          confidence: 0.82
        }
      ],
      bestChoice: "Tomorrow 10:00 AM",
      reasoning: "Optimal time based on productivity patterns and availability"
    };
    
    return createExecutionResult(
      context.nodeId,
      requirements,
      suggestions,
      { blockType: "llmSuggestTime", aiProcessing: true }
    );
  }
}; 