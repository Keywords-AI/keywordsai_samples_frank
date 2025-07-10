// src/engine/blocks/userOutput.ts
/**
 * User Output Block - Final formatted output for the user
 * This creates a nicely formatted message or report for the user.
 */

import { Block, createExecutionResult } from "./index";
import { ExecutionContext, ExecutionResult } from "../graph";

export const userOutputBlock: Block = {
  type: "userOutput",
  label: "User Output",
  description: "The final step! This creates a nicely formatted message or report for the user.",
  category: "output",
  level: 1,
  
  handles: {
    inputs: [
      { id: "input", label: "Text to format", type: "text", required: true }
    ],
    outputs: [] // This is the final output, no connections needed
  },

  hints: {
    inputHint: "🎯 Connect from your final processing step (like calendar scheduling)",
    outputHint: "✨ This creates the final message shown to the user - no further connections needed",
    usageExample: "Shows formatted results like 'Meeting scheduled for tomorrow at 2 PM'"
  },



  async execute(context: ExecutionContext): Promise<ExecutionResult> {
    const inputData = context.input || "No input provided";
    const params = context.metadata?.params || {};
    const format = params.format || "plain";
    const template = params.template || "Here's your result:\n\n{input}";

    // Replace {input} in template with actual input
    let formattedText = template.replace(/\{input\}/g, inputData);

    // Apply formatting based on selected format
    switch (format) {
      case "markdown":
        formattedText = `# Result\n\n${formattedText}`;
        break;
      case "html":
        formattedText = `<div class="result"><h2>Result</h2><p>${formattedText}</p></div>`;
        break;
      case "plain":
      default:
        // Keep as is for plain text
        break;
    }

    // Simulate some processing time
    await new Promise(resolve => setTimeout(resolve, 150));

    return createExecutionResult(
      context.nodeId,
      inputData,
      formattedText,
      { blockType: "userOutput", formatted: true }
    );
  }
}; 