// src/levels/types.ts
/**
 * Common types for all levels in the AI Blocks game
 */

import { Graph } from "../engine/graph";

export interface LevelAnswer {
  /** Required block sequence in correct order */
  requiredBlocks: string[];
  /** Required connections between blocks */
  requiredConnections: Array<{
    from: string; // block type
    to: string;   // block type
  }>;
  /** Minimum number of blocks needed */
  minBlocks: number;
  /** Maximum allowed blocks (to prevent over-engineering) */
  maxBlocks: number;
  /** Description of what this answer achieves */
  description: string;
}

export interface ValidationResult {
  /** Whether the pipeline is correct */
  isCorrect: boolean;
  /** Score out of 100 */
  score: number;
  /** What the user got right */
  correctAspects: string[];
  /** What needs to be fixed */
  issues: string[];
  /** Helpful hints for improvement */
  hints: string[];
  /** Overall feedback message */
  message: string;
}

export interface LevelConfig {
  /** Level number */
  id: number;
  /** Level title */
  title: string;
  /** Level description */
  description: string;
  /** Available block types for this level */
  availableBlocks: string[];
  /** Possible correct answers */
  answers: LevelAnswer[];
  /** Learning objectives */
  objectives: string[];
  /** Difficulty level (1-5) */
  difficulty: number;
}

export interface LevelValidator {
  /** Validate user's pipeline against level requirements */
  validate(graph: Graph): ValidationResult;
  /** Get hints specific to this level */
  getHints(): string[];
  /** Check if level is unlocked (based on previous completions) */
  isUnlocked(completedLevels: number[]): boolean;
} 