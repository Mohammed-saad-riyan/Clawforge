import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface GitHubUser {
  login: string;
  id: number;
  avatar_url: string;
  name: string | null;
}

export interface GitHubState {
  // Connection state
  isConnected: boolean;
  user: GitHubUser | null;
  accessToken: string | null;

  // Repository state
  selectedRepo: string | null;
  newRepoName: string | null;

  // Actions
  connect: (user: GitHubUser, accessToken: string) => void;
  disconnect: () => void;
  setSelectedRepo: (repo: string | null) => void;
  setNewRepoName: (name: string | null) => void;
}

export const useGitHubStore = create<GitHubState>()(
  persist(
    (set) => ({
      // Initial state
      isConnected: false,
      user: null,
      accessToken: null,
      selectedRepo: null,
      newRepoName: null,

      // Actions
      connect: (user, accessToken) =>
        set({
          isConnected: true,
          user,
          accessToken,
        }),

      disconnect: () =>
        set({
          isConnected: false,
          user: null,
          accessToken: null,
          selectedRepo: null,
          newRepoName: null,
        }),

      setSelectedRepo: (repo) => set({ selectedRepo: repo, newRepoName: null }),
      setNewRepoName: (name) => set({ newRepoName: name, selectedRepo: null }),
    }),
    {
      name: 'clawforge-github',
      partialize: (state) => ({
        isConnected: state.isConnected,
        user: state.user,
        accessToken: state.accessToken, // Persisted for dev - use httpOnly cookie in production
        selectedRepo: state.selectedRepo,
        newRepoName: state.newRepoName,
      }),
    }
  )
);
