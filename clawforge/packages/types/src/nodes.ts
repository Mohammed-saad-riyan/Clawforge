/**
 * Node Types
 * Types for workflow nodes displayed on the canvas
 */

import type { NodeStatus } from "./workflow";

export type WorkflowNodeType =
  | "app_idea"
  | "target_users"
  | "features"
  | "ui_spec"
  | "architecture"
  | "backend"
  | "environment"
  | "code_generation"
  | "evaluation"
  | "github_publish";

export interface WorkflowNodeData {
  label: string;
  description: string;
  step: number;
  status: NodeStatus;
  input?: string;
  output?: Record<string, unknown>;
  costCents?: number;
  tokens?: number;
}

export interface WorkflowNodePosition {
  x: number;
  y: number;
}

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  position: WorkflowNodePosition;
  data: WorkflowNodeData;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  animated?: boolean;
}

export interface CanvasState {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selectedNodeId: string | null;
}

export const NODE_LABELS: Record<WorkflowNodeType, string> = {
  app_idea: "App Idea",
  target_users: "Target Users",
  features: "Features",
  ui_spec: "UI Design",
  architecture: "Architecture",
  backend: "Backend",
  environment: "Environment",
  code_generation: "Code Generation",
  evaluation: "Evaluation",
  github_publish: "GitHub Publish",
};

export const NODE_DESCRIPTIONS: Record<WorkflowNodeType, string> = {
  app_idea: "Define your app concept and core value proposition",
  target_users: "Identify primary users and their needs",
  features: "List and prioritize app features",
  ui_spec: "Design screens, navigation, and visual style",
  architecture: "Choose tech stack and app structure",
  backend: "Configure backend services and APIs",
  environment: "Set up environment variables and secrets",
  code_generation: "Generate Flutter app code",
  evaluation: "Review and improve code quality",
  github_publish: "Push to GitHub and create PR",
};
