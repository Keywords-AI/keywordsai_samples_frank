// src/store/runStore.ts
/**
 * Run store manages execution state, traces, and evaluation results
 * This store tracks the runtime state of graph execution and test results
 */

import { create } from "zustand";
import { ExecutionTrace, ExecutionResult } from "@/engine/graph";
import { ValidationResult } from "@/levels/types";

export interface TestResult {
  id: string;
  name: string;
  passed: boolean;
  message: string;
  nodeId?: string; // Which node caused the failure
}

export interface BudgetConstraint {
  type: 'tokens' | 'apiCalls' | 'time';
  limit: number;
  current: number;
  exceeded: boolean;
}

export interface EvaluationResult {
  passed: boolean;
  score: number; // 0-100
  tests: TestResult[];
  budgets: BudgetConstraint[];
  observabilityScore: number; // 0-100, how well they traced/debugged
}

export interface RunState {
  // Execution state
  isRunning: boolean;
  currentNodeId: string | null;
  progress: number; // 0-100
  
  // Trace data
  trace: ExecutionTrace | null;
  liveResults: ExecutionResult[]; // Results as they come in
  
  // Evaluation results
  evaluation: EvaluationResult | null;
  
  // Animation state
  showSuccessAnimation: boolean;
  
  // Success modal state
  showSuccessModal: boolean;
  validationResult: ValidationResult | null;
  
  // UI state for trace console
  selectedTraceIndex: number | null;
  showOnlyErrors: boolean;
  
  // Actions
  startRun: () => void;
  updateProgress: (nodeId: string, progress: number) => void;
  addResult: (result: ExecutionResult) => void;
  finishRun: (trace: ExecutionTrace) => void;
  setEvaluation: (evaluation: EvaluationResult) => void;
  reset: () => void;
  setShowSuccessAnimation: (show: boolean) => void;
  setShowSuccessModal: (show: boolean, validationResult?: ValidationResult) => void;
  
  // Trace console actions
  selectTrace: (index: number | null) => void;
  toggleErrorFilter: () => void;
}

const initialState = {
  isRunning: false,
  currentNodeId: null,
  progress: 0,
  trace: null,
  liveResults: [],
  evaluation: null,
  selectedTraceIndex: null,
  showOnlyErrors: false,
  showSuccessAnimation: false,
  showSuccessModal: false,
  validationResult: null,
};

export const useRunStore = create<RunState>((set, get) => ({
  ...initialState,

  startRun: () => {
    set({
      isRunning: true,
      currentNodeId: null,
      progress: 0,
      trace: null,
      liveResults: [],
      evaluation: null,
      selectedTraceIndex: null,
    });
  },

  updateProgress: (nodeId: string, progress: number) => {
    set({
      currentNodeId: nodeId,
      progress: Math.min(100, Math.max(0, progress)),
    });
  },

  addResult: (result: ExecutionResult) => {
    const { liveResults } = get();
    set({
      liveResults: [...liveResults, result],
    });
  },

  finishRun: (trace: ExecutionTrace) => {
    set({
      isRunning: false,
      currentNodeId: null,
      progress: 100,
      trace,
      liveResults: trace.results,
    });
  },

  setShowSuccessAnimation: (show: boolean) => {
    set({ showSuccessAnimation: show });
  },

  setShowSuccessModal: (show: boolean, validationResult?: ValidationResult) => {
    set({ 
      showSuccessModal: show,
      validationResult: validationResult || null 
    });
  },

  setEvaluation: (evaluation: EvaluationResult) => {
    set({ evaluation });
  },

  reset: () => {
    set(initialState);
  },

  selectTrace: (index: number | null) => {
    set({ selectedTraceIndex: index });
  },

  toggleErrorFilter: () => {
    set(state => ({ showOnlyErrors: !state.showOnlyErrors }));
  },
})); 