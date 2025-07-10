// src/app/level1/page.tsx
/**
 * Level 1 page - Meeting Scheduler game interface
 */

"use client";
import { useEffect } from "react";
import { useUIStore } from "@/store/uiStore";
import { useGraphStore } from "@/store/graphStore";
import { loadLevel, getAvailableLevels } from "@/data/levelLoader";

// Components
import TopBar from "@/components/panels/TopBar";
import Toolbox from "@/components/panels/Toolbox";
import Canvas from "@/components/canvas/Canvas";
import TraceConsole from "@/components/panels/TraceConsole";
import QuickStartPanel from "@/components/panels/QuickStartPanel";

export default function Level1Page() {
  const { 
    currentLevel, 
    setCurrentLevel, 
    loadAvailableLevels,
    toolboxOpen,
    traceConsoleOpen
  } = useUIStore();
  const { setGraph } = useGraphStore();

  useEffect(() => {
    // Initialize the application
    async function initialize() {
      try {
        // Load available levels
        const levels = await getAvailableLevels();
        loadAvailableLevels(levels.map(l => ({
          id: l.id,
          title: l.title,
          description: `A ${l.difficulty} level`,
          difficulty: l.difficulty as 'easy' | 'medium' | 'hard',
          tags: [],
          targetTokens: 1000,
          targetApiCalls: 3,
          targetTime: 30,
          observabilityTarget: 80,
        })));

        // Load the first level by default
        if (!currentLevel) {
          const { level, starterGraph } = await loadLevel('level-1');
          setCurrentLevel(level);
          setGraph(starterGraph);
        }
      } catch (error) {
        console.error('Failed to initialize application:', error);
      }
    }

    initialize();
  }, [currentLevel, setCurrentLevel, loadAvailableLevels, setGraph]);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top navigation bar */}
      <TopBar />

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Toolbox */}
        {toolboxOpen && <Toolbox />}

        {/* Center - Canvas area */}
        <div className="flex-1 flex flex-col">
          <Canvas />
          
          {/* Bottom panel - Trace Console */}
          {traceConsoleOpen && <TraceConsole />}
        </div>

        {/* Inspector removed - was blocking view */}
      </div>
      
      {/* Quick Start Panel */}
      <QuickStartPanel />
    </div>
  );
} 