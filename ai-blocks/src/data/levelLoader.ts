// src/data/levelLoader.ts
/**
 * Level loader - loads and processes level definitions from JSON files
 */

import { LevelDefinition, TestCase, Evaluator } from "@/engine/evaluator";
import { Graph } from "@/engine/graph";

interface LevelJSON {
  id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
  targetTokens: number;
  targetApiCalls: number;
  targetTime: number;
  observabilityTarget: number;
  starThresholds: {
    oneStar: number;
    twoStar: number;
    threeStar: number;
  };
  starterGraph: Graph;
  tests: {
    id: string;
    name: string;
    description: string;
    category: 'functionality' | 'performance' | 'quality';
    points: number;
    assertion: string;
    params?: any[];
  }[];
  hints: string[];
  solution: {
    description: string;
    expectedBlocks: string[];
    expectedConnections: number;
  };
}

/**
 * Converts a JSON level definition to a proper LevelDefinition with executable test functions
 */
export function processLevelJSON(levelJSON: LevelJSON): LevelDefinition {
  const assertions = Evaluator.createAssertions();
  
  const tests: TestCase[] = levelJSON.tests.map(testJSON => {
    let assertion: TestCase['assertion'];
    
    // Map assertion strings to actual functions
    switch (testJSON.assertion) {
      case 'executionSucceeded':
        assertion = assertions.executionSucceeded();
        break;
      case 'usesBlockType':
        assertion = assertions.usesBlockType(testJSON.params?.[0] || '');
        break;
      case 'outputContains':
        assertion = assertions.outputContains(testJSON.params?.[0] || '');
        break;
      case 'outputEquals':
        assertion = assertions.outputEquals(testJSON.params?.[0]);
        break;
      case 'tokenUsageUnder':
        assertion = assertions.tokenUsageUnder(testJSON.params?.[0] || 1000);
        break;
      case 'hasConnectedFlow':
        // Custom assertion for connected workflow
        assertion = (trace) => {
          const connectedNodes = trace.results.filter(r => r.input !== null).length;
          return connectedNodes >= 1 || 'Workflow should have connected blocks';
        };
        break;
      default:
        // Fallback assertion
        assertion = () => true;
        console.warn(`Unknown assertion type: ${testJSON.assertion}`);
    }

    return {
      id: testJSON.id,
      name: testJSON.name,
      description: testJSON.description,
      assertion,
      points: testJSON.points,
      category: testJSON.category,
    };
  });

  return {
    id: levelJSON.id,
    title: levelJSON.title,
    description: levelJSON.description,
    difficulty: levelJSON.difficulty,
    tags: levelJSON.tags,
    targetTokens: levelJSON.targetTokens,
    targetApiCalls: levelJSON.targetApiCalls,
    targetTime: levelJSON.targetTime,
    observabilityTarget: levelJSON.observabilityTarget,
    tests,
    starThresholds: levelJSON.starThresholds,
  };
}

/**
 * Load a level by ID (in a real app this would fetch from the server)
 */
export async function loadLevel(levelId: string): Promise<{ level: LevelDefinition; starterGraph: Graph }> {
  try {
    // For now, we'll import the JSON file directly
    // In a real app, this would be a fetch request
    const levelModule = await import(`./levels/${levelId}.json`);
    const levelJSON: LevelJSON = levelModule.default;
    
    const level = processLevelJSON(levelJSON);
    const starterGraph = levelJSON.starterGraph;
    
    return { level, starterGraph };
  } catch (error) {
    throw new Error(`Failed to load level ${levelId}: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Get list of available levels (in a real app this would come from an API)
 */
export async function getAvailableLevels(): Promise<Array<{ id: string; title: string; difficulty: string; unlocked: boolean }>> {
  // For now, return a hardcoded list
  // In a real app, this would fetch from an API
  return [
    {
      id: 'level-1',
      title: 'Hello AI Blocks',
      difficulty: 'easy',
      unlocked: true,
    },
    {
      id: 'level-2', 
      title: 'Text Transformation',
      difficulty: 'easy',
      unlocked: false, // Would be unlocked after completing level-1
    },
    {
      id: 'level-3',
      title: 'Multi-step Processing',
      difficulty: 'medium',
      unlocked: false,
    }
  ];
}

/**
 * Save level progress (in a real app this would persist to backend)
 */
export function saveLevelProgress(levelId: string, score: number, stars: number, completed: boolean): void {
  const progress = {
    levelId,
    score,
    stars,
    completed,
    timestamp: Date.now(),
  };
  
  // Save to localStorage for now
  const key = `ai-blocks-progress-${levelId}`;
  localStorage.setItem(key, JSON.stringify(progress));
  
  console.log(`Saved progress for ${levelId}:`, progress);
}

/**
 * Load level progress
 */
export function loadLevelProgress(levelId: string): { score: number; stars: number; completed: boolean } | null {
  try {
    const key = `ai-blocks-progress-${levelId}`;
    const saved = localStorage.getItem(key);
    if (!saved) return null;
    
    return JSON.parse(saved);
  } catch (error) {
    console.warn(`Failed to load progress for ${levelId}:`, error);
    return null;
  }
} 