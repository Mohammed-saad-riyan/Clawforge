'use client';

import { useCallback, useMemo, useRef } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  type Connection,
  type Node,
  type NodeMouseHandler,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { WorkflowNode, type WorkflowNodeData } from '@/components/nodes/workflow-node';
import { WorkflowSidebar, type DraggableNodeType } from '@/components/sidebar/workflow-sidebar';
import { NodeInputPanel } from '@/components/panel/node-input-panel';
import { useWorkflowStore } from '@/lib/stores/workflow-store';
import {
  initialNodes,
  initialEdges,
  createAdvancedNode,
  createAdvancedEdge,
  advancedNodeTemplates,
} from '@/lib/initial-workflow';

function Flow() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const { screenToFlowPosition } = useReactFlow();

  // Zustand store for node selection and input values
  const { selectedNode, selectNode, saveNodeInput, nodeInputValues } = useWorkflowStore();

  const nodeTypes = useMemo(() => ({ workflow: WorkflowNode }), []);

  // Track which advanced nodes have been added
  const addedAdvancedNodes = useMemo(() => {
    const advancedIds = advancedNodeTemplates.map((t) => t.id);
    return nodes.filter((n) => advancedIds.includes(n.id)).map((n) => n.id);
  }, [nodes]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Handle drag start from sidebar
  const onDragStart = useCallback(
    (event: React.DragEvent, nodeType: DraggableNodeType) => {
      event.dataTransfer.setData('application/reactflow', nodeType.id);
      event.dataTransfer.effectAllowed = 'move';
    },
    []
  );

  // Handle drag over canvas
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop on canvas
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const nodeId = event.dataTransfer.getData('application/reactflow');
      if (!nodeId) return;

      // Check if already added
      if (addedAdvancedNodes.includes(nodeId)) return;

      // Get position where dropped
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // Create the new node
      const newNode = createAdvancedNode(nodeId, position);
      if (!newNode) return;

      // Add node and edge to generate-publish
      setNodes((nds) => [...nds, newNode]);
      setEdges((eds) => [...eds, createAdvancedEdge(nodeId)]);
    },
    [addedAdvancedNodes, screenToFlowPosition, setNodes, setEdges]
  );

  // Handle node deletion (for advanced nodes only)
  const onNodesDelete = useCallback(
    (deletedNodes: Node<WorkflowNodeData>[]) => {
      // Only allow deleting advanced nodes
      const advancedIds = advancedNodeTemplates.map((t) => t.id);
      const toDelete = deletedNodes.filter((n) => advancedIds.includes(n.id));

      if (toDelete.length > 0) {
        setNodes((nds) => nds.filter((n) => !toDelete.find((d) => d.id === n.id)));
        setEdges((eds) =>
          eds.filter((e) => !toDelete.find((d) => e.source === d.id || e.target === d.id))
        );
      }
    },
    [setNodes, setEdges]
  );

  // Handle node click to open input panel
  const onNodeClick: NodeMouseHandler<Node<WorkflowNodeData>> = useCallback(
    (event, node) => {
      // Don't open panel for generate-publish node (it's the final action)
      if (node.id === 'generate-publish') return;
      selectNode({ id: node.id, data: node.data });
    },
    [selectNode]
  );

  // Handle panel close
  const handlePanelClose = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  // Handle save from input panel
  const handleSaveInput = useCallback(
    (nodeId: string, value: string | Record<string, unknown>) => {
      saveNodeInput(nodeId, value);
    },
    [saveNodeInput]
  );

  return (
    <div className="flex h-full w-full">
      {/* Sidebar */}
      <WorkflowSidebar onDragStart={onDragStart} addedNodes={addedAdvancedNodes} />

      {/* Canvas */}
      <div ref={reactFlowWrapper} className="flex-1 h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodesDelete={onNodesDelete}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes as never}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          defaultEdgeOptions={{
            type: 'smoothstep',
            animated: true,
            style: { stroke: '#a78bfa', strokeWidth: 2 },
          }}
          deleteKeyCode={['Backspace', 'Delete']}
          className="bg-zinc-950"
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1}
            color="#27272a"
          />
          <Controls
            className="bg-zinc-900 border border-zinc-800 rounded-lg [&>button]:bg-zinc-900 [&>button]:border-zinc-700 [&>button]:text-zinc-400 [&>button:hover]:bg-zinc-800"
          />
          <MiniMap
            className="bg-zinc-900 border border-zinc-800 rounded-lg"
            nodeColor={(node) => {
              const data = node.data as WorkflowNodeData;
              return data.section === 'advanced' ? '#f59e0b' : '#8b5cf6';
            }}
            maskColor="rgba(9, 9, 11, 0.8)"
          />

          {/* Drop zone indicator */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none">
            <div className="bg-zinc-900/90 border border-zinc-700 rounded-lg px-4 py-2 text-xs text-zinc-400">
              Click nodes to add input • Drag components from sidebar • Delete with Backspace
            </div>
          </div>
        </ReactFlow>
      </div>

      {/* Node Input Panel */}
      <NodeInputPanel
        node={selectedNode}
        onClose={handlePanelClose}
        onSave={handleSaveInput}
        savedValues={nodeInputValues}
      />
    </div>
  );
}

export function WorkflowCanvas() {
  return (
    <ReactFlowProvider>
      <Flow />
    </ReactFlowProvider>
  );
}
