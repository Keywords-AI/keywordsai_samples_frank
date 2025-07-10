// src/app/sandbox/page.tsx
/**
 * Sandbox page - Free play mode with all blocks available
 */

"use client";
import { useEffect } from "react";
import { useUIStore } from "@/store/uiStore";
import { useGraphStore } from "@/store/graphStore";

// Components
import TopBar from "@/components/panels/TopBar";
import Toolbox from "@/components/panels/Toolbox";
import Canvas from "@/components/canvas/Canvas";
import TraceConsole from "@/components/panels/TraceConsole";
import SandboxGuidePanel from "@/components/panels/SandboxGuidePanel";

export default function SandboxPage() {
  const { 
    toolboxOpen,
    traceConsoleOpen
  } = useUIStore();
  const { clearGraph } = useGraphStore();

  useEffect(() => {
    // Start with a clean canvas in sandbox mode
    clearGraph();
  }, [clearGraph]);

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
      
      {/* Sandbox Guide Panel */}
      <SandboxGuidePanel />
    </div>
  );
} 