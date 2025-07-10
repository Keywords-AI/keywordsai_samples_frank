// src/engine/runner.ts
/**
 * Graph runner - executes the graph in topological order and emits execution traces
 * This is the core execution engine that processes the workflow
 */

import { 
  Graph, 
  ExecutionTrace, 
  ExecutionResult, 
  ExecutionContext,
  topologicalSort,
  getInputNodes,
  validateGraph 
} from "./graph";
import { blockRegistry } from "./blocks";

export interface RunnerOptions {
  /** Callback for live trace updates */
  onProgress?: (nodeId: string, progress: number) => void;
  
  /** Callback for each execution result */
  onResult?: (result: ExecutionResult) => void;
  
  /** Maximum execution time in milliseconds */
  timeout?: number;
  
  /** Whether to continue execution after errors */
  continueOnError?: boolean;
}

export class GraphRunner {
  private isRunning = false;
  private shouldStop = false;

  /**
   * Execute a graph and return the complete execution trace
   */
  async run(graph: Graph, options: RunnerOptions = {}): Promise<ExecutionTrace> {
    if (this.isRunning) {
      throw new Error("Runner is already executing a graph");
    }

    this.isRunning = true;
    this.shouldStop = false;

    const startTime = Date.now();
    const results: ExecutionResult[] = [];
    let totalTokens = 0;
    let totalApiCalls = 0;
    let success = true;
    let error: string | undefined;

    try {
      // Validate the graph first
      const validation = validateGraph(graph);
      if (!validation.valid) {
        throw new Error(`Graph validation failed: ${validation.errors.join(', ')}`);
      }

      // Get execution order
      const executionOrder = topologicalSort(graph);
      const nodeOutputs = new Map<string, any>();
      
      // Track progress
      const totalNodes = executionOrder.length;
      let completedNodes = 0;

      // Execute each node in order
      for (const nodeId of executionOrder) {
        if (this.shouldStop) {
          throw new Error("Execution stopped by user");
        }

        const node = graph.nodes.find(n => n.id === nodeId);
        if (!node) {
          throw new Error(`Node not found: ${nodeId}`);
        }

        // Get the block implementation
        const block = blockRegistry.get(node.type);
        if (!block) {
          throw new Error(`Unknown block type: ${node.type}`);
        }

        try {
          // Prepare input from connected nodes
          const inputNodes = getInputNodes(graph, nodeId);
          let nodeInput: any = null;

          if (inputNodes.length === 1) {
            // Single input
            nodeInput = nodeOutputs.get(inputNodes[0]);
          } else if (inputNodes.length > 1) {
            // Multiple inputs - combine into object
            nodeInput = {};
            inputNodes.forEach((inputNodeId, index) => {
              const inputEdge = graph.edges.find(e => e.source === inputNodeId && e.target === nodeId);
              const handleId = inputEdge?.targetHandle || `input${index + 1}`;
              nodeInput[handleId] = nodeOutputs.get(inputNodeId);
            });
          }

          // Create execution context
          const context: ExecutionContext = {
            nodeId,
            input: nodeInput,
            timestamp: Date.now(),
            metadata: {
              nodeType: node.type,
              position: node.position,
            }
          };

          // Execute the block
          const result = await this.executeWithTimeout(
            () => block.execute(context),
            options.timeout || 30000
          );

          // Store the output for downstream nodes
          nodeOutputs.set(nodeId, result.output);

          // Update counters
          if (result.metadata.tokens) {
            totalTokens += result.metadata.tokens;
          }
          if (result.metadata.apiCalls) {
            totalApiCalls += result.metadata.apiCalls;
          }

          results.push(result);

          // Notify progress
          completedNodes++;
          const progress = (completedNodes / totalNodes) * 100;
          options.onProgress?.(nodeId, progress);
          options.onResult?.(result);

          // Check for execution error
          if (result.metadata.error) {
            if (!options.continueOnError) {
              throw new Error(`Block execution failed in ${nodeId}: ${result.metadata.error}`);
            } else {
              success = false;
              error = result.metadata.error;
            }
          }

        } catch (blockError) {
          const errorMessage = blockError instanceof Error ? blockError.message : 'Unknown error';
          
          // Create error result
          const errorResult: ExecutionResult = {
            nodeId,
            input: nodeOutputs.get(nodeId) || null,
            output: null,
            metadata: {
              timestamp: Date.now(),
              duration: 0,
              error: errorMessage,
            }
          };

          results.push(errorResult);
          options.onResult?.(errorResult);

          if (!options.continueOnError) {
            throw new Error(`Execution failed at node ${nodeId}: ${errorMessage}`);
          } else {
            success = false;
            error = errorMessage;
          }
        }
      }

    } catch (runError) {
      success = false;
      error = runError instanceof Error ? runError.message : 'Unknown execution error';
    } finally {
      this.isRunning = false;
    }

    const trace: ExecutionTrace = {
      results,
      totalTokens,
      totalApiCalls,
      totalDuration: Date.now() - startTime,
      success,
      error,
    };

    return trace;
  }

  /**
   * Stop the current execution
   */
  stop(): void {
    this.shouldStop = true;
  }

  /**
   * Check if the runner is currently executing
   */
  get running(): boolean {
    return this.isRunning;
  }

  /**
   * Execute a function with a timeout
   */
  private async executeWithTimeout<T>(
    fn: () => Promise<T>,
    timeoutMs: number
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Execution timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      fn()
        .then(result => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch(error => {
          clearTimeout(timer);
          reject(error);
        });
    });
  }
}

// Export singleton instance
export const graphRunner = new GraphRunner(); 