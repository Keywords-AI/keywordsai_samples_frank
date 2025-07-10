// src/store/graphStore.ts
/**
 * Graph store manages the current graph state and provides undo/redo functionality
 * This store bridges between React Flow and our internal graph representation
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { Graph, GraphNode, GraphEdge, validateGraph } from "@/engine/graph";
import { v4 as uuid } from "uuid";

// Convert between React Flow types and our internal types
export interface ReactFlowNode extends GraphNode {
  // React Flow specific properties
  selected?: boolean;
  dragging?: boolean;
}

export interface ReactFlowEdge extends GraphEdge {
  // React Flow specific properties
  selected?: boolean;
  animated?: boolean;
}

export interface GraphHistory {
  past: Graph[];
  present: Graph;
  future: Graph[];
}

export interface GraphState {
  // Current graph state
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
  
  // History for undo/redo
  history: GraphHistory;
  canUndo: boolean;
  canRedo: boolean;
  
  // Validation state
  isValid: boolean;
  validationErrors: string[];
  
  // Actions
  setGraph: (graph: Graph) => void;
  addNode: (node: Omit<GraphNode, 'id'>) => void;
  updateNode: (id: string, updates: Partial<GraphNode>) => void;
  deleteNode: (id: string) => void;
  
  addEdge: (edge: Omit<GraphEdge, 'id'>) => void;
  updateEdge: (id: string, updates: Partial<GraphEdge>) => void;
  deleteEdge: (id: string) => void;
  
  // History actions
  undo: () => void;
  redo: () => void;
  pushToHistory: () => void;
  
  // Utility actions
  validateCurrentGraph: () => void;
  exportGraph: () => Graph;
  importGraph: (graph: Graph) => void;
  clearGraph: () => void;
}

const initialGraph: Graph = {
  nodes: [
    {
      id: uuid(),
      type: "userInput",
      data: { label: "User Input" },
      position: { x: 300, y: 200 }
    }
  ],
  edges: []
};

const createHistory = (graph: Graph): GraphHistory => ({
  past: [],
  present: graph,
  future: []
});

export const useGraphStore = create<GraphState>()(
  subscribeWithSelector((set, get) => ({
    // Initialize with default graph
    nodes: initialGraph.nodes as ReactFlowNode[],
    edges: initialGraph.edges as ReactFlowEdge[],
    
    history: createHistory(initialGraph),
    canUndo: false,
    canRedo: false,
    
    isValid: true,
    validationErrors: [],

    setGraph: (graph: Graph) => {
      const validation = validateGraph(graph);
      set({
        nodes: graph.nodes as ReactFlowNode[],
        edges: graph.edges as ReactFlowEdge[],
        isValid: validation.valid,
        validationErrors: validation.errors,
      });
    },

    addNode: (nodeData) => {
      const newNode: ReactFlowNode = {
        ...nodeData,
        id: uuid(),
      };
      
      const { nodes, edges } = get();
      const newNodes = [...nodes, newNode];
      
      get().pushToHistory();
      set({ nodes: newNodes });
      get().validateCurrentGraph();
    },

    updateNode: (id, updates) => {
      const { nodes } = get();
      const newNodes = nodes.map(node => 
        node.id === id ? { ...node, ...updates } : node
      );
      
      get().pushToHistory();
      set({ nodes: newNodes });
      get().validateCurrentGraph();
    },

    deleteNode: (id) => {
      const { nodes, edges } = get();
      const newNodes = nodes.filter(node => node.id !== id);
      const newEdges = edges.filter(edge => 
        edge.source !== id && edge.target !== id
      );
      
      get().pushToHistory();
      set({ nodes: newNodes, edges: newEdges });
      get().validateCurrentGraph();
    },

    addEdge: (edgeData) => {
      const newEdge: ReactFlowEdge = {
        ...edgeData,
        id: uuid(),
      };
      
      const { edges } = get();
      const newEdges = [...edges, newEdge];
      
      get().pushToHistory();
      set({ edges: newEdges });
      get().validateCurrentGraph();
    },

    updateEdge: (id, updates) => {
      const { edges } = get();
      const newEdges = edges.map(edge => 
        edge.id === id ? { ...edge, ...updates } : edge
      );
      
      get().pushToHistory();
      set({ edges: newEdges });
      get().validateCurrentGraph();
    },

    deleteEdge: (id) => {
      const { edges } = get();
      const newEdges = edges.filter(edge => edge.id !== id);
      
      get().pushToHistory();
      set({ edges: newEdges });
      get().validateCurrentGraph();
    },

    pushToHistory: () => {
      const { history, nodes, edges } = get();
      const currentGraph = { nodes, edges };
      
      const newHistory: GraphHistory = {
        past: [...history.past, history.present],
        present: currentGraph,
        future: [] // Clear future when new action is taken
      };
      
      set({
        history: newHistory,
        canUndo: newHistory.past.length > 0,
        canRedo: false,
      });
    },

    undo: () => {
      const { history } = get();
      if (history.past.length === 0) return;
      
      const newPresent = history.past[history.past.length - 1];
      const newPast = history.past.slice(0, -1);
      
      const newHistory: GraphHistory = {
        past: newPast,
        present: newPresent,
        future: [history.present, ...history.future]
      };
      
      set({
        nodes: newPresent.nodes as ReactFlowNode[],
        edges: newPresent.edges as ReactFlowEdge[],
        history: newHistory,
        canUndo: newPast.length > 0,
        canRedo: true,
      });
      
      get().validateCurrentGraph();
    },

    redo: () => {
      const { history } = get();
      if (history.future.length === 0) return;
      
      const newPresent = history.future[0];
      const newFuture = history.future.slice(1);
      
      const newHistory: GraphHistory = {
        past: [...history.past, history.present],
        present: newPresent,
        future: newFuture
      };
      
      set({
        nodes: newPresent.nodes as ReactFlowNode[],
        edges: newPresent.edges as ReactFlowEdge[],
        history: newHistory,
        canUndo: true,
        canRedo: newFuture.length > 0,
      });
      
      get().validateCurrentGraph();
    },

    validateCurrentGraph: () => {
      const { nodes, edges } = get();
      const graph = { nodes, edges };
      const validation = validateGraph(graph);
      
      set({
        isValid: validation.valid,
        validationErrors: validation.errors,
      });
    },

    exportGraph: (): Graph => {
      const { nodes, edges } = get();
      return { nodes, edges };
    },

    importGraph: (graph: Graph) => {
      get().pushToHistory();
      get().setGraph(graph);
    },

    clearGraph: () => {
      get().pushToHistory();
      set({
        nodes: [],
        edges: [],
      });
      get().validateCurrentGraph();
    },
  }))
);
