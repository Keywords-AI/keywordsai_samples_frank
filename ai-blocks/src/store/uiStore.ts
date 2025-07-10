// src/store/uiStore.ts
/**
 * UI store manages panel visibility, selections, and modal states
 * This store handles all UI-related state that's not specific to graph or execution
 */

import { create } from "zustand";

export interface LevelMeta {
  id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
  targetTokens: number;
  targetApiCalls: number;
  targetTime: number; // seconds
  observabilityTarget: number; // percentage
}

export interface UIState {
  // Panel visibility
  toolboxOpen: boolean;
  traceConsoleOpen: boolean;
  
  // Current selections
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  
  // Modal states
  showLevelModal: boolean;
  showWinModal: boolean;
  showSettingsModal: boolean;
  
  // Level management
  currentLevel: LevelMeta | null;
  availableLevels: LevelMeta[];
  
  // Theme and preferences
  theme: 'light' | 'dark' | 'auto';
  debugMode: boolean;
  
  // Actions
  togglePanel: (panel: 'toolbox' | 'traceConsole') => void;
  selectNode: (nodeId: string | null) => void;
  selectEdge: (edgeId: string | null) => void;
  
  // Modal actions
  showModal: (modal: 'level' | 'win' | 'settings') => void;
  hideModal: (modal: 'level' | 'win' | 'settings') => void;
  hideAllModals: () => void;
  
  // Level actions
  setCurrentLevel: (level: LevelMeta) => void;
  loadAvailableLevels: (levels: LevelMeta[]) => void;
  
  // Settings actions
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  toggleDebugMode: () => void;
}

const initialState = {
  // Panel visibility - start with toolbox open
  toolboxOpen: true,
  traceConsoleOpen: false,
  
  // Selections
  selectedNodeId: null,
  selectedEdgeId: null,
  
  // Modals
  showLevelModal: false,
  showWinModal: false,
  showSettingsModal: false,
  
  // Level management
  currentLevel: null,
  availableLevels: [],
  
  // Theme and preferences
  theme: 'auto' as const,
  debugMode: false,
};

export const useUIStore = create<UIState>((set, get) => ({
  ...initialState,

  togglePanel: (panel) => {
    set(state => ({
      [`${panel}Open`]: !state[`${panel}Open` as keyof typeof state]
    }));
  },

  selectNode: (nodeId) => {
    set({
      selectedNodeId: nodeId,
      selectedEdgeId: null, // Clear edge selection when selecting node
    });
  },

  selectEdge: (edgeId) => {
    set({
      selectedEdgeId: edgeId,
      selectedNodeId: null, // Clear node selection when selecting edge
    });
  },

  showModal: (modal) => {
    set({
      [`show${modal.charAt(0).toUpperCase() + modal.slice(1)}Modal`]: true
    });
  },

  hideModal: (modal) => {
    set({
      [`show${modal.charAt(0).toUpperCase() + modal.slice(1)}Modal`]: false
    });
  },

  hideAllModals: () => {
    set({
      showLevelModal: false,
      showWinModal: false,
      showSettingsModal: false,
    });
  },

  setCurrentLevel: (level) => {
    set({ currentLevel: level });
  },

  loadAvailableLevels: (levels) => {
    set({ availableLevels: levels });
  },

  setTheme: (theme) => {
    set({ theme });
  },

  toggleDebugMode: () => {
    set(state => ({ debugMode: !state.debugMode }));
  },
})); 