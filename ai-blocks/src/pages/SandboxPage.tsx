// src/pages/SandboxPage.tsx
/**
 * Sandbox Page - Free play mode with all blocks available
 * Unified page component for sandbox workflow building
 */

"use client";
import { useEffect } from "react";
import { useUIStore } from "@/store/uiStore";
import { useGraphStore } from "@/store/graphStore";

// Feature components
import { WorkflowCanvas, WorkflowToolbox, WorkflowConsole } from "@/features/workflow";
import { SandboxGuide } from "@/features/sandbox";
import { AppTopBar } from "@/features/layout";

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
      <AppTopBar mode="sandbox" />

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Toolbox */}
        {toolboxOpen && <WorkflowToolbox />}

        {/* Center - Canvas area */}
        <div className="flex-1 flex flex-col">
          <WorkflowCanvas />
          
          {/* Bottom panel - Console */}
          {traceConsoleOpen && <WorkflowConsole />}
        </div>
      </div>
      
      {/* Sandbox Guide Panel */}
      <SandboxGuide />
    </div>
  );
} 