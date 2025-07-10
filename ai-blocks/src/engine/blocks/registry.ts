// src/engine/blocks/registry.ts
/**
 * Block registry - imports and registers all available block types
 * This file should be imported once at app startup to register all blocks
 */

import { blockRegistry } from "./index";
import { userInputBlock } from "./userInput";
import { llmParseBlock } from "./llmParse";
import { contextMergeBlock } from "./contextMerge"; // Essential - combines user input with context!
import { contextVariableBlock } from "./contextVariable"; // Essential - provides current date/time context!  
import { llmSuggestTimeBlock } from "./llmSuggestTime";
import { googleCalendarGetBlock } from "./googleCalendarGet"; // Actually essential - need to check for conflicts!
import { googleCalendarScheduleBlock } from "./googleCalendarSchedule";
import { userOutputBlock } from "./userOutput";
// import { dataFormatterBlock } from "./dataFormatter"; // Removed - redundant with LLM functionality

/**
 * Register all available blocks
 * Call this function once at app startup
 */
export function initializeBlocks(): void {
  // Input blocks
  blockRegistry.register(userInputBlock);
  blockRegistry.register(contextVariableBlock); // Essential - provides current date/time context!
  
  // Transform blocks
  blockRegistry.register(contextMergeBlock); // Essential - combines user input with context!
  // blockRegistry.register(dataFormatterBlock); // Removed - LLMs can format data
  
  // LLM blocks
  blockRegistry.register(llmParseBlock);
  blockRegistry.register(llmSuggestTimeBlock);
  
  // Tool blocks
  blockRegistry.register(googleCalendarGetBlock); // Essential - must check for conflicts!
  blockRegistry.register(googleCalendarScheduleBlock);
  
  // Output blocks
  blockRegistry.register(userOutputBlock);
}

/**
 * Get all blocks organized by category for the toolbox
 */
export function getBlocksByCategory() {
  return {
    input: blockRegistry.getByCategory('input'),
    transform: blockRegistry.getByCategory('transform'), // Context blocks are essential!
    llm: blockRegistry.getByCategory('llm'),
    tool: blockRegistry.getByCategory('tool'),
    output: blockRegistry.getByCategory('output'),
    // control: blockRegistry.getByCategory('control'), // No control blocks in Level 1
  };
}

/**
 * Get a specific block by type
 */
export function getBlock(type: string) {
  return blockRegistry.get(type);
}

/**
 * Check if a block type exists
 */
export function blockExists(type: string): boolean {
  return blockRegistry.exists(type);
} 