/**
 * Workflow Types
 * Types for the workflow state and operations
 */

export type WorkflowStatus = "idle" | "running" | "completed" | "error" | "paused";

export type NodeStatus = "pending" | "running" | "completed" | "error" | "skipped";

export interface WorkflowState {
  id: string;
  appName: string;
  status: WorkflowStatus;
  currentStep: number;
  completedSteps: number[];
  totalCostCents: number;
  totalTokens: number;
  error: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowInput {
  appName: string;
  userInputs: Record<string, string>;
}

export interface StepInput {
  workflowId: string;
  step: number;
  input: string;
}

export interface WorkflowProgress {
  workflowId: string;
  step: number;
  status: NodeStatus;
  message: string;
  data?: Record<string, unknown>;
  costCents: number;
  tokens: number;
  timestamp: string;
}

export interface WorkflowResult {
  workflowId: string;
  status: WorkflowStatus;
  appName: string;
  githubRepoUrl: string | null;
  qualityScore: number;
  issues: string[];
  totalCostCents: number;
  totalTokens: number;
  generatedFiles: GeneratedFile[];
}

export interface GeneratedFile {
  path: string;
  content: string;
  language: string;
}
