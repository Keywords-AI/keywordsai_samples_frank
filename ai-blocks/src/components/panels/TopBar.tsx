// src/components/panels/TopBar.tsx
/**
 * Top bar - contains run controls, level information, and main navigation
 */

"use client";
import { useRunStore } from "@/store/runStore";
import { useUIStore } from "@/store/uiStore";
import { useGraphStore } from "@/store/graphStore";
import { graphRunner } from "@/engine/runner";
import { useRouter } from "next/navigation";

import { LevelDefinition } from "@/engine/evaluator";
import { getLevelValidator } from "@/levels";

// Mock level for demonstration - in real app this would come from data/levels
const mockLevel: LevelDefinition = {
  id: "demo",
  title: "Demo Level",
  description: "Build a basic text processing workflow",
  difficulty: "easy",
  tags: ["basics", "text"],
  targetTokens: 1000,
  targetApiCalls: 3,
  targetTime: 30,
  observabilityTarget: 80,
  tests: [],
  starThresholds: {
    oneStar: 60,
    twoStar: 80,
    threeStar: 95,
  }
};

export default function TopBar() {
  const router = useRouter();

  const { 
    isRunning, 
    progress, 
    evaluation,
    startRun, 
    updateProgress, 
    addResult, 
    finishRun, 
    reset,
    setShowSuccessModal
  } = useRunStore();
  
  const { 
    currentLevel, 
    showModal, 
    togglePanel
  } = useUIStore();
  
  const { 
    exportGraph, 
    undo, 
    redo,
    isValid,
    validationErrors,
    canUndo,
    canRedo,
    clearGraph
  } = useGraphStore();

  const handleRun = async () => {
         if (isRunning) {
       graphRunner.stop();
       return;
     }

     if (!isValid) {
       alert(`Cannot run: ${validationErrors.join(', ')}`);
       return;
     }

     try {
      
             // Get current graph
       const currentGraph = exportGraph();
       
       // Get current level validator (defaulting to Level 1 for now)
       const currentLevelId = 1; // TODO: Get from UI store
       const validator = getLevelValidator(currentLevelId);
       
       if (!validator) {
         console.error(`No validator found for level ${currentLevelId}`);
         alert('❌ Level system error. Please refresh the page.');
         return;
       }
       
       console.log('Current graph:', currentGraph);
       console.log('Graph nodes:', currentGraph.nodes.length);
       console.log('Graph edges:', currentGraph.edges.length);
       
       // Debug: Show actual node types
       console.log('Node types found:', currentGraph.nodes.map(n => ({
         id: n.id,
         type: n.type,
         dataType: n.data?.type,
         data: n.data
       })));
       
       // Validate the pipeline first (this is the game logic)
       const validationResult = validator.validate(currentGraph);
       
       // Show validation feedback
       console.log('Validation Result:', validationResult);
       
       if (validationResult.score >= 60) {
         // Achieved at least 1 star! Run the actual execution
         startRun();
         const trace = await graphRunner.run(currentGraph, {
           onProgress: updateProgress,
           onResult: addResult,
           timeout: 30000,
           continueOnError: false,
         });
         finishRun(trace);
         
         // Show success modal with execution trace
         setShowSuccessModal(true, validationResult);
         
         // Modal shows success with detailed traces
         console.log('Level completed with score:', validationResult.score, validationResult);
       } else {
         // Pipeline needs work, show helpful feedback
         const feedback = [
           validationResult.message,
           '',
           'What you got right:',
           ...validationResult.correctAspects,
           '',
           'What needs fixing:',
           ...validationResult.issues,
           '',
           'Hints:',
           ...validationResult.hints
         ].join('\n');
         
         alert(`Score: ${validationResult.score}/100\n\n${feedback}`);
       }
         } catch (error) {
       console.error('Execution failed:', error);
       console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace');
       console.log('Current graph at error:', exportGraph());
       
       finishRun({
         results: [],
         totalTokens: 0,
         totalApiCalls: 0,
         totalDuration: 0,
         success: false,
         error: error instanceof Error ? error.message : 'Unknown error',
       });
       
       const errorMessage = error instanceof Error ? error.message : 'Unknown error';
       alert(`❌ Error Details:\n${errorMessage}\n\nCheck browser console (F12) for more info.\n\nCommon fixes:\n• Add blocks to canvas\n• Connect blocks with lines\n• Make sure you have User Input → LLM Parse → etc.`);
     }
  };

  const getStarDisplay = (score: number) => {
    // Use mock level thresholds for now
    const thresholds = mockLevel.starThresholds;
    if (score >= thresholds.threeStar) return '⭐⭐⭐';
    if (score >= thresholds.twoStar) return '⭐⭐';
    if (score >= thresholds.oneStar) return '⭐';
    return '';
  };

  return (
    <header className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-4">
      {/* Left side - Level info and run controls */}
      <div className="flex items-center space-x-4">
        {/* Level info */}
        <div 
          className="cursor-pointer hover:bg-gray-100 p-2 rounded"
          onClick={() => showModal('level')}
        >
          <h1 className="font-semibold text-gray-900">
            {(currentLevel || mockLevel).title}
          </h1>
          <p className="text-xs text-gray-600">
            {(currentLevel || mockLevel).difficulty} • {(currentLevel || mockLevel).tags.join(', ')}
          </p>
        </div>

        <div className="h-8 w-px bg-gray-300" />

        {/* Run controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRun}
            disabled={!isValid && !isRunning}
            className={`px-4 py-2 rounded font-medium ${
              isRunning
                ? 'bg-red-500 text-white hover:bg-red-600'
                : isValid
                ? 'bg-green-500 text-white hover:bg-green-600'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isRunning ? '⏹ Stop' : '▶ Run'}
          </button>

          <button
            onClick={() => {
              reset(); // Reset execution state
              clearGraph(); // Clear the canvas
            }}
            disabled={isRunning}
            className="px-3 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
          >
            🔄 Reset
          </button>
        </div>

        {/* Progress bar */}
        {isRunning && (
          <div className="w-32 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Validation status */}
        {!isValid && (
          <div className="text-red-500 text-sm">
            ⚠️ {validationErrors[0]}
          </div>
        )}
      </div>

      {/* Center - Results display */}
      {evaluation && (
        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 rounded text-sm font-medium ${
            evaluation.passed 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {evaluation.passed ? '✅ Passed' : '❌ Failed'}
          </div>

          <div className="text-sm text-gray-600">
            Score: {evaluation.score}/100 {getStarDisplay(evaluation.score)}
          </div>

          <div className="text-xs text-gray-500">
            {evaluation.tests.filter(t => t.passed).length}/{evaluation.tests.length} tests • 
            {evaluation.budgets.filter(b => !b.exceeded).length}/{evaluation.budgets.length} budgets
          </div>
        </div>
      )}

      {/* Right side - Panel toggles and actions */}
      <div className="flex items-center space-x-2">
        {/* Undo/Redo */}
        <button
          onClick={undo}
          disabled={!canUndo || isRunning}
          className="p-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
          title="Undo"
        >
          ↶
        </button>

        <button
          onClick={redo}
          disabled={!canRedo || isRunning}
          className="p-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
          title="Redo"
        >
          ↷
        </button>

        <div className="h-6 w-px bg-gray-300" />

        {/* Panel toggles */}
        <button
          onClick={() => togglePanel('toolbox')}
          className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
        >
          Toolbox
        </button>
        
        <button
          onClick={() => togglePanel('traceConsole')}
          className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
        >
          Console
        </button>

        <div className="h-6 w-px bg-gray-300" />

        {/* Settings */}
        <button
          onClick={() => showModal('settings')}
          className="p-2 text-gray-600 hover:text-gray-800"
          title="Settings"
        >
          ⚙️
        </button>

        <div className="h-6 w-px bg-gray-300" />

        {/* Back to Menu */}
        <button
          onClick={() => router.push('/')}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-600 rounded hover:bg-blue-200"
          title="Back to Menu"
        >
          🏠 Menu
        </button>
      </div>

      {/* Success Modal - Removed to avoid duplicate success screens */}
    </header>
  );
} 