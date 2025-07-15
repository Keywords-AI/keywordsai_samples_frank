// src/config/levels.ts
/**
 * Centralized levels configuration
 * Defines all available levels and their properties
 */

import { BLOCK_CONFIGS } from './blocks';

export interface LevelConfig {
  id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
  category: 'tutorial' | 'challenge' | 'sandbox';
  isAvailable: boolean;
  
  // Gameplay metrics
  targetTokens: number;
  targetApiCalls: number;
  targetTime: number; // in seconds
  observabilityTarget: number;
  estimatedDuration: string;
  
  // Scoring
  starThresholds: {
    oneStar: number;
    twoStar: number;
    threeStar: number;
  };
  
  // Level-specific configuration
  availableBlocks: string[];
  objectives: string[];
  
  // Correct answers for validation
  answers: LevelAnswer[];
  
  // Starter configuration
  starterGraph?: {
    nodes: any[];
    edges: any[];
  };
  
  // Hints and guidance
  hints: string[];
  unlockConditions?: {
    requiredLevels: string[];
    requiredScore?: number;
  };
}

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

export const LEVEL_CONFIGS: Record<string, LevelConfig> = {
  'level-1': {
    id: 'level-1',
    title: 'Tutorial 1 - Calendar Agent Workflow',
    description: 'Learn to build an AI agent that schedules meetings and manages calendar conflicts',
    difficulty: 'easy',
    tags: ['basics', 'tutorial', 'calendar', 'scheduling'],
    category: 'tutorial',
    isAvailable: true,
    
    targetTokens: 1000,
    targetApiCalls: 3,
    targetTime: 30,
    observabilityTarget: 80,
    estimatedDuration: '5-10min',
    
    starThresholds: {
      oneStar: 60,
      twoStar: 80,
      threeStar: 95
    },
    
    availableBlocks: [
      'userInput',
      'contextVariable', 
      'contextMerge',
      'llmParse',
      'googleCalendarGet',
      'llmSuggestTime',
      'googleCalendarSchedule',
      'userOutput'
    ],
    
    objectives: [
      'Connect user input to understand meeting requests',
      'Use context to provide relevant information',
      'Parse user intent with AI analysis',
      'Check calendar for conflicts',
      'Generate smart time suggestions',
      'Schedule the meeting successfully',
      'Provide clear output to the user'
    ],
    
    answers: [
      {
        requiredBlocks: [
          'userInput',
          'contextVariable',
          'contextMerge',
          'llmParse',
          'googleCalendarGet',
          'llmSuggestTime',
          'googleCalendarSchedule',
          'userOutput'
        ],
        requiredConnections: [
          { from: 'userInput', to: 'contextMerge' },
          { from: 'contextVariable', to: 'contextMerge' },
          { from: 'contextMerge', to: 'llmParse' },
          { from: 'llmParse', to: 'googleCalendarGet' },
          { from: 'googleCalendarGet', to: 'llmSuggestTime' },
          { from: 'llmSuggestTime', to: 'googleCalendarSchedule' },
          { from: 'googleCalendarSchedule', to: 'userOutput' }
        ],
        minBlocks: 8,
        maxBlocks: 8,
        description: 'A complete workflow that understands relative dates like "tomorrow", checks existing calendar, avoids conflicts, and creates events with proper context.'
      }
    ],
    
    starterGraph: {
      nodes: [
        {
          id: 'input-1',
          type: 'userInput',
          position: { x: 100, y: 200 },
          data: {
            label: 'User Input',
            params: {
              prompt: 'Enter some text to process:',
              defaultValue: 'Hello, world!'
            }
          }
        }
      ],
      edges: []
    },
    
    hints: [
      'Start with User Input to capture the meeting request',
      'Use Context Variable to store user preferences and settings',
      'Merge user input with context for better understanding',
      'Parse the request with LLM to extract meeting details',
      'Check existing calendar events to avoid conflicts',
      'Generate smart time suggestions based on availability',
      'Create the calendar event with the suggested time',
      'Provide confirmation to the user'
    ]
  },
  
  'level-2': {
    id: 'level-2',
    title: 'Tutorial 2 - Multi-Agent System',
    description: 'Design competing AI agents with complex decision trees and state management',
    difficulty: 'medium',
    tags: ['intermediate', 'multi-agent', 'state-management'],
    category: 'tutorial',
    isAvailable: false,
    
    targetTokens: 2000,
    targetApiCalls: 8,
    targetTime: 60,
    observabilityTarget: 85,
    estimatedDuration: '15min',
    
    starThresholds: {
      oneStar: 65,
      twoStar: 80,
      threeStar: 95
    },
    
    availableBlocks: [
      'userInput',
      'contextVariable',
      'contextMerge',
      'llmParse',
      'userOutput'
    ],
    
    objectives: [
      'Create multiple agent workflows',
      'Implement decision-making logic',
      'Manage state between agents',
      'Handle complex interactions'
    ],
    
    answers: [],
    hints: [],
    
    unlockConditions: {
      requiredLevels: ['level-1'],
      requiredScore: 80
    }
  },
  
  'level-3': {
    id: 'level-3',
    title: 'Tutorial 3 - Trading Agent Workflow',
    description: 'Build an autonomous trading agent with risk management and decision logic',
    difficulty: 'hard',
    tags: ['advanced', 'trading', 'risk-management'],
    category: 'challenge',
    isAvailable: false,
    
    targetTokens: 3000,
    targetApiCalls: 15,
    targetTime: 120,
    observabilityTarget: 90,
    estimatedDuration: '20min',
    
    starThresholds: {
      oneStar: 70,
      twoStar: 85,
      threeStar: 95
    },
    
    availableBlocks: [
      'userInput',
      'contextVariable',
      'contextMerge',
      'llmParse',
      'userOutput'
    ],
    
    objectives: [
      'Implement risk assessment',
      'Create trading decision logic',
      'Handle market data analysis',
      'Manage portfolio optimization'
    ],
    
    answers: [],
    hints: [],
    
    unlockConditions: {
      requiredLevels: ['level-1', 'level-2'],
      requiredScore: 85
    }
  },
  

};

// Helper functions
export function getLevelConfig(levelId: string): LevelConfig | undefined {
  return LEVEL_CONFIGS[levelId];
}

export function getAvailableLevels(): LevelConfig[] {
  return Object.values(LEVEL_CONFIGS).filter(level => level.isAvailable);
}

export function getLevelsByCategory(category: LevelConfig['category']): LevelConfig[] {
  return Object.values(LEVEL_CONFIGS).filter(level => level.category === category);
}

export function getAllLevels(): LevelConfig[] {
  return Object.values(LEVEL_CONFIGS);
}

export function isLevelUnlocked(levelId: string, completedLevels: string[], scores: Record<string, number>): boolean {
  const level = getLevelConfig(levelId);
  if (!level) return false;
  
  // Available levels are always unlocked
  if (level.isAvailable) return true;
  
  // Check unlock conditions
  if (level.unlockConditions) {
    // Check required levels
    const requiredCompleted = level.unlockConditions.requiredLevels.every(
      requiredLevel => completedLevels.includes(requiredLevel)
    );
    
    // Check required score if specified
    const requiredScore = level.unlockConditions.requiredScore || 0;
    const hasRequiredScore = level.unlockConditions.requiredLevels.every(
      requiredLevel => (scores[requiredLevel] || 0) >= requiredScore
    );
    
    return requiredCompleted && hasRequiredScore;
  }
  
  return false;
}

export function getBlocksForLevel(levelId: string): string[] {
  const level = getLevelConfig(levelId);
  return level?.availableBlocks || [];
}

export function validateLevelCompletion(levelId: string, userGraph: any): {
  isComplete: boolean;
  score: number;
  feedback: string;
  matchedAnswer?: LevelAnswer;
} {
  const level = getLevelConfig(levelId);
  if (!level || level.answers.length === 0) {
    return { isComplete: false, score: 0, feedback: 'Level not found or no answers defined' };
  }
  
  // Check each possible answer
  for (const answer of level.answers) {
    const result = validateAnswer(userGraph, answer);
    if (result.isComplete) {
      return { ...result, matchedAnswer: answer };
    }
  }
  
  return { isComplete: false, score: 0, feedback: 'No valid solution found' };
}

function validateAnswer(userGraph: any, answer: LevelAnswer): {
  isComplete: boolean;
  score: number;
  feedback: string;
} {
  // This is a simplified validation - in a real implementation,
  // you would check the graph structure against the answer requirements
  
  // For now, return a basic validation
  return {
    isComplete: false,
    score: 0,
    feedback: 'Validation not implemented yet'
  };
} 