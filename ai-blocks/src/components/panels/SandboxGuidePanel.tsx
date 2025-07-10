// src/components/panels/SandboxGuidePanel.tsx
/**
 * Sandbox Guide Panel - Shows creative mode instructions and tips
 */

"use client";
import { useState } from "react";

export default function SandboxGuidePanel() {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!isExpanded) {
    return (
      <div className="fixed top-20 right-4 z-30">
        <button
          onClick={() => setIsExpanded(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg shadow-lg transition-colors flex items-center space-x-2"
        >
          <span>🔧</span>
          <span>Sandbox Guide</span>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed top-20 right-4 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-30">
      {/* Header */}
      <div className="bg-purple-600 text-white px-4 py-3 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🔧</span>
          <h3 className="font-semibold">Sandbox Mode</h3>
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
          {/* Freedom Message */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <p className="text-sm text-purple-800">
              <strong>🎨 Free Play Mode:</strong> Experiment with all blocks without restrictions! 
              No scoring, no rules - just pure creativity.
            </p>
          </div>

          {/* Basic Steps */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="text-green-600 mr-2">📋</span>
              How to Build
            </h4>
            <div className="space-y-2 text-sm text-gray-700">
              <div className="flex items-start space-x-2">
                <span className="bg-purple-100 text-purple-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">1</span>
                <span>Drag any blocks from the <strong>Toolbox</strong></span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-purple-100 text-purple-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">2</span>
                <span>Connect them in <strong>any order</strong> you want</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-purple-100 text-purple-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">3</span>
                <span>Experiment with different <strong>combinations</strong></span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-purple-100 text-purple-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-semibold mt-0.5">4</span>
                <span>Test and iterate as much as you want!</span>
              </div>
            </div>
          </div>

          {/* Ideas */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="text-yellow-600 mr-2">💡</span>
              Creative Ideas
            </h4>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-start space-x-2">
                <span className="text-yellow-600">•</span>
                <span>Create <strong>multiple LLM chains</strong> for complex reasoning</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-yellow-600">•</span>
                <span>Build <strong>data transformation</strong> pipelines</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-yellow-600">•</span>
                <span>Test <strong>different block combinations</strong></span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-yellow-600">•</span>
                <span>Prototype your own <strong>workflows</strong></span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="text-blue-600 mr-2">🚀</span>
              Sandbox Tips
            </h4>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-start space-x-2">
                <span className="text-blue-600">•</span>
                <span>Use the <strong>Console</strong> to debug your creations</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-blue-600">•</span>
                <span>Save interesting workflows as screenshots</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-blue-600">•</span>
                <span>Try breaking things - that's how you learn!</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 