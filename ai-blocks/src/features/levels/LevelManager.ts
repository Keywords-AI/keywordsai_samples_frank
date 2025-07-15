// src/features/levels/LevelManager.ts
/**
 * Level Manager - Unified level system that integrates with block configuration
 * Manages level progression, validation, and block availability
 */

import { getLevelConfig, LevelConfig, LevelAnswer, getBlocksForLevel } from "@/config/levels";
import { getBlockConfig, BlockConfig } from "@/config/blocks";
import { BlockFactory } from "@/engine/blocks/factory";

export interface LevelState {
  levelId: string;
  isCompleted: boolean;
  score: number;
  stars: number;
  completedAt?: Date;
  attempts: number;
  bestTime?: number;
  bestScore?: number;
}

export interface LevelProgress {
  completedLevels: string[];
  currentLevel?: string;
  levelStates: Record<string, LevelState>;
  totalScore: number;
  totalStars: number;
}

export class LevelManager {
  private static instance: LevelManager;
  private progress: LevelProgress = {
    completedLevels: [],
    levelStates: {},
    totalScore: 0,
    totalStars: 0
  };

  private constructor() {
    this.loadProgress();
  }

  static getInstance(): LevelManager {
    if (!LevelManager.instance) {
      LevelManager.instance = new LevelManager();
    }
    return LevelManager.instance;
  }

  /**
   * Get current level progress
   */
  getProgress(): LevelProgress {
    return { ...this.progress };
  }

  /**
   * Get level configuration with block availability
   */
  getLevelWithBlocks(levelId: string): {
    level: LevelConfig;
    availableBlocks: BlockConfig[];
  } | null {
    const level = getLevelConfig(levelId);
    if (!level) return null;

    const availableBlocks = level.availableBlocks
      .map(blockId => getBlockConfig(blockId))
      .filter(block => block !== undefined) as BlockConfig[];

    return {
      level,
      availableBlocks
    };
  }

  /**
   * Check if a level is unlocked
   */
  isLevelUnlocked(levelId: string): boolean {
    const level = getLevelConfig(levelId);
    if (!level) return false;

    // Sandbox and explicitly available levels are always unlocked
    if (level.category === 'sandbox' || level.isAvailable) return true;

    // Check unlock conditions
    if (level.unlockConditions) {
      // All required levels must be completed
      const requiredCompleted = level.unlockConditions.requiredLevels.every(
        requiredLevelId => this.progress.completedLevels.includes(requiredLevelId)
      );

      // Check minimum score if specified
      if (level.unlockConditions.requiredScore) {
        const hasRequiredScore = level.unlockConditions.requiredLevels.every(
          requiredLevelId => {
            const state = this.progress.levelStates[requiredLevelId];
            return state && state.score >= (level.unlockConditions?.requiredScore || 0);
          }
        );
        return requiredCompleted && hasRequiredScore;
      }

      return requiredCompleted;
    }

    return false;
  }

  /**
   * Get all unlocked levels
   */
  getUnlockedLevels(): LevelConfig[] {
    const allLevels = Object.values(getLevelConfig);
    return allLevels.filter(level => this.isLevelUnlocked(level.id));
  }

  /**
   * Start a level
   */
  startLevel(levelId: string): boolean {
    if (!this.isLevelUnlocked(levelId)) {
      console.warn(`Level ${levelId} is not unlocked`);
      return false;
    }

    this.progress.currentLevel = levelId;
    
    // Initialize level state if not exists
    if (!this.progress.levelStates[levelId]) {
      this.progress.levelStates[levelId] = {
        levelId,
        isCompleted: false,
        score: 0,
        stars: 0,
        attempts: 0
      };
    }

    this.progress.levelStates[levelId].attempts++;
    this.saveProgress();
    return true;
  }

  /**
   * Complete a level with validation
   */
  completeLevel(levelId: string, userGraph: any): {
    isSuccess: boolean;
    score: number;
    stars: number;
    feedback: string;
    matchedAnswer?: LevelAnswer;
  } {
    const level = getLevelConfig(levelId);
    if (!level) {
      return { isSuccess: false, score: 0, stars: 0, feedback: 'Level not found' };
    }

    const validation = this.validateLevel(levelId, userGraph);
    
    if (validation.isSuccess) {
      // Update level state
      const levelState = this.progress.levelStates[levelId];
      if (levelState) {
        levelState.isCompleted = true;
        levelState.completedAt = new Date();
        levelState.bestScore = Math.max(levelState.bestScore || 0, validation.score);
        levelState.score = validation.score;
        levelState.stars = validation.stars;
      }

      // Update progress
      if (!this.progress.completedLevels.includes(levelId)) {
        this.progress.completedLevels.push(levelId);
      }

      this.updateTotalProgress();
      this.saveProgress();
    }

    return validation;
  }

  /**
   * Validate level completion
   */
  private validateLevel(levelId: string, userGraph: any): {
    isSuccess: boolean;
    score: number;
    stars: number;
    feedback: string;
    matchedAnswer?: LevelAnswer;
  } {
    const level = getLevelConfig(levelId);
    if (!level || level.answers.length === 0) {
      return { isSuccess: false, score: 0, stars: 0, feedback: 'No validation rules found' };
    }

    // Check each possible answer
    for (const answer of level.answers) {
      const validation = this.validateAnswer(userGraph, answer, level);
      if (validation.isSuccess) {
        return { ...validation, matchedAnswer: answer };
      }
    }

    return { isSuccess: false, score: 0, stars: 0, feedback: 'Solution does not match any expected answer' };
  }

  /**
   * Validate specific answer
   */
  private validateAnswer(userGraph: any, answer: LevelAnswer, level: LevelConfig): {
    isSuccess: boolean;
    score: number;
    stars: number;
    feedback: string;
  } {
    // Extract nodes and edges from user graph
    const nodes = userGraph.nodes || [];
    const edges = userGraph.edges || [];

    let score = 0;
    let feedback = '';

    // Check block count
    if (nodes.length < answer.minBlocks) {
      return {
        isSuccess: false,
        score: 0,
        stars: 0,
        feedback: `Not enough blocks. Need at least ${answer.minBlocks}, but found ${nodes.length}`
      };
    }

    if (nodes.length > answer.maxBlocks) {
      return {
        isSuccess: false,
        score: 0,
        stars: 0,
        feedback: `Too many blocks. Maximum allowed is ${answer.maxBlocks}, but found ${nodes.length}`
      };
    }

    // Check required blocks
    const userBlockTypes = nodes.map((node: any) => node.data?.blockType || node.type);
    const missingBlocks = answer.requiredBlocks.filter(blockType => !userBlockTypes.includes(blockType));
    
    if (missingBlocks.length > 0) {
      return {
        isSuccess: false,
        score: 20,
        stars: 0,
        feedback: `Missing required blocks: ${missingBlocks.join(', ')}`
      };
    }

    score += 40; // Base score for having all required blocks

    // Check connections
    const userConnections = edges.map((edge: any) => ({
      from: nodes.find((n: any) => n.id === edge.source)?.data?.blockType || edge.source,
      to: nodes.find((n: any) => n.id === edge.target)?.data?.blockType || edge.target
    }));

    const missingConnections = answer.requiredConnections.filter(conn => 
      !userConnections.some((userConn: { from: string; to: string }) => userConn.from === conn.from && userConn.to === conn.to)
    );

    if (missingConnections.length > 0) {
      return {
        isSuccess: false,
        score: score + 20,
        stars: 0,
        feedback: `Missing required connections: ${missingConnections.map(c => `${c.from} → ${c.to}`).join(', ')}`
      };
    }

    score += 40; // Additional score for correct connections

    // Calculate stars based on score
    let stars = 0;
    if (score >= level.starThresholds.threeStar) stars = 3;
    else if (score >= level.starThresholds.twoStar) stars = 2;
    else if (score >= level.starThresholds.oneStar) stars = 1;

    return {
      isSuccess: true,
      score,
      stars,
      feedback: `Great work! ${answer.description}`
    };
  }

  /**
   * Update total progress calculations
   */
  private updateTotalProgress(): void {
    this.progress.totalScore = Object.values(this.progress.levelStates)
      .reduce((sum, state) => sum + state.score, 0);
    
    this.progress.totalStars = Object.values(this.progress.levelStates)
      .reduce((sum, state) => sum + state.stars, 0);
  }

  /**
   * Save progress to localStorage
   */
  private saveProgress(): void {
    try {
      localStorage.setItem('ai-blocks-progress', JSON.stringify(this.progress));
    } catch (error) {
      console.warn('Failed to save progress:', error);
    }
  }

  /**
   * Load progress from localStorage
   */
  private loadProgress(): void {
    try {
      const saved = localStorage.getItem('ai-blocks-progress');
      if (saved) {
        this.progress = { ...this.progress, ...JSON.parse(saved) };
      }
    } catch (error) {
      console.warn('Failed to load progress:', error);
    }
  }

  /**
   * Reset all progress
   */
  resetProgress(): void {
    this.progress = {
      completedLevels: [],
      levelStates: {},
      totalScore: 0,
      totalStars: 0
    };
    this.saveProgress();
  }

  /**
   * Get level statistics
   */
  getLevelStats(levelId: string): LevelState | null {
    return this.progress.levelStates[levelId] || null;
  }
}

// Export singleton instance
export const levelManager = LevelManager.getInstance(); 