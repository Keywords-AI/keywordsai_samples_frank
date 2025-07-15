// src/config/blocks.ts
/**
 * Centralized block configuration
 * Defines all available blocks and their properties
 */

export interface BlockConfig {
  id: string;
  label: string;
  description: string;
  category: 'input' | 'transform' | 'llm' | 'output' | 'control' | 'tool';
  level: number;
  isEnabled: boolean;
  handles: {
    inputs: Array<{
      id: string;
      label: string;
      type: string;
      required: boolean;
    }>;
    outputs: Array<{
      id: string;
      label: string;
      type: string;
      required: boolean;
    }>;
  };
  hints: {
    inputHint: string;
    outputHint: string;
    usageExample: string;
  };
  ui: {
    color: string;
    icon?: string;
  };
}

export const BLOCK_CONFIGS: Record<string, BlockConfig> = {
  // Input Blocks
  userInput: {
    id: 'userInput',
    label: 'User Input',
    description: 'Start here! This is where users give instructions to your workflow.',
    category: 'input',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [],
      outputs: [{
        id: 'output',
        label: 'User Request',
        type: 'text',
        required: true
      }]
    },
    hints: {
      inputHint: '💭 No input needed - this is where the user types their request',
      outputHint: '📝 Outputs user\'s text request (like \'Schedule a meeting tomorrow\')',
      usageExample: 'Connect this to LLM Parse to analyze what the user wants'
    },
    ui: {
      color: 'bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100',
      icon: '📥'
    }
  },

  contextVariable: {
    id: 'contextVariable',
    label: 'Context Variable',
    description: 'Store important information that your workflow can use (like user preferences or settings).',
    category: 'input',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [],
      outputs: [{
        id: 'output',
        label: 'Stored Data',
        type: 'data',
        required: true
      }]
    },
    hints: {
      inputHint: '💾 No input needed - this stores pre-defined information',
      outputHint: '📋 Outputs stored data (like user preferences, API keys, or settings)',
      usageExample: 'Use this to provide your workflow with context about the user'
    },
    ui: {
      color: 'bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100',
      icon: '📥'
    }
  },

  // Transform Blocks
  contextMerge: {
    id: 'contextMerge',
    label: 'Context Merge',
    description: 'Smart combiner! This merges user input with stored context to create richer information.',
    category: 'transform',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [
        {
          id: 'userInput',
          label: 'User Input',
          type: 'text',
          required: true
        },
        {
          id: 'context',
          label: 'Context Data',
          type: 'data',
          required: true
        }
      ],
      outputs: [{
        id: 'output',
        label: 'Merged Data',
        type: 'data',
        required: true
      }]
    },
    hints: {
      inputHint: '🔀 Takes user input and context data',
      outputHint: '📊 Outputs enriched data combining both inputs',
      usageExample: 'Connect User Input and Context Variable to this block'
    },
    ui: {
      color: 'bg-purple-50 border-purple-200 text-purple-800 hover:bg-purple-100',
      icon: '🔄'
    }
  },

  // LLM Blocks
  llmParse: {
    id: 'llmParse',
    label: 'LLM Parse',
    description: 'The workflow analyzer! This analyzes text and understands what the user wants.',
    category: 'llm',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [{
        id: 'input',
        label: 'Text to Analyze',
        type: 'text',
        required: true
      }],
      outputs: [{
        id: 'output',
        label: 'AI Analysis',
        type: 'data',
        required: true
      }]
    },
    hints: {
      inputHint: '📝 Takes user text (like \'Schedule a meeting tomorrow\')',
      outputHint: '🧠 Outputs AI analysis with intent, entities, and requirements',
      usageExample: 'Connect User Input → LLM Parse to understand what users want'
    },
    ui: {
      color: 'bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100',
      icon: '🤖'
    }
  },

  llmSuggestTime: {
    id: 'llmSuggestTime',
    label: 'LLM Suggest Time',
    description: 'Time wizard! This suggests the best meeting times based on availability and preferences.',
    category: 'llm',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [{
        id: 'input',
        label: 'Calendar Data',
        type: 'data',
        required: true
      }],
      outputs: [{
        id: 'output',
        label: 'Time Suggestions',
        type: 'data',
        required: true
      }]
    },
    hints: {
      inputHint: '📅 Takes calendar availability data',
      outputHint: '⏰ Outputs smart time suggestions avoiding conflicts',
      usageExample: 'Connect Google Calendar Get → LLM Suggest Time for smart scheduling'
    },
    ui: {
      color: 'bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100',
      icon: '🤖'
    }
  },

  // Tool Blocks
  googleCalendarGet: {
    id: 'googleCalendarGet',
    label: 'Google Calendar Get',
    description: 'Calendar checker! This looks at your existing calendar to find conflicts and availability.',
    category: 'tool',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [{
        id: 'input',
        label: 'Query Parameters',
        type: 'data',
        required: true
      }],
      outputs: [{
        id: 'output',
        label: 'Calendar Data',
        type: 'data',
        required: true
      }]
    },
    hints: {
      inputHint: '🔍 Takes search parameters for calendar events',
      outputHint: '📅 Outputs existing calendar events and availability',
      usageExample: 'Connect LLM Parse → Google Calendar Get to check for conflicts'
    },
    ui: {
      color: 'bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100',
      icon: '🔧'
    }
  },

  googleCalendarSchedule: {
    id: 'googleCalendarSchedule',
    label: 'Google Calendar Schedule',
    description: 'Event creator! This actually creates the meeting in your calendar.',
    category: 'tool',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [{
        id: 'input',
        label: 'Event Details',
        type: 'data',
        required: true
      }],
      outputs: [{
        id: 'output',
        label: 'Created Event',
        type: 'data',
        required: true
      }]
    },
    hints: {
      inputHint: '📝 Takes event details (time, title, participants)',
      outputHint: '✅ Outputs confirmation of created calendar event',
      usageExample: 'Connect LLM Suggest Time → Google Calendar Schedule to book meetings'
    },
    ui: {
      color: 'bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100',
      icon: '🔧'
    }
  },

  // Output Blocks
  userOutput: {
    id: 'userOutput',
    label: 'User Output',
    description: 'The final result! This shows the completed workflow result to the user.',
    category: 'output',
    level: 1,
    isEnabled: true,
    handles: {
      inputs: [{
        id: 'input',
        label: 'Final Result',
        type: 'data',
        required: true
      }],
      outputs: []
    },
    hints: {
      inputHint: '📤 Takes the final workflow result',
      outputHint: '👤 Displays result to user (no further output)',
      usageExample: 'Connect the final step of your workflow to this block'
    },
    ui: {
      color: 'bg-rose-50 border-rose-200 text-rose-800 hover:bg-rose-100',
      icon: '📤'
    }
  }
};

// Category configuration
export const BLOCK_CATEGORIES = {
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
};

// Helper functions
export function getBlockConfig(blockId: string): BlockConfig | undefined {
  return BLOCK_CONFIGS[blockId];
}

export function getBlocksByCategory(category: keyof typeof BLOCK_CATEGORIES): BlockConfig[] {
  return Object.values(BLOCK_CONFIGS).filter(
    block => block.category === category && block.isEnabled
  );
}

export function getAllBlocks(): BlockConfig[] {
  return Object.values(BLOCK_CONFIGS).filter(block => block.isEnabled);
}

export function getBlocksByLevel(level: number): BlockConfig[] {
  return Object.values(BLOCK_CONFIGS).filter(
    block => block.level <= level && block.isEnabled
  );
} 