// src/components/panels/TopBar.tsx
/**
 * Top bar - contains run controls, level information, and main navigation
 */

"use client";
// Remove unused imports at the top
import { useRunStore } from "@/store/runStore";
import { useUIStore } from "@/store/uiStore";
import { useGraphStore } from "@/store/graphStore";
import { graphRunner } from "@/engine/runner";
import { useRouter } from "next/navigation";
import { getLevelValidator } from "@/levels";
// Import centralized configuration
import { APP_CONFIG, ROUTES } from "@/config";
import { THEME } from "@/config/theme";
import { UI_STATES } from "@/lib/constants";

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

  // Get current level config from centralized configuration
  const getCurrentLevelConfig = () => {
    // Default to level-1 if no current level is set
    const levelId = currentLevel?.id || 'level-1';
    return APP_CONFIG.levels[levelId as keyof typeof APP_CONFIG.levels] || APP_CONFIG.levels['level-1'];
  };

  const currentLevelConfig = getCurrentLevelConfig();

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
      
      // Get current level validator
      const currentLevelId = parseInt(currentLevelConfig.id.replace('level-', '')) || 1;
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
      
      if (validationResult.score >= currentLevelConfig.starThresholds.oneStar) {
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
    const thresholds = currentLevelConfig.starThresholds;
    if (score >= thresholds.threeStar) return '⭐⭐⭐';
    if (score >= thresholds.twoStar) return '⭐⭐';
    if (score >= thresholds.oneStar) return '⭐';
    return '';
  };

  return (
    <header className={`${APP_CONFIG.ui.layout.topBarHeight} ${THEME.colors.border.default} bg-white flex items-center justify-between px-4`}>
      {/* Left side - Level info and run controls */}
      <div className="flex items-center space-x-4">
        {/* Level info */}
        <div 
          className={`cursor-pointer ${THEME.categories.input.hover} p-2 ${THEME.borderRadius.sm}`}
          onClick={() => showModal('level')}
        >
          <h1 className={`${THEME.typography.weight.semibold} ${THEME.colors.text.primary}`}>
            {currentLevelConfig.title}
          </h1>
          <p className={`${THEME.typography.body.xs} ${THEME.colors.text.secondary}`}>
            {currentLevelConfig.difficulty} • {currentLevelConfig.tags.join(', ')}
          </p>
        </div>

        <div className="h-8 w-px bg-gray-300" />

        {/* Run controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRun}
            disabled={!isValid && !isRunning}
            className={`${THEME.components.button.base} ${
              isRunning
                ? THEME.components.button.danger
                : isValid
                ? THEME.components.button.success
                : THEME.components.button.disabled
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
            className={`px-3 py-2 ${THEME.colors.text.secondary} hover:text-gray-800 disabled:opacity-50`}
          >
            🔄 Reset
          </button>
        </div>

        {/* Progress bar */}
        {isRunning && (
          <div className="w-32 bg-gray-200 rounded-full h-2">
            <div 
              className={`${THEME.colors.primary[500]} h-2 rounded-full ${THEME.transitions.default}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Validation status */}
        {!isValid && (
          <div className={`${THEME.colors.error.text} ${THEME.typography.body.small}`}>
            ⚠️ {validationErrors[0]}
          </div>
        )}
      </div>

      {/* Center - Results display */}
      {evaluation && (
        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 ${THEME.borderRadius.sm} ${THEME.typography.body.small} ${THEME.typography.weight.medium} ${
            evaluation.passed 
              ? `${THEME.colors.success[100]} ${THEME.colors.success.text}` 
              : `${THEME.colors.error[100]} ${THEME.colors.error.text}`
          }`}>
            {evaluation.passed ? '✅ Passed' : '❌ Failed'}
          </div>

          <div className={`${THEME.typography.body.small} ${THEME.colors.text.secondary}`}>
            Score: {evaluation.score}/100 {getStarDisplay(evaluation.score)}
          </div>

          <div className={`${THEME.typography.body.xs} ${THEME.colors.text.muted}`}>
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
          className={`p-2 ${THEME.colors.text.secondary} hover:text-gray-800 disabled:opacity-50`}
          title="Undo"
        >
          ↶
        </button>

        <button
          onClick={redo}
          disabled={!canRedo || isRunning}
          className={`p-2 ${THEME.colors.text.secondary} hover:text-gray-800 disabled:opacity-50`}
          title="Redo"
        >
          ↷
        </button>

        <div className="h-6 w-px bg-gray-300" />

        {/* Panel toggles */}
        <button
          onClick={() => togglePanel('toolbox')}
          className={`px-3 py-1 ${THEME.typography.body.small} ${THEME.components.button.secondary}`}
        >
          Toolbox
        </button>
        
        <button
          onClick={() => togglePanel('traceConsole')}
          className={`px-3 py-1 ${THEME.typography.body.small} ${THEME.components.button.secondary}`}
        >
          Console
        </button>

        <div className="h-6 w-px bg-gray-300" />

        {/* Settings */}
        <button
          onClick={() => showModal('settings')}
          className={`p-2 ${THEME.colors.text.secondary} hover:text-gray-800`}
          title="Settings"
        >
          ⚙️
        </button>

        <div className="h-6 w-px bg-gray-300" />

        {/* Back to Menu */}
        <button
          onClick={() => router.push(ROUTES.home)}
          className={`px-3 py-1 ${THEME.typography.body.small} ${THEME.colors.primary[100]} text-blue-600 ${THEME.borderRadius.sm} hover:bg-blue-200`}
          title="Back to Menu"
        >
          🏠 Menu
        </button>
      </div>
    </header>
  );
}