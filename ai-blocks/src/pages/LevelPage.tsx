// src/pages/LevelPage.tsx
/**
 * Level Page - Tutorial/Challenge mode with level-specific configuration
 * Unified page component for level-based workflow building
 */

"use client";
import { useEffect } from "react";
import { useUIStore } from "@/store/uiStore";
import { useGraphStore } from "@/store/graphStore";
import { loadLevel, getAvailableLevels } from "@/data/levelLoader";
import { APP_CONFIG } from "@/config";
import { levelManager } from "@/features/levels";

// Components (using existing components for now)
import TopBar from "@/components/panels/TopBar";
import Toolbox from "@/components/panels/Toolbox";
import Canvas from "@/components/canvas/Canvas";
import TraceConsole from "@/components/panels/TraceConsole";
import QuickStartPanel from "@/components/panels/QuickStartPanel";
import WorkflowSuccessModal from "@/components/modals/WorkflowSuccessModal";

interface LevelPageProps {
  levelId: string;
}

export default function LevelPage({ levelId }: LevelPageProps) {
  const { 
    currentLevel, 
    setCurrentLevel, 
    loadAvailableLevels,
    toolboxOpen,
    traceConsoleOpen
  } = useUIStore();
  const { setGraph } = useGraphStore();

  useEffect(() => {
    // Initialize the level
    async function initialize() {
      try {
        // Check if level is unlocked
        if (!levelManager.isLevelUnlocked(levelId)) {
          console.warn(`Level ${levelId} is not unlocked`);
          return;
        }

        // Start the level in the level manager
        levelManager.startLevel(levelId);

        // Get level with blocks from level manager
        const levelWithBlocks = levelManager.getLevelWithBlocks(levelId);
        if (levelWithBlocks) {
          setCurrentLevel(levelWithBlocks.level);
        }

        // Load legacy level data for graph
        const { level, starterGraph } = await loadLevel(levelId);
        setGraph(starterGraph);
      } catch (error) {
        console.error(`Failed to initialize level ${levelId}:`, error);
      }
    }

    initialize();
  }, [levelId, setCurrentLevel, setGraph]);

  // Get level config from APP_CONFIG
  const levelConfig = APP_CONFIG.levels[levelId as keyof typeof APP_CONFIG.levels];
  
  if (!levelConfig) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Level Not Found</h1>
          <p className="text-gray-600">The level "{levelId}" could not be found.</p>
        </div>
      </div>
    );
  }

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
      </div>
      
      {/* Level-specific panels */}
      <QuickStartPanel />
      
      {/* Success Modal */}
      <WorkflowSuccessModal 
        isOpen={false} // Will be controlled by level completion logic
        validationResult={{
          isCorrect: false,
          score: 0,
          correctAspects: [],
          issues: [],
          hints: [],
          message: ""
        }}
        onClose={() => {}}
        onNextLevel={() => {}}
        onReplay={() => {}}
        onReturnToMenu={() => {}}
      />
    </div>
  );
} 