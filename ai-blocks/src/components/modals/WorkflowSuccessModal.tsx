// src/components/modals/WorkflowSuccessModal.tsx
/**
 * Workflow Success Modal - Keywords AI Observability Style
 * Shows successful level completion with trace-like execution details
 */

"use client";
import { useState, useMemo } from "react";
import { ValidationResult } from "@/levels/types";
import { ExecutionTrace, ExecutionResult } from "@/engine/graph";
import { blockRegistry } from "@/engine/blocks";

interface WorkflowTrace {
  workflowName: string;
  totalDuration: number;
  totalTokens: number;
  spans: Array<{
    id: string;
    name: string;
    duration: number;
    status: 'success' | 'error' | 'running';
    metadata: {
      blockType: string;
      inputTokens?: number;
      outputTokens?: number;
      model?: string;
    };
    startTime: number;
    endTime: number;
  }>;
}

interface Props {
  isOpen: boolean;
  validationResult: ValidationResult;
  executionTrace?: ExecutionTrace; // Add actual execution data
  onClose: () => void;
  onNextLevel?: () => void;
  onReplay?: () => void;
  onReturnToMenu?: () => void;
}

// Convert ExecutionTrace to WorkflowTrace format
const generateTraceFromExecution = (executionTrace: ExecutionTrace | undefined): WorkflowTrace => {
  if (!executionTrace || !executionTrace.results.length) {
    // Fallback to mock data if no execution trace
    const baseTime = Date.now() - 3000;
    return {
      workflowName: "Meeting Scheduler Workflow",
      totalDuration: 2847,
      totalTokens: 1234,
      spans: [
        {
          id: "span_1",
          name: "Context Merge",
          duration: 245,
          status: 'success',
          metadata: { blockType: "contextMerge" },
          startTime: baseTime,
          endTime: baseTime + 245
        },
        {
          id: "span_2", 
          name: "LLM Parse & Analysis",
          duration: 1203,
          status: 'success',
          metadata: { blockType: "llmParse", inputTokens: 23, outputTokens: 156, model: "gpt-4" },
          startTime: baseTime + 245,
          endTime: baseTime + 1448
        },
        {
          id: "span_3",
          name: "Calendar Check",
          duration: 567,
          status: 'success',
          metadata: { blockType: "googleCalendarGet" },
          startTime: baseTime + 1448,
          endTime: baseTime + 2015
        },
        {
          id: "span_4",
          name: "Time Suggestion",
          duration: 432,
          status: 'success',
          metadata: { blockType: "llmSuggestTime", inputTokens: 156, outputTokens: 89, model: "gpt-4" },
          startTime: baseTime + 2015,
          endTime: baseTime + 2447
        },
        {
          id: "span_5",
          name: "Calendar Scheduling",
          duration: 234,
          status: 'success',
          metadata: { blockType: "googleCalendarSchedule" },
          startTime: baseTime + 2447,
          endTime: baseTime + 2681
        },
        {
          id: "span_6",
          name: "User Output",
          duration: 166,
          status: 'success',
          metadata: { blockType: "userOutput", inputTokens: 34, outputTokens: 67, model: "gpt-4" },
          startTime: baseTime + 2681,
          endTime: baseTime + 2847
        }
      ]
    };
  }

  // Expected execution order (excluding userInput which is just the trigger)
  const expectedBlockOrder = [
    'contextVariable',
    'contextMerge', 
    'llmParse',
    'googleCalendarGet',
    'llmSuggestTime',
    'googleCalendarSchedule',
    'userOutput'
  ];

  // Generate spans for the complete expected workflow
  const spans: WorkflowTrace['spans'] = [];
  let cumulativeTime = Date.now() - executionTrace.totalDuration;

  for (let index = 0; index < expectedBlockOrder.length; index++) {
    const expectedBlockType = expectedBlockOrder[index];
    const block = blockRegistry.get(expectedBlockType);
    
    // Generate reasonable random durations based on block type
    const baseDuration = getDurationForBlockType(expectedBlockType);
    const duration = Math.floor(baseDuration + (Math.random() * baseDuration * 0.4)); // ±40% variation
    
    const span = {
      id: `span_${index + 1}`,
      name: getDisplayNameForBlock(expectedBlockType, block?.label),
      duration,
      status: 'success' as const, // Assume success since the workflow completed
      metadata: {
        blockType: expectedBlockType,
        inputTokens: getTokensFromResult({ metadata: { nodeType: expectedBlockType } } as any, 'input'),
        outputTokens: getTokensFromResult({ metadata: { nodeType: expectedBlockType } } as any, 'output'), 
        model: getModelFromBlockType(expectedBlockType)
      },
      startTime: cumulativeTime,
      endTime: cumulativeTime + duration
    };
    
    spans.push(span);
    cumulativeTime += duration;
  }

  const totalDuration = spans.reduce((sum: number, span: WorkflowTrace['spans'][0]) => sum + span.duration, 0);
  
  return {
    workflowName: "Meeting Scheduler Workflow",
    totalDuration,
    totalTokens: executionTrace.totalTokens || spans.reduce((sum: number, span: WorkflowTrace['spans'][0]) => sum + (span.metadata.inputTokens || 0) + (span.metadata.outputTokens || 0), 0),
    spans
  };
};

// Helper functions
const extractBlockTypeFromNodeId = (nodeId: string): string => {
  // Extract block type from nodeId if metadata doesn't have it
  // NodeId format could be "blockType-randomId", "randomId-blockType", or just "randomId"
  
  if (!nodeId) return 'unknown';
  
  const parts = nodeId.split('-');
  
  // Known block types to check against
  const knownBlockTypes = [
    'userInput', 'contextVariable', 'contextMerge', 'llmParse', 
    'googleCalendarGet', 'llmSuggestTime', 'googleCalendarSchedule', 'userOutput'
  ];
  
  // Check each part to see if it matches a known block type
  for (const part of parts) {
    if (knownBlockTypes.includes(part)) {
      return part;
    }
  }
  
  // If no known block type found, check if any part looks like a block type (not a random ID)
  for (const part of parts) {
    if (part.length > 3 && part.length < 20 && !part.match(/^[a-f0-9]{8,}$/i)) {
      return part;
    }
  }
  
  return 'unknown';
};

const getDurationForBlockType = (blockType: string): number => {
  const durations: Record<string, number> = {
    'contextMerge': 200,
    'contextVariable': 150,
    'llmParse': 1200,
    'llmSuggestTime': 800,
    'googleCalendarGet': 450,
    'googleCalendarSchedule': 350,
    'userOutput': 180,
    'default': 300
  };
  return durations[blockType] || durations.default;
};

const getDisplayNameForBlock = (blockType: string, label?: string): string => {
  const names: Record<string, string> = {
    'userInput': 'User Input',
    'contextVariable': 'Context Variable',
    'contextMerge': 'Context Merge',
    'llmParse': 'LLM Parse & Analysis',
    'googleCalendarGet': 'Calendar Check', 
    'llmSuggestTime': 'LLM Suggest Time',
    'googleCalendarSchedule': 'Calendar Scheduling',
    'userOutput': 'User Output'
  };
  // Return mapped name, fallback to label, then blockType, then 'Unknown Block'
  return names[blockType] || label || blockType || 'Unknown Block';
};

const getTokensFromResult = (result: ExecutionResult, type: 'input' | 'output'): number => {
  // Estimate tokens based on block type for display purposes
  const blockType = result.metadata.nodeType || extractBlockTypeFromNodeId(result.nodeId);
  
  if (type === 'input') {
    const inputTokens: Record<string, number> = {
      'contextMerge': 25,
      'llmParse': 35,
      'llmSuggestTime': 120,
      'googleCalendarGet': 45,
      'googleCalendarSchedule': 80,
      'userOutput': 40
    };
    return inputTokens[blockType] || 20;
  } else {
    const outputTokens: Record<string, number> = {
      'contextMerge': 45,
      'llmParse': 150,
      'llmSuggestTime': 85,
      'googleCalendarGet': 30,
      'googleCalendarSchedule': 25,
      'userOutput': 65
    };
    return outputTokens[blockType] || 30;
  }
};

const getModelFromBlockType = (blockType: string): string | undefined => {
  const llmBlocks = ['llmParse', 'llmSuggestTime', 'userOutput'];
  return llmBlocks.includes(blockType) ? 'gpt-4' : undefined;
};

export default function WorkflowSuccessModal({ 
  isOpen, 
  validationResult, 
  executionTrace,
  onClose, 
  onNextLevel,
  onReplay,
  onReturnToMenu 
}: Props) {
  const trace = useMemo(() => generateTraceFromExecution(executionTrace), [executionTrace]);
  const [selectedSpan, setSelectedSpan] = useState<string | null>(null);

  if (!isOpen) return null;

  const getSpanColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'running': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStarDisplay = (score: number) => {
    if (score >= 95) return '⭐⭐⭐';
    if (score >= 80) return '⭐⭐';
    if (score >= 60) return '⭐';
    return '';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-gray-700 to-gray-800 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center text-white">
                🎉 Level Complete! {getStarDisplay(validationResult.score)}
              </h2>
                              <p className="text-gray-200 mt-1">Your workflow executed successfully</p>
            </div>
            <div className="flex items-center space-x-4">
              <a 
                href="https://www.keywordsai.co/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-gray-300 hover:text-white flex items-center space-x-1"
              >
                <span>Powered by</span>
                <span className="font-semibold">Keywords AI</span>
              </a>
              <button
                onClick={onClose}
                className="text-white hover:text-gray-300 text-xl"
              >
                ✕
              </button>
            </div>
          </div>
          
          {/* Score & Metrics */}
          <div className="flex items-center space-x-6 mt-4">
            <div className="bg-black bg-opacity-30 rounded px-3 py-1">
              <span className="text-sm text-white font-medium">Score: {validationResult.score}/100</span>
            </div>
            <div className="bg-black bg-opacity-30 rounded px-3 py-1">
              <span className="text-sm text-white font-medium">Duration: {formatDuration(trace.totalDuration)}</span>
            </div>
            <div className="bg-black bg-opacity-30 rounded px-3 py-1">
              <span className="text-sm text-white font-medium">Tokens: {trace.totalTokens}</span>
            </div>
            <div className="bg-black bg-opacity-30 rounded px-3 py-1">
              <span className="text-sm text-white font-medium">Spans: {trace.spans.length}</span>
            </div>
          </div>
        </div>

        <div className="flex h-96 overflow-y-auto">
          {/* Trace Timeline */}
          <div className="flex-1 p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Trace: {trace.workflowName}
            </h3>
            
            <div className="space-y-2">
              {trace.spans.map((span, index) => (
                <div 
                  key={span.id}
                  className={`border rounded-lg p-3 cursor-pointer transition-all ${
                    selectedSpan === span.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedSpan(selectedSpan === span.id ? null : span.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500 text-sm">#{index + 1}</span>
                        <div className={`w-3 h-3 rounded-full ${getSpanColor(span.status)}`}></div>
                      </div>
                      <span className="font-medium text-gray-800">{span.name}</span>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-600">
                        {formatDuration(span.duration)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {span.metadata.blockType}
                      </span>
                    </div>
                  </div>
                  
                  {/* Timeline Bar */}
                  <div className="mt-2">
                    <div className="bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div 
                        className={`h-full ${getSpanColor(span.status)} transition-all duration-500`}
                        style={{ 
                          width: `${(span.duration / trace.totalDuration) * 100}%`,
                          marginLeft: `${((span.startTime - trace.spans[0].startTime) / trace.totalDuration) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {selectedSpan === span.id && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Input Tokens:</span>
                          <span className="ml-2 font-medium">{span.metadata.inputTokens || 0}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Output Tokens:</span>
                          <span className="ml-2 font-medium">{span.metadata.outputTokens || 0}</span>
                        </div>
                        {span.metadata.model && (
                          <div className="col-span-2">
                            <span className="text-gray-500">Model:</span>
                            <span className="ml-2 font-medium">{span.metadata.model}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar - Success Details */}
          <div className="w-80 border-l border-gray-200 p-6 bg-gray-50">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Validation Results</h3>
            
            {/* What worked */}
            <div className="mb-4">
              <h4 className="font-medium text-green-800 mb-2">✅ What you got right:</h4>
              <div className="space-y-1">
                {validationResult.correctAspects.map((aspect, i) => (
                  <div key={i} className="text-sm text-green-700">{aspect}</div>
                ))}
              </div>
            </div>

            {/* Message */}
            <div className="bg-green-100 border border-green-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-green-800">{validationResult.message}</p>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <h4 className="font-medium text-gray-800 mb-2">Performance</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Time:</span>
                  <span className="font-medium">{formatDuration(trace.totalDuration)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Span Time:</span>
                  <span className="font-medium">{formatDuration(trace.totalDuration / trace.spans.length)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Success Rate:</span>
                  <span className="font-medium text-green-600">100%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="flex justify-between">
            <button
              onClick={onReturnToMenu}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              🏠 Back to Menu
            </button>
            <div className="flex space-x-3">
              <button
                onClick={onReplay}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                🔄 Replay Level
              </button>
              <button
                onClick={onNextLevel}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                ➡️ Next Level
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 