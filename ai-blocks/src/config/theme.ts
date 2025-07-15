// src/config/theme.ts
/**
 * Comprehensive theme system for consistent styling
 */

export const THEME = {
  // Color palette
  colors: {
    // Primary colors
    primary: {
      50: 'bg-blue-50',
      100: 'bg-blue-100',
      500: 'bg-blue-500',
      600: 'bg-blue-600',
      700: 'bg-blue-700'
    },
    
    // Semantic colors
    success: {
      50: 'bg-green-50',
      100: 'bg-green-100',
      500: 'bg-green-500',
      600: 'bg-green-600',
      text: 'text-green-800'
    },
    
    error: {
      50: 'bg-red-50',
      100: 'bg-red-100',
      500: 'bg-red-500',
      600: 'bg-red-600',
      text: 'text-red-600'
    },
    
    warning: {
      50: 'bg-amber-50',
      100: 'bg-amber-100',
      500: 'bg-amber-500',
      text: 'text-amber-800'
    },
    
    // Neutral colors
    gray: {
      50: 'bg-gray-50',
      100: 'bg-gray-100',
      200: 'bg-gray-200',
      300: 'bg-gray-300',
      500: 'bg-gray-500',
      600: 'bg-gray-600',
      700: 'bg-gray-700',
      800: 'bg-gray-800',
      900: 'bg-gray-900'
    },
    
    // Text colors
    text: {
      primary: 'text-gray-900',
      secondary: 'text-gray-600',
      muted: 'text-gray-500',
      inverse: 'text-white'
    },
    
    // Border colors
    border: {
      default: 'border-gray-200',
      hover: 'border-gray-400',
      focus: 'border-blue-500'
    }
  },
  
  // Category-specific colors
  categories: {
    input: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      hover: 'hover:bg-blue-100'
    },
    transform: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-800',
      hover: 'hover:bg-purple-100'
    },
    llm: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-800',
      hover: 'hover:bg-emerald-100'
    },
    tool: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-800',
      hover: 'hover:bg-amber-100'
    },
    output: {
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-800',
      hover: 'hover:bg-rose-100'
    },
    control: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      text: 'text-gray-800',
      hover: 'hover:bg-gray-100'
    }
  },
  
  // Spacing
  spacing: {
    xs: 'p-1',
    sm: 'p-2',
    md: 'p-3',
    lg: 'p-4',
    xl: 'p-6',
    '2xl': 'p-8'
  },
  
  // Border radius
  borderRadius: {
    sm: 'rounded',
    md: 'rounded-lg',
    lg: 'rounded-xl',
    full: 'rounded-full'
  },
  
  // Shadows
  shadows: {
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    hover: 'hover:shadow-md'
  },
  
  // Typography
  typography: {
    heading: {
      h1: 'text-6xl font-bold tracking-tight',
      h2: 'text-4xl font-semibold',
      h3: 'text-3xl font-semibold',
      h4: 'text-xl font-bold',
      h5: 'text-lg font-semibold'
    },
    body: {
      large: 'text-lg',
      base: 'text-base',
      small: 'text-sm',
      xs: 'text-xs'
    },
    weight: {
      normal: 'font-normal',
      medium: 'font-medium',
      semibold: 'font-semibold',
      bold: 'font-bold'
    }
  },
  
  // Component-specific styles
  components: {
    button: {
      base: 'px-4 py-2 rounded font-medium transition-colors',
      primary: 'bg-blue-500 text-white hover:bg-blue-600',
      secondary: 'bg-gray-100 text-gray-600 hover:bg-gray-200',
      success: 'bg-green-500 text-white hover:bg-green-600',
      danger: 'bg-red-500 text-white hover:bg-red-600',
      disabled: 'bg-gray-600 text-gray-400 cursor-not-allowed'
    },
    
    panel: {
      base: 'bg-white border border-gray-200 rounded-lg',
      header: 'p-3 border-b border-gray-200',
      content: 'p-4',
      footer: 'p-3 border-t border-gray-200'
    },
    
    modal: {
      overlay: 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50',
      content: 'bg-white rounded-lg shadow-lg max-w-md w-full mx-4',
      header: 'p-6 border-b border-gray-200',
      body: 'p-6',
      footer: 'p-6 border-t border-gray-200 flex justify-end space-x-2'
    },
    
    badge: {
      base: 'px-3 py-1 rounded-full text-xs font-medium',
      primary: 'bg-blue-100 text-blue-700',
      success: 'bg-green-100 text-green-700',
      warning: 'bg-amber-100 text-amber-700',
      error: 'bg-red-100 text-red-700',
      gray: 'bg-gray-100 text-gray-700'
    }
  },
  
  // Transitions and animations
  transitions: {
    default: 'transition-all duration-200',
    fast: 'transition-all duration-100',
    slow: 'transition-all duration-300',
    transform: 'transform transition-transform duration-200'
  }
} as const;

// Utility functions for theme usage
export const getThemeClass = (path: string) => {
  const keys = path.split('.');
  let current: any = THEME;
  
  for (const key of keys) {
    current = current[key];
    if (!current) return '';
  }
  
  return current;
};

export const getCategoryTheme = (category: string) => {
  return THEME.categories[category as keyof typeof THEME.categories] || THEME.categories.input;
};

export type ThemeConfig = typeof THEME;
export type CategoryTheme = typeof THEME.categories.input;