import { create } from 'zustand';

export interface ProjectFile {
  path: string;
  content: string;
  language?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  filesChanged?: string[];
}

export interface Project {
  id: string;
  appName: string;
  appIdea: string;
  targetUsers: string;
  features: string;
  uiDesign: string;
  githubRepo: string;
  files: ProjectFile[];
  messages: ChatMessage[];
  fullSpec: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  totalCostCents: number;
  iterationCount: number;
}

interface ProjectState {
  // Current project
  currentProject: Project | null;
  projects: Project[];

  // Loading states
  isLoading: boolean;
  isSending: boolean;
  isPushing: boolean;

  // Error handling
  error: string | null;

  // Selected file for viewing
  selectedFile: ProjectFile | null;

  // Actions
  setCurrentProject: (project: Project | null) => void;
  setProjects: (projects: Project[]) => void;
  setSelectedFile: (file: ProjectFile | null) => void;
  setLoading: (loading: boolean) => void;
  setSending: (sending: boolean) => void;
  setPushing: (pushing: boolean) => void;
  setError: (error: string | null) => void;

  // API actions
  fetchProjects: () => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  sendMessage: (projectId: string, message: string) => Promise<ChatMessage | null>;
  pushToGithub: (projectId: string, githubToken: string, commitMessage?: string) => Promise<boolean>;

  // Helpers
  addMessage: (message: ChatMessage) => void;
  updateFiles: (files: ProjectFile[]) => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  currentProject: null,
  projects: [],
  isLoading: false,
  isSending: false,
  isPushing: false,
  error: null,
  selectedFile: null,

  setCurrentProject: (project) => set({ currentProject: project }),
  setProjects: (projects) => set({ projects }),
  setSelectedFile: (file) => set({ selectedFile: file }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSending: (sending) => set({ isSending: sending }),
  setPushing: (pushing) => set({ isPushing: pushing }),
  setError: (error) => set({ error }),

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch('/api/projects');
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to fetch projects');
      }
      const projects = await response.json();
      set({ projects, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch projects',
        isLoading: false
      });
    }
  },

  fetchProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`/api/projects/${id}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to fetch project');
      }
      const project = await response.json();

      // Transform from snake_case to camelCase
      const transformedProject: Project = {
        id: project.project_id || project.id,
        appName: project.app_name,
        appIdea: project.app_idea,
        targetUsers: project.target_users,
        features: project.features,
        uiDesign: project.ui_design,
        githubRepo: project.github_repo,
        files: project.files || [],
        messages: (project.messages || []).map((m: Record<string, unknown>) => ({
          id: m.id || crypto.randomUUID(),
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
          filesChanged: m.files_changed || [],
        })),
        fullSpec: project.full_spec || {},
        createdAt: project.created_at,
        updatedAt: project.updated_at,
        totalCostCents: project.total_cost_cents || 0,
        iterationCount: project.iteration_count || 0,
      };

      set({ currentProject: transformedProject, isLoading: false });

      // Auto-select first file if available
      if (transformedProject.files.length > 0 && !get().selectedFile) {
        set({ selectedFile: transformedProject.files[0] });
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch project',
        isLoading: false
      });
    }
  },

  sendMessage: async (projectId: string, message: string) => {
    set({ isSending: true, error: null });

    // Optimistically add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    get().addMessage(userMessage);

    try {
      const response = await fetch(`/api/projects/${projectId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to send message');
      }

      const result = await response.json();

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: result.message_id || crypto.randomUUID(),
        role: 'assistant',
        content: result.assistant_message,
        timestamp: new Date().toISOString(),
        filesChanged: result.files_changed || [],
      };
      get().addMessage(assistantMessage);

      // Refresh project to get updated files
      await get().fetchProject(projectId);

      set({ isSending: false });
      return assistantMessage;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to send message',
        isSending: false
      });
      return null;
    }
  },

  pushToGithub: async (projectId: string, githubToken: string, commitMessage?: string) => {
    set({ isPushing: true, error: null });
    try {
      const response = await fetch(`/api/projects/${projectId}/push`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          githubToken,
          commitMessage: commitMessage || 'Update from ClawForge iterative development',
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to push to GitHub');
      }

      set({ isPushing: false });
      return true;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to push to GitHub',
        isPushing: false
      });
      return false;
    }
  },

  addMessage: (message: ChatMessage) => {
    const project = get().currentProject;
    if (project) {
      set({
        currentProject: {
          ...project,
          messages: [...project.messages, message],
        },
      });
    }
  },

  updateFiles: (files: ProjectFile[]) => {
    const project = get().currentProject;
    if (project) {
      set({
        currentProject: {
          ...project,
          files,
        },
      });
    }
  },
}));
