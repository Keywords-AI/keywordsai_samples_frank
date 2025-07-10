// src/engine/graph.ts
/**
 * Core graph types and utilities for AI Blocks
 * This module defines the fundamental building blocks of the graph system
 */

export interface NodeData {
  label: string;
  params?: Record<string, any>;
  [key: string]: any;
}

export interface GraphNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: NodeData;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Execution context passed between blocks during graph execution
 */
export interface ExecutionContext {
  nodeId: string;
  input: any;
  timestamp: number;
  metadata?: Record<string, any>;
}

/**
 * Result of executing a single block
 */
export interface ExecutionResult {
  nodeId: string;
  input: any;
  output: any;
  metadata: {
    timestamp: number;
    duration: number;
    tokens?: number;
    apiCalls?: number;
    error?: string;
    [key: string]: any;
  };
}

/**
 * Complete trace of a graph execution
 */
export interface ExecutionTrace {
  results: ExecutionResult[];
  totalTokens: number;
  totalApiCalls: number;
  totalDuration: number;
  success: boolean;
  error?: string;
}

/**
 * Performs topological sort on the graph to determine execution order
 * @param graph The graph to sort
 * @returns Array of node IDs in execution order
 */
export function topologicalSort(graph: Graph): string[] {
  const { nodes, edges } = graph;
  const visited = new Set<string>();
  const visiting = new Set<string>();
  const result: string[] = [];

  // Build adjacency list for dependencies
  const dependencies = new Map<string, string[]>();
  const dependents = new Map<string, string[]>();

  // Initialize maps
  nodes.forEach(node => {
    dependencies.set(node.id, []);
    dependents.set(node.id, []);
  });

  // Build dependency relationships
  edges.forEach(edge => {
    const deps = dependencies.get(edge.target) || [];
    deps.push(edge.source);
    dependencies.set(edge.target, deps);

    const depts = dependents.get(edge.source) || [];
    depts.push(edge.target);
    dependents.set(edge.source, depts);
  });

  function visit(nodeId: string): void {
    if (visiting.has(nodeId)) {
      throw new Error(`Circular dependency detected involving node: ${nodeId}`);
    }
    if (visited.has(nodeId)) {
      return;
    }

    visiting.add(nodeId);

    // Visit all dependencies first
    const deps = dependencies.get(nodeId) || [];
    deps.forEach(depId => visit(depId));

    visiting.delete(nodeId);
    visited.add(nodeId);
    result.push(nodeId);
  }

  // Visit all nodes
  nodes.forEach(node => {
    if (!visited.has(node.id)) {
      visit(node.id);
    }
  });

  return result;
}

/**
 * Gets all input nodes for a given node
 * @param graph The graph
 * @param nodeId The target node ID
 * @returns Array of input node IDs
 */
export function getInputNodes(graph: Graph, nodeId: string): string[] {
  return graph.edges
    .filter(edge => edge.target === nodeId)
    .map(edge => edge.source);
}

/**
 * Gets all output nodes for a given node
 * @param graph The graph
 * @param nodeId The source node ID
 * @returns Array of output node IDs
 */
export function getOutputNodes(graph: Graph, nodeId: string): string[] {
  return graph.edges
    .filter(edge => edge.source === nodeId)
    .map(edge => edge.target);
}

/**
 * Validates that a graph is properly connected and executable
 * @param graph The graph to validate
 * @returns Validation result with any errors
 */
export function validateGraph(graph: Graph): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  try {
    // Check for circular dependencies
    topologicalSort(graph);
  } catch (error) {
    errors.push(`Graph validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  // Check for disconnected components
  const nodeIds = new Set(graph.nodes.map(n => n.id));
  const connectedNodes = new Set<string>();

  graph.edges.forEach(edge => {
    if (!nodeIds.has(edge.source)) {
      errors.push(`Edge references non-existent source node: ${edge.source}`);
    }
    if (!nodeIds.has(edge.target)) {
      errors.push(`Edge references non-existent target node: ${edge.target}`);
    }
    connectedNodes.add(edge.source);
    connectedNodes.add(edge.target);
  });

  return {
    valid: errors.length === 0,
    errors
  };
} 