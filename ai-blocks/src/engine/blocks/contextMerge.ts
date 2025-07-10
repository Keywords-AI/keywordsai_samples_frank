// src/engine/blocks/contextMerge.ts
/**
 * Context Merge block - Level 1
 * Teaches players how to combine information from different sources
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const contextMergeBlock: Block = {
  type: "contextMerge",
  label: "Context Merge",
  description: "Combine information! This takes data from multiple sources and puts them together.",
  category: "transform",
  level: 1,
  
  handles: {
    inputs: [
      {
        id: "primary",
        label: "Main Data",
        type: "data",
        required: true,
      },
      {
        id: "secondary",
        label: "Extra Data",
        type: "data",
        required: false,
      }
    ],
    outputs: [
      {
        id: "output",
        label: "Combined Data",
        type: "data",
        required: true,
      }
    ]
  },
  
  hints: {
    inputHint: "📊 Takes multiple pieces of data (AI analysis + user preferences)",
    outputHint: "🔗 Outputs one combined dataset with all the information together",
    usageExample: "Merge AI analysis with user context before making decisions"
  },
  
  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    const primaryData = context.input;
    // In the game, we'll simulate secondary input
    const secondaryData = { userContext: "additional context data" };
    
    // Simple merge operation for the game
    const mergedData = {
      ...primaryData,
      additionalContext: secondaryData,
      mergedAt: new Date().toISOString(),
      confidence: "high"
    };
    
    return createExecutionResult(
      context.nodeId,
      primaryData,
      mergedData,
      { blockType: "contextMerge" }
    );
  }
}; 