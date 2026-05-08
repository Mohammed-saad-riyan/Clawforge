import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Node, Edge } from '@xyflow/react';
import type { WorkflowNodeData } from '@/components/nodes/workflow-node';

export interface WorkflowState {
  // Canvas state
  nodes: Node<WorkflowNodeData>[];
  edges: Edge[];

  // Selected node for input panel
  selectedNode: { id: string; data: WorkflowNodeData } | null;

  // Node input values (string or object for each node)
  nodeInputValues: Record<string, string | Record<string, unknown>>;

  // Workflow data (form inputs for each node)
  workflowData: Record<string, Record<string, unknown>>;

  // Execution state
  currentStep: number | null;
  isRunning: boolean;
  error: string | null;

  // Actions
  setNodes: (nodes: Node<WorkflowNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  updateNodeStatus: (nodeId: string, status: WorkflowNodeData['status']) => void;
  setWorkflowData: (nodeId: string, data: Record<string, unknown>) => void;
  selectNode: (node: { id: string; data: WorkflowNodeData } | null) => void;
  saveNodeInput: (nodeId: string, value: string | Record<string, unknown>) => void;
  startWorkflow: () => void;
  stopWorkflow: () => void;
  setCurrentStep: (step: number | null) => void;
  setError: (error: string | null) => void;
  resetWorkflow: () => void;
}

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      // Initial state
      nodes: [],
      edges: [],
      selectedNode: null,
      nodeInputValues: {},
      workflowData: {},
      currentStep: null,
      isRunning: false,
      error: null,

      // Actions
      setNodes: (nodes) => set({ nodes }),
      setEdges: (edges) => set({ edges }),

      updateNodeStatus: (nodeId, status) =>
        set((state) => ({
          nodes: state.nodes.map((node) =>
            node.id === nodeId ? { ...node, data: { ...node.data, status } } : node
          ),
        })),

      setWorkflowData: (nodeId, data) =>
        set((state) => ({
          workflowData: { ...state.workflowData, [nodeId]: data },
        })),

      selectNode: (node) => set({ selectedNode: node }),

      saveNodeInput: (nodeId, value) =>
        set((state) => ({
          nodeInputValues: { ...state.nodeInputValues, [nodeId]: value },
        })),

      startWorkflow: () => set({ isRunning: true, currentStep: 1, error: null }),
      stopWorkflow: () => set({ isRunning: false }),
      setCurrentStep: (step) => set({ currentStep: step }),
      setError: (error) => set({ error, isRunning: false }),

      resetWorkflow: () =>
        set((state) => ({
          workflowData: {},
          nodeInputValues: {},
          currentStep: null,
          isRunning: false,
          error: null,
          selectedNode: null,
          nodes: state.nodes.map((node) => ({
            ...node,
            data: { ...node.data, status: 'idle' as const },
          })),
        })),
    }),
    {
      name: 'clawforge-workflow',
      partialize: (state) => ({
        workflowData: state.workflowData,
        nodeInputValues: state.nodeInputValues,
      }),
    }
  )
);
