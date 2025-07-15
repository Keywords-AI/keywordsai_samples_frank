// src/engine/blocks/registry.ts
/**
 * Block registry - now uses the new factory system for more flexible block management
 * This file should be imported once at app startup to register all blocks
 */

import { blockRegistry } from "./index";
import { BlockFactory } from "./factory";
import { getAllBlocks } from "@/config/blocks";

/**
 * Register all available blocks using the new factory system
 * Call this function once at app startup
 */
export function initializeBlocks(): void {
  // Get all blocks from factory and register them
  const blocks = BlockFactory.getAllBlocks();
  blocks.forEach(block => {
    blockRegistry.register(block);
  });
}

/**
 * Get blocks organized by category using the new factory system
 */
export function getBlocksCategorized(): Record<string, any[]> {
  const blocks = BlockFactory.getAllBlocks();
  const categories: Record<string, any[]> = {};
  
  blocks.forEach(block => {
    if (!categories[block.category]) {
      categories[block.category] = [];
    }
    categories[block.category].push(block);
  });
  
  return categories;
}

/**
 * Get all blocks
 */
export function getAllBlocksFromRegistry(): any[] {
  return BlockFactory.getAllBlocks();
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