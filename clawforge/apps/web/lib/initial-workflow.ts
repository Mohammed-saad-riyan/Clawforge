import type { Node, Edge } from '@xyflow/react';
import type { WorkflowNodeData } from '@/components/nodes/workflow-node';

/**
 * ClawForge Workflow Structure
 *
 * BASIC FLOW (On canvas by default):
 * 1. App Idea - What's your app about?
 * 2. Target Users - Who will use it?
 * 3. Features - What should it do?
 * 4. UI Design - How should it look?
 * 5. Generate & Publish - Create code and push to GitHub
 *
 * ADVANCED OPTIONS (In sidebar - drag to add):
 * - Architecture, Backend, Environment, Code Settings, Quality
 * - Smart defaults used if not added
 *
 * GitHub connection is MANDATORY for code delivery
 */

// ========== BASIC FLOW NODES (Default on canvas) ==========
export const basicNodes: Node<WorkflowNodeData>[] = [
  {
    id: 'app-idea',
    type: 'workflow',
    position: { x: 250, y: 50 },
    data: {
      label: 'App Idea',
      description: 'Describe your app in plain language. What problem does it solve?',
      icon: 'lightbulb',
      status: 'idle',
      stepNumber: 1,
      section: 'basic',
      agent: 'planner',
    },
  },
  {
    id: 'target-users',
    type: 'workflow',
    position: { x: 250, y: 170 },
    data: {
      label: 'Target Users',
      description: 'Who will use your app? Students, businesses, everyone?',
      icon: 'users',
      status: 'idle',
      stepNumber: 2,
      section: 'basic',
      agent: 'planner',
    },
  },
  {
    id: 'features',
    type: 'workflow',
    position: { x: 250, y: 290 },
    data: {
      label: 'Features',
      description: 'List the main things your app should do',
      icon: 'list-checks',
      status: 'idle',
      stepNumber: 3,
      section: 'basic',
      agent: 'planner',
    },
  },
  {
    id: 'ui-design',
    type: 'workflow',
    position: { x: 250, y: 410 },
    data: {
      label: 'UI Design',
      description: 'Pick a style: Modern, Minimal, Playful, or Professional',
      icon: 'palette',
      status: 'idle',
      stepNumber: 4,
      section: 'basic',
      agent: 'planner',
    },
  },
  {
    id: 'generate-publish',
    type: 'workflow',
    position: { x: 250, y: 530 },
    data: {
      label: 'Generate & Publish',
      description: 'AI generates your Flutter app and pushes to GitHub',
      icon: 'rocket',
      status: 'idle',
      stepNumber: 5,
      section: 'basic',
      agent: 'orchestrator',
    },
  },
];

// ========== BASIC EDGES ==========
export const basicEdges: Edge[] = [
  { id: 'e-idea-users', source: 'app-idea', target: 'target-users', animated: true },
  { id: 'e-users-features', source: 'target-users', target: 'features', animated: true },
  { id: 'e-features-ui', source: 'features', target: 'ui-design', animated: true },
  { id: 'e-ui-generate', source: 'ui-design', target: 'generate-publish', animated: true },
];

// ========== ADVANCED NODE TEMPLATES (For sidebar drag-drop) ==========
export type AdvancedNodeTemplate = {
  id: string;
  label: string;
  description: string;
  icon: string;
  agent: string;
  defaultValue: Record<string, unknown>;
};

export const advancedNodeTemplates: AdvancedNodeTemplate[] = [
  {
    id: 'architecture',
    label: 'Architecture',
    description: 'State: Riverpod | Navigation: go_router | DB: Drift',
    icon: 'cog',
    agent: 'planner',
    defaultValue: { state: 'riverpod', nav: 'go_router', db: 'drift' },
  },
  {
    id: 'backend',
    label: 'Backend & APIs',
    description: 'Firebase, Supabase, custom REST, or offline-first',
    icon: 'server',
    agent: 'planner',
    defaultValue: { type: 'offline-first' },
  },
  {
    id: 'environment',
    label: 'Environment',
    description: 'API keys and secrets (stored securely)',
    icon: 'key',
    agent: 'none',
    defaultValue: {},
  },
  {
    id: 'code-settings',
    label: 'Code Settings',
    description: 'Defensive prompts, test coverage, documentation level',
    icon: 'code',
    agent: 'coder',
    defaultValue: { defensive: true, tests: 'basic', docs: 'inline' },
  },
  {
    id: 'quality',
    label: 'Quality & Polish',
    description: 'Accessibility level, performance optimization',
    icon: 'sparkles',
    agent: 'claws',
    defaultValue: { a11y: 'standard', performance: 'balanced' },
  },
];

// Helper to create a node from template when dropped
export function createAdvancedNode(
  templateId: string,
  position: { x: number; y: number }
): Node<WorkflowNodeData> | null {
  const template = advancedNodeTemplates.find((t) => t.id === templateId);
  if (!template) return null;

  return {
    id: template.id,
    type: 'workflow',
    position,
    data: {
      label: template.label,
      description: template.description,
      icon: template.icon,
      status: 'idle',
      stepNumber: 0,
      section: 'advanced',
      agent: template.agent,
      defaultValue: template.defaultValue,
    },
  };
}

// Helper to create edge from advanced node to generate-publish
export function createAdvancedEdge(nodeId: string): Edge {
  return {
    id: `e-${nodeId}-generate`,
    source: nodeId,
    target: 'generate-publish',
    animated: false,
    style: { strokeDasharray: '5,5', stroke: '#f59e0b' },
  };
}

// Default exports for initial canvas state
export const initialNodes = basicNodes;
export const initialEdges = basicEdges;

// ========== ORCHESTRATOR ROUTING ==========
export type AgentType = 'planner' | 'coder' | 'claws' | 'github' | 'orchestrator' | 'none';

export const nodeToAgentMapping: Record<string, AgentType> = {
  'app-idea': 'planner',
  'target-users': 'planner',
  'features': 'planner',
  'ui-design': 'planner',
  'architecture': 'planner',
  'backend': 'planner',
  'environment': 'none',
  'code-settings': 'coder',
  'quality': 'claws',
  'generate-publish': 'orchestrator',
};

// Connection suggestions based on what makes sense
export const connectionSuggestions: Record<string, string[]> = {
  'architecture': ['generate-publish'],
  'backend': ['generate-publish', 'environment'],
  'environment': ['generate-publish', 'backend'],
  'code-settings': ['generate-publish', 'quality'],
  'quality': ['generate-publish'],
};
