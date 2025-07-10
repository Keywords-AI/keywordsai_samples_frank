// src/engine/blocks/index.ts
/**
 * Block system for Workflow Building Game - Level 1
 * Simple blocks that teach players how to connect AI pipelines
 */

import { ExecutionContext, ExecutionResult } from "../graph";

/**
 * Simplified Block interface for the game
 */
export interface Block {
  /** Unique identifier for this block type */
  type: string;
  
  /** Human-readable name for the toolbox */
  label: string;
  
  /** Description of what this block does */
  description: string;
  
  /** Category for grouping in toolbox */
  category: 'input' | 'transform' | 'llm' | 'output' | 'control' | 'tool';
  
  /** Level of difficulty (1 = basic, 2 = intermediate, 3 = advanced) */
  level: number;
  
  /** Input/output handle configuration */
  handles: {
    inputs: HandleConfig[];
    outputs: HandleConfig[];
  };
  
  /** Game hints for players */
  hints: {
    /** What this block expects as input */
    inputHint: string;
    /** What this block produces as output */
    outputHint: string;
    /** Example of how to use this block */
    usageExample: string;
  };
  
  /** Simple execution for game validation */
  execute: (context: ExecutionContext) => Promise<ExecutionResult>;
}

export interface HandleConfig {
  id: string;
  label: string;
  type: 'text' | 'data' | 'schedule' | 'suggestion' | 'any';
  required: boolean;
}

/**
 * Global registry of all available blocks
 */
class BlockRegistry {
  private blocks: Map<string, Block> = new Map();

  register(block: Block): void {
    this.blocks.set(block.type, block);
  }

  get(type: string): Block | undefined {
    return this.blocks.get(type);
  }

  getAll(): Block[] {
    return Array.from(this.blocks.values());
  }

  getByCategory(category: Block['category']): Block[] {
    return this.getAll().filter(block => block.category === category);
  }

  getByLevel(level: number): Block[] {
    return this.getAll().filter(block => block.level === level);
  }

  exists(type: string): boolean {
    return this.blocks.has(type);
  }
}

// Export singleton instance
export const blockRegistry = new BlockRegistry();

/**
 * Helper function to create a simple execution result for the game
 */
export function createExecutionResult(
  nodeId: string,
  input: any,
  output: any,
  metadata: Partial<ExecutionResult['metadata']> = {}
): ExecutionResult {
  return {
    nodeId,
    input,
    output,
    metadata: {
      timestamp: Date.now(),
      duration: 50, // Simplified for game
      success: true,
      ...metadata,
    },
  };
} 