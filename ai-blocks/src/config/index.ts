// src/config/index.ts
/**
 * Centralized configuration for AI Blocks application
 * Eliminates hardcoded values and provides type-safe configuration
 */

// Re-export configuration modules
export { LEVEL_CONFIGS, getLevelConfig, getAvailableLevels, type LevelConfig } from './levels';
export { BLOCK_CONFIGS, getBlockConfig, getAllBlocks, type BlockConfig } from './blocks';

// Import for internal use
import { LEVEL_CONFIGS } from './levels';
import { BLOCK_CONFIGS } from './blocks';

export interface UIConfig {
  layout: {
    topBarHeight: string;
    toolboxWidth: string;
    traceConsoleHeight: string;
    panelBorderRadius: string;
  };
  animation: {
    transitionDuration: string;
    hoverScale: string;
    dragSensitivity: number;
  };
  breakpoints: {
    mobile: string;
    tablet: string;
    desktop: string;
  };
}

export interface ToolboxConfig {
  categories: {
    [key: string]: {
      name: string;
      icon: string;
      description: string;
      defaultExpanded: boolean;
    };
  };
  defaultExpandedCategories: string[];
}

export const APP_CONFIG = {
  // Application metadata
  app: {
    name: 'Agent Blocks',
    tagline: 'Visual Workflow Builder for AI Agents',
    description: 'Design and prototype your AI agent workflows with our intuitive visual programming platform.',
    version: '1.0.0'
  },

  // Level configurations (using centralized system)
  levels: LEVEL_CONFIGS,

  // Block configurations (using centralized system)
  blocks: BLOCK_CONFIGS,

  // UI Layout configuration
  ui: {
    layout: {
      topBarHeight: 'h-16',
      toolboxWidth: 'w-64',
      traceConsoleHeight: 'h-80',
      panelBorderRadius: 'rounded-lg'
    },
    animation: {
      transitionDuration: 'duration-200',
      hoverScale: 'hover:scale-[1.02]',
      dragSensitivity: 0.2
    },
    breakpoints: {
      mobile: 'sm',
      tablet: 'md',
      desktop: 'lg'
    }
  } as UIConfig,

  // Toolbox configuration
  toolbox: {
    categories: {
      input: {
        name: 'Input',
        icon: '📥',
        description: 'Data input and user interaction blocks',
        defaultExpanded: true
      },
      transform: {
        name: 'Transform',
        icon: '🔄',
        description: 'Data transformation and processing blocks',
        defaultExpanded: false
      },
      llm: {
        name: 'AI Models',
        icon: '🤖',
        description: 'Large language model and AI processing blocks',
        defaultExpanded: true
      },
      tool: {
        name: 'Tools',
        icon: '🔧',
        description: 'External tools and API integrations',
        defaultExpanded: false
      },
      output: {
        name: 'Output',
        icon: '📤',
        description: 'Data output and result display blocks',
        defaultExpanded: false
      },
      control: {
        name: 'Control',
        icon: '🎛️',
        description: 'Flow control and logic blocks',
        defaultExpanded: false
      }
    },
    defaultExpandedCategories: ['input', 'llm']
  } as ToolboxConfig
} as const;

// Routes configuration
export const ROUTES = {
  home: '/',
  sandbox: '/sandbox',
  level: (id: string | number) => `/level${id}`,
  settings: '/settings'
} as const;

// API configuration
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
  timeout: 30000,
  retries: 3
} as const;

// Export types for use in components
export type AppConfig = typeof APP_CONFIG;
export type LevelId = keyof typeof APP_CONFIG.levels;
export type CategoryId = keyof typeof APP_CONFIG.toolbox.categories;