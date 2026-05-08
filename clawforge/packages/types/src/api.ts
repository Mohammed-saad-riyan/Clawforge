/**
 * API Types
 * Types for API requests and responses
 */

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Health check
export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  services: ServiceHealth[];
}

export interface ServiceHealth {
  name: string;
  status: "up" | "down" | "unknown";
  latencyMs?: number;
}

// LLM Usage
export interface LLMUsage {
  model: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  costCents: number;
  durationMs: number;
}

// Agent Types
export type AgentType = "router" | "planner" | "coder" | "claws" | "github";

export interface AgentResult<T = unknown> {
  success: boolean;
  output?: T;
  error?: string;
  usage?: LLMUsage;
}

// WebSocket Events
export type WSEventType =
  | "workflow:started"
  | "workflow:step:started"
  | "workflow:step:completed"
  | "workflow:step:error"
  | "workflow:completed"
  | "workflow:error";

export interface WSEvent<T = unknown> {
  type: WSEventType;
  workflowId: string;
  timestamp: string;
  data: T;
}

export interface StepStartedEvent {
  step: number;
  nodeName: string;
}

export interface StepCompletedEvent {
  step: number;
  nodeName: string;
  output: Record<string, unknown>;
  costCents: number;
  tokens: number;
}

export interface StepErrorEvent {
  step: number;
  nodeName: string;
  error: string;
}

export interface WorkflowCompletedEvent {
  githubRepoUrl: string | null;
  qualityScore: number;
  totalCostCents: number;
  totalTokens: number;
}
