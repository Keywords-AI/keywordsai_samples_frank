// src/components/panels/TraceConsole.tsx
/**
 * Trace Console panel - displays live execution traces and debugging information
 */

"use client";
import { useRunStore } from "@/store/runStore";
import { useUIStore } from "@/store/uiStore";
import { ExecutionResult } from "@/engine/graph";
import { useState } from "react";

export default function TraceConsole() {
  const { 
    liveResults, 
    trace, 
    selectedTraceIndex, 
    showOnlyErrors, 
    selectTrace, 
    toggleErrorFilter,
    showSuccessAnimation
  } = useRunStore();
  const { traceConsoleOpen, togglePanel } = useUIStore();
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

  if (!traceConsoleOpen || showSuccessAnimation) {
    return null;
  }

  const results = trace ? trace.results : liveResults;
  const filteredResults = showOnlyErrors 
    ? results.filter(r => r.metadata.error)
    : results;

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const renderResult = (result: ExecutionResult, index: number) => {
            const isSelected = selectedTraceIndex === index;
    const isExpanded = expandedResults.has(index);
    const hasError = !!result.metadata.error;

    return (
      <div
        key={`${result.nodeId}-${index}`}
        className={`border-b border-gray-200 ${isSelected ? 'bg-blue-50' : ''}`}
      >
        <div
          className={`p-3 cursor-pointer hover:bg-gray-50 ${hasError ? 'bg-red-50' : ''}`}
                      onClick={() => {
              selectTrace(isSelected ? null : index);
            toggleExpanded(index);
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${hasError ? 'bg-red-500' : 'bg-green-500'}`} />
              <span className="font-mono text-sm font-medium text-gray-900">{result.nodeId}</span>
              <span className="text-xs text-gray-600">
                {result.metadata.nodeType || 'unknown'}
              </span>
            </div>
            <div className="flex items-center space-x-2 text-xs text-gray-600">
              <span>{formatTimestamp(result.metadata.timestamp)}</span>
              <span>{formatDuration(result.metadata.duration)}</span>
              {result.metadata.tokens && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                  {result.metadata.tokens} tokens
                </span>
              )}
              {result.metadata.apiCalls && (
                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
                  {result.metadata.apiCalls} API
                </span>
              )}
            </div>
          </div>

          {hasError && (
            <div className="mt-2 text-sm text-red-600">
              ❌ {result.metadata.error}
            </div>
          )}
        </div>

        {isExpanded && (
          <div className="px-3 pb-3 bg-gray-50 border-t border-gray-200">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {/* Input */}
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Input</h4>
                <pre className="bg-white p-2 rounded border border-gray-300 text-gray-900 text-xs overflow-auto max-h-32">
                  {result.input !== null 
                    ? JSON.stringify(result.input, null, 2) 
                    : 'null'
                  }
                </pre>
              </div>

              {/* Output */}
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Output</h4>
                <pre className="bg-white p-2 rounded border border-gray-300 text-gray-900 text-xs overflow-auto max-h-32">
                  {result.output !== null 
                    ? JSON.stringify(result.output, null, 2) 
                    : 'null'
                  }
                </pre>
              </div>
            </div>

            {/* Metadata */}
            <div className="mt-4">
              <h4 className="font-medium text-gray-700 mb-2">Metadata</h4>
              <pre className="bg-white p-2 rounded border border-gray-300 text-gray-900 text-xs overflow-auto max-h-24">
                {JSON.stringify(result.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-80 border-t border-gray-200 bg-white flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <h2 className="font-semibold text-gray-900">Trace Console</h2>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span>{filteredResults.length} entries</span>
            {trace && (
              <>
                <span>•</span>
                <span>{formatDuration(trace.totalDuration)} total</span>
                <span>•</span>
                <span>{trace.totalTokens} tokens</span>
                <span>•</span>
                <span>{trace.totalApiCalls} API calls</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Filter Toggle */}
          <button
            onClick={toggleErrorFilter}
            className={`px-3 py-1 text-sm rounded ${
              showOnlyErrors 
                ? 'bg-red-100 text-red-700' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {showOnlyErrors ? 'Show All' : 'Errors Only'}
          </button>

          {/* Clear */}
          <button
            onClick={() => {
              setExpandedResults(new Set());
              selectTrace(null);
            }}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
          >
            Clear
          </button>

          {/* Close */}
          <button
            onClick={() => togglePanel('traceConsole')}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {filteredResults.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {showOnlyErrors 
              ? 'No errors in execution trace'
              : 'No execution results yet. Run the workflow to see traces.'
            }
          </div>
        ) : (
          <div>
            {filteredResults.map((result) => 
              renderResult(result, results.indexOf(result))
            )}
          </div>
        )}
      </div>

      {/* Footer with stats */}
      {trace && (
        <div className="px-3 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
          <div className="flex justify-between">
            <span>
              Status: {trace.success ? '✅ Success' : '❌ Failed'}
              {trace.error && ` - ${trace.error}`}
            </span>
            <span>
              {results.length} nodes executed
            </span>
          </div>
        </div>
      )}
    </div>
  );
} 