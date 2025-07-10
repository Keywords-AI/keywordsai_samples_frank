// src/engine/blocks/dataFormatter.ts
/**
 * Data Formatter block - Level 1
 * Teaches players how to transform and organize data
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const dataFormatterBlock: Block = {
  type: "dataFormatter",
  label: "Data Formatter",
  description: "Organize data! This cleans up and restructures information to make it more useful.",
  category: "transform",
  level: 1,
  
  handles: {
    inputs: [
      {
        id: "input",
        label: "Raw Data",
        type: "data",
        required: true,
      }
    ],
    outputs: [
      {
        id: "output",
        label: "Formatted Data",
        type: "data",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "📊 Takes messy or complex data structures",
    outputHint: "🗂️ Outputs clean, organized data that's easier to use",
    usageExample: "Use this to prepare data before sending it to other blocks"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    const inputData = context.input;
    
    // Simulate data formatting for the game
    const formattedData = {
      summary: {
        dataType: typeof inputData,
        processed: true,
        timestamp: new Date().toISOString()
      },
      cleanedData: inputData,
      metadata: {
        formattingApplied: ["structure cleanup", "type validation"],
        readyForNextStep: true
      }
    };
    
    return createExecutionResult(
      context.nodeId,
      inputData,
      formattedData,
      { blockType: "dataFormatter" }
    );
  }
}; 