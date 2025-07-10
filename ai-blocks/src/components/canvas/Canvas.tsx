// src/components/canvas/Canvas.tsx
/**
 * Canvas component - main drag-and-drop board using React Flow
 * Integrates with the graph store and UI state management
 */

"use client";
import { useCallback, useRef } from "react";
import ReactFlow, {
  Controls,
  Background,
  Connection,
  ReactFlowProvider,
  useReactFlow,
  NodeMouseHandler,
  EdgeMouseHandler,
} from "react-flow-renderer";
import { useGraphStore } from "@/store/graphStore";
import { useUIStore } from "@/store/uiStore";
import { useRunStore } from "@/store/runStore";
import { nodeTypes } from "./CustomNode";
import { FlowAnimation } from "./FlowAnimation";
import WorkflowSuccessModal from "@/components/modals/WorkflowSuccessModal";
import { useRouter } from "next/navigation";

function InnerCanvas() {
  const router = useRouter();
  
  const { 
    nodes, 
    edges, 
    addNode, 
    addEdge, 
    updateNode,
    deleteNode,
    deleteEdge 
  } = useGraphStore();
  
  const { 
    selectNode, 
    selectEdge, 
    selectedNodeId,
    selectedEdgeId
  } = useUIStore();
  
  const { 
    isRunning, 
    currentNodeId, 
    liveResults,
    showSuccessAnimation,
    setShowSuccessAnimation,
    showSuccessModal,
    validationResult,
    trace,
    setShowSuccessModal
  } = useRunStore();

  const flowWrapper = useRef<HTMLDivElement | null>(null);
  const rfInstance = useReactFlow();

  /* Handle edge creation */
  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) return;
      
      addEdge({
        source: params.source,
        target: params.target,
        sourceHandle: params.sourceHandle || undefined,
        targetHandle: params.targetHandle || undefined,
      });
    },
    [addEdge]
  );

  /* Handle drag-drop to add nodes */
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const raw = event.dataTransfer.getData("application/block");
      if (!raw) return;
      
      const { type, label } = JSON.parse(raw);

      // Translate mouse to canvas coordinates
      const bounds = flowWrapper.current!.getBoundingClientRect();
      const position = rfInstance.project({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top
      });

      addNode({
        type,
        position,
        data: { 
          label,
          params: {} // Initialize with empty params
        }
      });
    },
    [addNode, rfInstance]
  );

  /* Handle node selection */
  const onNodeClick: NodeMouseHandler = useCallback(
    (event, node) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  /* Handle edge selection */
  const onEdgeClick: EdgeMouseHandler = useCallback(
    (event, edge) => {
      selectEdge(edge.id);
    },
    [selectEdge]
  );

  /* Handle canvas click (clear selection) */
  const onPaneClick = useCallback(() => {
    selectNode(null);
    selectEdge(null);
  }, [selectNode, selectEdge]);

  /* Handle node position changes during drag */
  const onNodeDrag = useCallback(
    (event: React.MouseEvent, node: any) => {
      updateNode(node.id, { position: node.position });
    },
    [updateNode]
  );

  /* Handle node position changes when drag stops */
  const onNodeDragStop = useCallback(
    (event: React.MouseEvent, node: any) => {
      updateNode(node.id, { position: node.position });
    },
    [updateNode]
  );

  /* Handle delete key */
  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (selectedNodeId) {
          deleteNode(selectedNodeId);
          selectNode(null);
        } else if (selectedEdgeId) {
          deleteEdge(selectedEdgeId);
          selectEdge(null);
        }
      }
    },
    [selectedNodeId, selectedEdgeId, deleteNode, deleteEdge, selectNode, selectEdge]
  );

  // Enhance nodes with execution state
  const enhancedNodes = nodes.map(node => {
    let className = 'react-flow__node-default';
    
    if (node.id === selectedNodeId) {
      className += ' selected';
    }
    
    if (isRunning) {
      if (node.id === currentNodeId) {
        className += ' executing';
      } else if (liveResults.some(r => r.nodeId === node.id)) {
        const result = liveResults.find(r => r.nodeId === node.id);
        if (result?.metadata.error) {
          className += ' error';
        } else {
          className += ' success';
        }
      }
    }

    return {
      ...node,
      className,
      selected: node.id === selectedNodeId,
    };
  });

  // Enhance edges with selection state
  const enhancedEdges = edges.map(edge => ({
    ...edge,
    selected: edge.id === selectedEdgeId,
    animated: isRunning && liveResults.some(r => r.nodeId === edge.target),
  }));

  return (
    <div
      ref={flowWrapper}
      className="h-full w-full bg-gray-50"
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      onKeyDown={onKeyDown}
      tabIndex={0} // Make div focusable for keyboard events
    >
      <ReactFlow
        nodes={enhancedNodes}
        edges={enhancedEdges}
        nodeTypes={nodeTypes}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onNodeDrag={onNodeDrag}
        onNodeDragStop={onNodeDragStop}
        nodesDraggable={true}
        nodesConnectable={true}
        elementsSelectable={true}
        selectNodesOnDrag={false}
        multiSelectionKeyCode="Meta"
        deleteKeyCode={null} // Handle delete manually
        connectionLineStyle={{ stroke: '#6366f1', strokeWidth: 3 }}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: false,
        }}
      >
        <Background 
          gap={20} 
          size={1}
          color="#e5e7eb"
        />
        <Controls />
      </ReactFlow>
      
      {/* Overlay for disabled state during execution */}
      {isRunning && (
        <div className="absolute inset-0 bg-black bg-opacity-10 flex items-center justify-center pointer-events-none">
          <div className="bg-white px-4 py-2 rounded-lg shadow-lg border">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="text-sm font-medium text-gray-700">
                Executing workflow...
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Success Animation Overlay */}
      <FlowAnimation
        isVisible={showSuccessAnimation}
        onComplete={() => {
          setShowSuccessAnimation(false);
          // Don't auto-open trace console - let user stay on success screen
        }}
      />

      {/* Success Modal with Detailed Traces */}
      {validationResult && (
        <WorkflowSuccessModal
          isOpen={showSuccessModal}
          validationResult={validationResult}
          executionTrace={trace || undefined}
          onClose={() => setShowSuccessModal(false)}
          onNextLevel={() => {
            setShowSuccessModal(false);
            // TODO: Navigate to next level
          }}
          onReplay={() => {
            setShowSuccessModal(false);
            // TODO: Reset current level
          }}
          onReturnToMenu={() => {
            setShowSuccessModal(false);
            router.push('/');
          }}
        />
      )}
    </div>
  );
}

/* Export the provider-wrapped version */
export default function Canvas() {
  return (
    <ReactFlowProvider>
      <InnerCanvas />
    </ReactFlowProvider>
  );
}
