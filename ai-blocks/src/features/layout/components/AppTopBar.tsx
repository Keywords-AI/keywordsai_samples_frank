// src/features/layout/components/AppTopBar.tsx
/**
 * App Top Bar - Main navigation and control bar
 * Feature-based organization for better maintainability
 * (Temporarily wrapping existing TopBar component)
 */

"use client";
import TopBar from "@/components/panels/TopBar";

interface AppTopBarProps {
  mode?: 'sandbox' | 'level' | 'home';
}

export function AppTopBar({ mode = 'home' }: AppTopBarProps) {
  return <TopBar />;
}

export default AppTopBar; 