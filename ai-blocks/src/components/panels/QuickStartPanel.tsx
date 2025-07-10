// src/components/panels/QuickStartPanel.tsx
/**
 * QuickStart Panel - Shows game instructions and tips prominently
 */

"use client";
import { useState } from "react";

export default function QuickStartPanel() {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!isExpanded) {
    return (
      <div className="fixed top-20 right-4 z-30">
        <button
          onClick={() => setIsExpanded(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-lg transition-colors flex items-center space-x-2"
        >
          <span>❓</span>
          <span>Workflow Guide</span>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed top-20 right-4 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-30">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-3 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🚀</span>
          <h3 className="font-semibold">Workflow Building Guide</h3>
        </div>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-white hover:text-gray-200 text-xl"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="space-y-4">
          {/* Basic Steps */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="text-green-600 mr-2">📋</span>
              How to Build Workflows
            </h4>
            <div className="space-y-2 text-sm text-gray-700">
              <div className="flex items-start space-x-2">
                <span className="bg-blue-100 text-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">1</span>
                <span>Drag blocks from the <strong>Toolbox</strong> to the canvas</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-blue-100 text-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">2</span>
                <span>Connect block <strong>outputs</strong> to <strong>inputs</strong> by dragging</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-blue-100 text-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">3</span>
                <span>Click blocks to edit their settings</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-blue-100 text-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">4</span>
                <span>Press the <strong>▶ Run</strong> button to execute the workflow</span>
              </div>
            </div>
          </div>

          {/* Level 1 Goal */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="text-yellow-600 mr-2">🎯</span>
              Level 1 Goal
            </h4>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                Build a workflow that can <strong>schedule meetings automatically</strong>. 
                Connect <strong>all blocks</strong> to create a complete workflow from user input to calendar scheduling.
              </p>
            </div>
          </div>

          {/* Pro Tips */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="text-purple-600 mr-2">💡</span>
              Pro Tips
            </h4>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-start space-x-2">
                <span className="text-purple-600">•</span>
                <span><strong>Use ALL blocks</strong> to build the complete workflow</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-purple-600">•</span>
                <span>Start with <strong>User Input</strong> and end with <strong>User Output</strong></span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-purple-600">•</span>
                <span>Use <strong>Context Variable</strong> to provide current date/time</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-purple-600">•</span>
                <span>Check the console for workflow execution feedback</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-purple-600">•</span>
                <span>Hover over blocks to see connection hints</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 