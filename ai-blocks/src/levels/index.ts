// src/levels/index.ts
/**
 * Level System - manages all levels and provides unified access
 */

import { LevelConfig, LevelValidator } from "./types";
import { LEVEL_1_CONFIG } from "./level1/config";
import { level1Validator } from "./level1/validation";

/**
 * Registry of all available levels
 */
const LEVEL_CONFIGS: Record<number, LevelConfig> = {
  1: LEVEL_1_CONFIG,
  // Future levels will be added here:
  // 2: LEVEL_2_CONFIG,
  // 3: LEVEL_3_CONFIG,
};

/**
 * Registry of all level validators
 */
const LEVEL_VALIDATORS: Record<number, LevelValidator> = {
  1: level1Validator,
  // Future validators will be added here:
  // 2: level2Validator,
  // 3: level3Validator,
};

/**
 * Get configuration for a specific level
 */
export function getLevelConfig(levelId: number): LevelConfig | null {
  return LEVEL_CONFIGS[levelId] || null;
}

/**
 * Get validator for a specific level
 */
export function getLevelValidator(levelId: number): LevelValidator | null {
  return LEVEL_VALIDATORS[levelId] || null;
}

/**
 * Get all available levels
 */
export function getAllLevels(): LevelConfig[] {
  return Object.values(LEVEL_CONFIGS).sort((a, b) => a.id - b.id);
}

/**
 * Get unlocked levels based on user progress
 */
export function getUnlockedLevels(completedLevels: number[]): LevelConfig[] {
  return getAllLevels().filter(level => {
    const validator = getLevelValidator(level.id);
    return validator ? validator.isUnlocked(completedLevels) : false;
  });
}

/**
 * Check if a specific level is unlocked
 */
export function isLevelUnlocked(levelId: number, completedLevels: number[]): boolean {
  const validator = getLevelValidator(levelId);
  return validator ? validator.isUnlocked(completedLevels) : false;
}

/**
 * Get the next level after completing current level
 */
export function getNextLevel(currentLevelId: number): LevelConfig | null {
  const nextLevelId = currentLevelId + 1;
  return getLevelConfig(nextLevelId);
}

/**
 * Get available blocks for a specific level
 */
export function getLevelBlocks(levelId: number): string[] {
  const config = getLevelConfig(levelId);
  return config ? config.availableBlocks : [];
}

// Re-export types for convenience
export type { LevelConfig, LevelValidator, ValidationResult, LevelAnswer } from "./types"; 