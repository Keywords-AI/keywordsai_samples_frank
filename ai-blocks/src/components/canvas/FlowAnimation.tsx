// src/components/canvas/FlowAnimation.tsx
/**
 * Simple success animation - just shows a window with trace results
 */

import React, { useState, useEffect } from 'react';
import { useRunStore } from '@/store/runStore';

interface FlowAnimationProps {
  isVisible: boolean;
  onComplete?: () => void;
}

export function FlowAnimation({ isVisible, onComplete }: FlowAnimationProps) {
  const { trace } = useRunStore();
  const [showTrace, setShowTrace] = useState(false);

  useEffect(() => {
    if (!isVisible) {
      setShowTrace(false);
      return;
    }

    // Simple delay then show trace
    const timer = setTimeout(() => {
      setShowTrace(true);
    }, 1000);

    return () => clearTimeout(timer);
  }, [isVisible]);

  if (!isVisible) return null;

  // Create proper trace structure with all executed blocks as spans
  const aiSchedulerTrace = {
    name: "AI Scheduler",
    duration: trace?.totalDuration || 2847,
    totalTokens: trace?.totalTokens || 0,
    totalApiCalls: trace?.totalApiCalls || 0,
    spans: trace?.results.map((result, index) => ({
      id: `span${index + 1}`,
      name: result.nodeId,
      type: "task",
      duration: result.metadata.duration || 0,
      status: result.metadata.error ? "failed" : "completed",
      tokens: result.metadata.tokens || 0,
      nodeType: result.metadata.nodeType || "unknown"
    })) || []
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto animate-in slide-in-from-bottom-4 duration-500">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-blue-600 text-white p-6 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center">
                🎉 Success!
              </h2>
              <p className="text-green-100 mt-1">AI Workflow Executed Successfully</p>
            </div>
            <button
              onClick={onComplete}
              className="text-white hover:text-gray-200 text-xl"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Trace Content */}
        {showTrace && (
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Trace: {aiSchedulerTrace.name}
            </h3>
            
            {/* Main trace info - trace on top with full time */}
            <div className="mb-6 p-4 bg-blue-50 rounded border border-blue-200">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-blue-900">🔍 {aiSchedulerTrace.name}</div>
                  <div className="text-sm text-blue-700">Workflow Trace</div>
                </div>
                <div className="text-right text-sm text-blue-700">
                  <div><strong>Total Duration: {aiSchedulerTrace.duration}ms</strong></div>
                  <div>Tokens: {aiSchedulerTrace.totalTokens} | API Calls: {aiSchedulerTrace.totalApiCalls}</div>
                  <div>Status: ✅ Completed</div>
                </div>
              </div>
            </div>

            {/* Spans - each block gets its own span with duration */}
            <div className="space-y-3">
              <h4 className="font-medium text-gray-700 mb-3">📊 Spans (Each Block):</h4>
              {aiSchedulerTrace.spans.map((span, index) => (
                <div key={span.id} className="flex items-center space-x-4 p-3 bg-gray-50 rounded border">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                    span.status === 'completed' ? 'bg-green-500' : 'bg-red-500'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-gray-900">{span.name}</div>
                        <div className="text-sm text-gray-600">{span.nodeType} • {span.type}</div>
                      </div>
                      <div className="text-right text-sm text-gray-600">
                        <div><strong>Duration: {span.duration}ms</strong></div>
                        {span.tokens > 0 && <div>{span.tokens} tokens</div>}
                        <div className={`${span.status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>
                          {span.status === 'completed' ? '✅ completed' : '❌ failed'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="mt-6 p-4 bg-gray-100 rounded">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-gray-900">{aiSchedulerTrace.spans.length}</div>
                  <div className="text-sm text-gray-600">Spans</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">{aiSchedulerTrace.duration}ms</div>
                  <div className="text-sm text-gray-600">Total Time</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {aiSchedulerTrace.spans.reduce((sum, span) => sum + span.tokens, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Total Tokens</div>
                </div>
              </div>
            </div>

                         {/* Keywords AI Branding */}
             <div className="mt-6 text-center">
               <div className="text-sm text-gray-500">
                 Powered by <a 
                   href="https://www.keywordsai.co/" 
                   target="_blank" 
                   rel="noopener noreferrer"
                   className="font-semibold text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                 >
                   Keywords AI
                 </a>
               </div>
             </div>
          </div>
        )}
      </div>
    </div>
  );
} 