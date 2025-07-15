// src/components/panels/Toolbox.tsx
/**
 * Toolbox panel - displays available blocks organized by category
 */

"use client";
import { useUIStore } from "@/store/uiStore";
import { getBlocksCategorized, initializeBlocks } from "@/engine/blocks/registry";
import { BLOCK_CATEGORIES } from "@/config/blocks";
import { Block } from "@/engine/blocks";
import { useState, useEffect, useCallback } from "react";

export default function Toolbox() {
  const { toolboxOpen, togglePanel } = useUIStore();
  const [blocksByCategory, setBlocksByCategory] = useState<Record<string, Block[]>>({});
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['input', 'llm']) // Start with basic categories expanded
  );

  // Smooth drag toggle position
  const [togglePosition, setTogglePosition] = useState(10); // Start at 10th position
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartPosition, setDragStartPosition] = useState(10);
  const [hasDragged, setHasDragged] = useState(false);
  
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setHasDragged(false);
    setDragStartX(e.clientX);
    setDragStartPosition(togglePosition);
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - dragStartX;
    const sensitivity = 0.2; // Reduced sensitivity for better control
    const newPosition = Math.max(0, Math.min(100, dragStartPosition + deltaX * sensitivity));
    
    // Mark that we've actually moved
    if (Math.abs(deltaX) > 3) {
      setHasDragged(true);
    }
    
    setTogglePosition(newPosition);
  }, [isDragging, dragStartX, dragStartPosition]);
  
  const handleMouseUp = useCallback(() => {
    if (!isDragging) return;
    setIsDragging(false);
    
    // Snap to nearest 10th position
    const snappedPosition = Math.round(togglePosition / 10) * 10;
    setTogglePosition(Math.max(10, Math.min(90, snappedPosition)));
  }, [isDragging, togglePosition]);
  
  const handleClick = () => {
    // Only toggle panel if we didn't drag
    if (!hasDragged) {
      togglePanel('toolbox');
    }
    setHasDragged(false); // Reset for next interaction
  };
  
  // Add global mouse event listeners for smooth dragging
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  useEffect(() => {
    // Initialize blocks on component mount
    initializeBlocks();
    setBlocksByCategory(getBlocksCategorized());
  }, []);

  if (!toolboxOpen) {
    return null;
  }

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const categoryIcons: Record<string, string> = Object.fromEntries(
    Object.entries(BLOCK_CATEGORIES).map(([key, category]) => [key, category.icon])
  );

  const categoryNames: Record<string, string> = Object.fromEntries(
    Object.entries(BLOCK_CATEGORIES).map(([key, category]) => [key, category.name])
  );

  const categoryColors: Record<string, string> = {
    input: 'bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100',
    transform: 'bg-purple-50 border-purple-200 text-purple-800 hover:bg-purple-100',
    llm: 'bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100',
    tool: 'bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100',
    output: 'bg-rose-50 border-rose-200 text-rose-800 hover:bg-rose-100',
    control: 'bg-gray-50 border-gray-200 text-gray-800 hover:bg-gray-100',
  };

  return (
    <aside className="w-64 border-r border-gray-200 bg-white p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900">Toolbox</h2>
        <button
          onMouseDown={handleMouseDown}
          onClick={handleClick}
          className={`text-gray-500 hover:text-gray-700 select-none transition-colors ${
            isDragging ? 'cursor-grabbing' : 'cursor-grab'
          }`}
          style={{ 
            transform: `translateX(${togglePosition - 10}px)`,
            transition: isDragging ? 'none' : 'transform 0.3s ease-out',
            userSelect: 'none',
            WebkitUserSelect: 'none',
            MozUserSelect: 'none',
            msUserSelect: 'none'
          }}
        >
          ✕
        </button>
      </div>

      <div className="space-y-3">
        {Object.entries(blocksByCategory).map(([category, blocks]) => {
          if (!blocks || blocks.length === 0) return null;
          
          const isExpanded = expandedCategories.has(category);
          const categoryBlocks = blocks;

          return (
            <div key={category} className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleCategory(category)}
                className="w-full px-3 py-2 text-left font-medium text-gray-700 hover:bg-gray-50 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <span>{categoryIcons[category]}</span>
                  <span>{categoryNames[category]}</span>
                  <span className="text-xs text-gray-500">({categoryBlocks.length})</span>
                </div>
                <span className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                  ▶
                </span>
              </button>

              {isExpanded && (
                <div className="px-2 pb-2 space-y-1">
                  {categoryBlocks.map((block) => (
                    <div
                      key={block.type}
                      className={`p-3 rounded border cursor-grab active:cursor-grabbing ${categoryColors[category]}`}
          draggable
                      onDragStart={(e) => {
            e.dataTransfer.setData(
              "application/block",
                          JSON.stringify({
                            type: block.type,
                            label: block.label,
                          })
                        );
                      }}
        >
                      <div className="font-medium text-sm">
                        {block.label}
                      </div>
                      <div className="text-xs opacity-90 mt-1">
                        {block.description}
                      </div>
                      
                      {/* Show connection info */}
                      <div className="flex justify-between text-xs opacity-80 mt-2">
                        <span>
                          {block.handles.inputs.length} in
                        </span>
                        <span>
                          {block.handles.outputs.length} out
                        </span>
                      </div>
        </div>
      ))}
                </div>
              )}
            </div>
          );
        })}
      </div>


    </aside>
  );
}
