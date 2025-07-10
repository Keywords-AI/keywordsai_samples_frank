// src/components/panels/BlockHints.tsx
/**
 * Block Hints Panel - Shows educational hints for selected blocks
 * Replaces the complex Inspector with simple learning aids
 */

import React from 'react';
import { useUIStore } from '../../store/uiStore';
import { useGraphStore } from '../../store/graphStore';
import { getBlock } from '../../engine/blocks/registry';

export function BlockHints() {
  const { selectedNodeId } = useUIStore();
  const { nodes } = useGraphStore();
  
  // Get the selected node
  const selectedNode = selectedNodeId 
    ? nodes.find(node => node.id === selectedNodeId)
    : null;
    
  const block = selectedNode ? getBlock(selectedNode.data.type) : null;
  
  if (!selectedNode || !block) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          💡 Block Hints
        </h3>
        <div className="text-gray-400 text-sm">
          Click on a block to see helpful hints and tips! 
          <br /><br />
          🎯 <strong>Goal:</strong> Connect all blocks to build a workflow that can schedule meetings automatically.
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-white font-medium mb-3 flex items-center gap-2">
        💡 {block.label} - Level {block.level}
      </h3>
      
      <div className="space-y-4">
        {/* Block Description */}
        <div className="bg-gray-800 rounded-lg p-3">
          <p className="text-gray-300 text-sm">{block.description}</p>
        </div>
        
        {/* Input Hint */}
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-3">
          <h4 className="text-blue-300 font-medium text-sm mb-1">📥 Input</h4>
          <p className="text-blue-200 text-sm">{block.hints.inputHint}</p>
        </div>
        
        {/* Output Hint */}
        <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-3">
          <h4 className="text-green-300 font-medium text-sm mb-1">📤 Output</h4>
          <p className="text-green-200 text-sm">{block.hints.outputHint}</p>
        </div>
        
        {/* Usage Example */}
        <div className="bg-purple-900/30 border border-purple-700/50 rounded-lg p-3">
          <h4 className="text-purple-300 font-medium text-sm mb-1">💡 Usage Tip</h4>
          <p className="text-purple-200 text-sm">{block.hints.usageExample}</p>
        </div>
        
        {/* Connection Info */}
        {block.handles.inputs.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-3">
            <h4 className="text-gray-300 font-medium text-sm mb-2">🔗 Connections</h4>
            <div className="space-y-1">
              {block.handles.inputs.map(input => (
                <div key={input.id} className="text-xs text-gray-400">
                  • Input: <span className="text-blue-400">{input.label}</span> ({input.type})
                </div>
              ))}
              {block.handles.outputs.map(output => (
                <div key={output.id} className="text-xs text-gray-400">
                  • Output: <span className="text-green-400">{output.label}</span> ({output.type})
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 