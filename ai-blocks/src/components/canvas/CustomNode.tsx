// src/components/canvas/CustomNode.tsx
/**
 * Custom React Flow node component that shows proper input/output handles
 * Based on block definitions from the registry
 */

import React from 'react';
import { Handle, Position, NodeProps } from 'react-flow-renderer';
import { getBlock } from '@/engine/blocks/registry';

interface CustomNodeData {
  label: string;
  params?: Record<string, unknown>;
  [key: string]: unknown;
}

export function CustomNode({ data, type }: NodeProps<CustomNodeData>) {
  const block = getBlock(type);
  
  if (!block) {
    return (
      <div className="px-4 py-2 bg-red-50 border-2 border-red-300 rounded-lg">
        <div className="text-sm font-medium text-red-700">Unknown Block</div>
        <div className="text-xs text-red-600">{type}</div>
      </div>
    );
  }

  const inputs = block.handles?.inputs || [];
  const outputs = block.handles?.outputs || [];

  // Category-based styling
  const categoryStyles: Record<string, string> = {
    input: 'bg-blue-100 border-blue-400 text-blue-900',
    transform: 'bg-purple-100 border-purple-400 text-purple-900', 
    llm: 'bg-emerald-100 border-emerald-400 text-emerald-900',
    tool: 'bg-amber-100 border-amber-400 text-amber-900',
    output: 'bg-rose-100 border-rose-400 text-rose-900',
    control: 'bg-gray-100 border-gray-400 text-gray-900',
  };

  const nodeStyle = categoryStyles[block.category] || 'bg-gray-100 border-gray-400 text-gray-900';

  return (
    <div className={`relative px-4 py-2 min-w-[120px] border-2 rounded-lg ${nodeStyle}`}>
      {/* Input handles */}
      {inputs.map((input, index) => (
        <Handle
          key={input.id}
          type="target"
          position={Position.Left}
          id={input.id}
          style={{
            top: inputs.length === 1 ? '50%' : `${((index + 1) / (inputs.length + 1)) * 100}%`,
            transform: 'translateY(-50%)',
          }}
          className="react-flow__handle-custom"
        />
      ))}

      {/* Node content */}
      <div className="text-center">
        <div className="text-sm font-medium">{data.label}</div>
        <div className="text-xs opacity-70 mt-1">{block.category}</div>
      </div>

      {/* Output handles */}
      {outputs.map((output, index) => (
        <Handle
          key={output.id}
          type="source"
          position={Position.Right}
          id={output.id}
          style={{
            top: outputs.length === 1 ? '50%' : `${((index + 1) / (outputs.length + 1)) * 100}%`,
            transform: 'translateY(-50%)',
          }}
          className="react-flow__handle-custom"
        />
      ))}
    </div>
  );
}

// Define the node types mapping
export const nodeTypes = {
  userInput: CustomNode,
  contextVariable: CustomNode,
  contextMerge: CustomNode,
  llmParse: CustomNode,
  llmSuggestTime: CustomNode,
  googleCalendarGet: CustomNode,
  googleCalendarSchedule: CustomNode,
  userOutput: CustomNode,
  // Add any other block types here
}; 