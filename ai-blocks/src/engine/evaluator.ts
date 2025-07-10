// src/engine/evaluator.ts
/**
 * Evaluator - checks tests and budgets to determine if the player passed the level
 * This module provides Jest-style assertions and scoring logic
 */

import { ExecutionTrace, ExecutionResult } from "./graph";
import { 
  TestResult, 
  BudgetConstraint, 
  EvaluationResult 
} from "@/store/runStore";
import { LevelMeta } from "@/store/uiStore";

export interface TestCase {
  id: string;
  name: string;
  description: string;
  assertion: (trace: ExecutionTrace, results: ExecutionResult[]) => boolean | string;
  points: number; // How many points this test is worth
  category: 'functionality' | 'performance' | 'quality';
}

export interface LevelDefinition extends LevelMeta {
  tests: TestCase[];
  starThresholds: {
    oneStar: number;  // Minimum score for 1 star
    twoStar: number;  // Minimum score for 2 stars  
    threeStar: number; // Minimum score for 3 stars
  };
}

export class Evaluator {
  /**
   * Evaluate a completed execution trace against level requirements
   */
  evaluate(trace: ExecutionTrace, level: LevelDefinition): EvaluationResult {
    const testResults = this.runTests(trace, level.tests);
    const budgetConstraints = this.checkBudgets(trace, level);
    const observabilityScore = this.calculateObservabilityScore(trace, level);
    
    // Calculate overall score
    const { score, passed } = this.calculateScore(testResults, budgetConstraints, observabilityScore, level);
    
    return {
      passed,
      score,
      tests: testResults,
      budgets: budgetConstraints,
      observabilityScore,
    };
  }

  /**
   * Run all tests for a level
   */
  private runTests(trace: ExecutionTrace, tests: TestCase[]): TestResult[] {
    return tests.map(test => {
      try {
        const result = test.assertion(trace, trace.results);
        
        if (typeof result === 'boolean') {
          return {
            id: test.id,
            name: test.name,
            passed: result,
            message: result ? 'Test passed' : 'Test failed',
          };
        } else {
          // String result indicates failure with message
          return {
            id: test.id,
            name: test.name,
            passed: false,
            message: result,
            nodeId: this.findFailureNode(trace, result),
          };
        }
      } catch (error) {
        return {
          id: test.id,
          name: test.name,
          passed: false,
          message: error instanceof Error ? error.message : 'Test execution error',
        };
      }
    });
  }

  /**
   * Check budget constraints (tokens, API calls, time)
   */
  private checkBudgets(trace: ExecutionTrace, level: LevelDefinition): BudgetConstraint[] {
    const budgets: BudgetConstraint[] = [];

    // Token budget
    budgets.push({
      type: 'tokens',
      limit: level.targetTokens,
      current: trace.totalTokens,
      exceeded: trace.totalTokens > level.targetTokens,
    });

    // API calls budget
    budgets.push({
      type: 'apiCalls',
      limit: level.targetApiCalls,
      current: trace.totalApiCalls,
      exceeded: trace.totalApiCalls > level.targetApiCalls,
    });

    // Time budget (convert to seconds)
    const timeInSeconds = Math.ceil(trace.totalDuration / 1000);
    budgets.push({
      type: 'time',
      limit: level.targetTime,
      current: timeInSeconds,
      exceeded: timeInSeconds > level.targetTime,
    });

    return budgets;
  }

  /**
   * Calculate observability score based on how well the player debugged/traced
   */
  private calculateObservabilityScore(trace: ExecutionTrace, level: LevelDefinition): number {
    let score = 0;
    const maxScore = 100;

    // Base score for successful execution
    if (trace.success) {
      score += 30;
    }

    // Points for good error handling
    const errorResults = trace.results.filter(r => r.metadata.error);
    if (errorResults.length === 0) {
      score += 20; // No errors
    } else {
      // Partial credit for handling some errors
      const totalResults = trace.results.length;
      score += Math.max(0, 20 - (errorResults.length / totalResults) * 20);
    }

    // Points for efficient execution (fewer retries, good flow)
    const avgDuration = trace.totalDuration / trace.results.length;
    if (avgDuration < 1000) { // Less than 1 second per block
      score += 20;
    } else if (avgDuration < 3000) {
      score += 10;
    }

    // Points for following best practices (proper connections, reasonable parameters)
    const wellConnectedNodes = trace.results.filter(r => r.input !== null).length;
    const connectionScore = (wellConnectedNodes / trace.results.length) * 30;
    score += connectionScore;

    return Math.min(maxScore, Math.round(score));
  }

  /**
   * Calculate overall score and pass/fail status
   */
  private calculateScore(
    testResults: TestResult[], 
    budgets: BudgetConstraint[], 
    observabilityScore: number,
    level: LevelDefinition
  ): { score: number; passed: boolean } {
    // Calculate test score
    const passedTests = testResults.filter(t => t.passed);
    const totalTestPoints = level.tests.reduce((sum, test) => sum + test.points, 0);
    const earnedTestPoints = passedTests.reduce((sum, result) => {
      const test = level.tests.find(t => t.id === result.id);
      return sum + (test?.points || 0);
    }, 0);

    const testScore = totalTestPoints > 0 ? (earnedTestPoints / totalTestPoints) * 70 : 0; // 70% weight

    // Budget penalties
    const exceededBudgets = budgets.filter(b => b.exceeded).length;
    const budgetPenalty = exceededBudgets * 10; // 10 points per exceeded budget

    // Observability bonus (scaled to 30%)
    const observabilityBonus = (observabilityScore / 100) * 30;

    // Calculate final score
    const rawScore = testScore + observabilityBonus - budgetPenalty;
    const finalScore = Math.max(0, Math.min(100, Math.round(rawScore)));

    // Determine pass/fail
    const allCriticalTestsPassed = testResults
      .filter(t => level.tests.find(lt => lt.id === t.id)?.category === 'functionality')
      .every(t => t.passed);
    
    const passed = allCriticalTestsPassed && finalScore >= level.starThresholds.oneStar;

    return { score: finalScore, passed };
  }

  /**
   * Find which node likely caused a test failure
   */
  private findFailureNode(trace: ExecutionTrace, errorMessage: string): string | undefined {
    // Look for nodes with errors
    const errorNode = trace.results.find(r => r.metadata.error);
    if (errorNode) {
      return errorNode.nodeId;
    }

    // Look for the last successfully executed node
    const lastNode = trace.results[trace.results.length - 1];
    return lastNode?.nodeId;
  }

  /**
   * Create common test assertions
   */
  static createAssertions() {
    return {
      /** Check if output contains specific text */
      outputContains: (expectedText: string) => (trace: ExecutionTrace) => {
        const finalResult = trace.results[trace.results.length - 1];
        const output = finalResult?.output;
        if (typeof output !== 'string') {
          return `Expected string output, got ${typeof output}`;
        }
        return output.includes(expectedText) || `Output does not contain "${expectedText}"`;
      },

      /** Check if output matches exact value */
      outputEquals: (expectedValue: any) => (trace: ExecutionTrace) => {
        const finalResult = trace.results[trace.results.length - 1];
        const output = finalResult?.output;
        return JSON.stringify(output) === JSON.stringify(expectedValue) || 
               `Expected ${JSON.stringify(expectedValue)}, got ${JSON.stringify(output)}`;
      },

      /** Check if execution completed successfully */
      executionSucceeded: () => (trace: ExecutionTrace) => {
        return trace.success || `Execution failed: ${trace.error}`;
      },

      /** Check if specific node type was used */
      usesBlockType: (blockType: string) => (trace: ExecutionTrace) => {
        return trace.results.some(r => r.metadata.nodeType === blockType) ||
               `Workflow must include a ${blockType} block`;
      },

      /** Check token usage is under limit */
      tokenUsageUnder: (limit: number) => (trace: ExecutionTrace) => {
        return trace.totalTokens <= limit ||
               `Token usage ${trace.totalTokens} exceeds limit of ${limit}`;
      },
    };
  }
}

// Export singleton instance
export const evaluator = new Evaluator(); 