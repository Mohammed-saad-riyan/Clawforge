'use client';

import { useState } from 'react';
import { FolderGit, Plus, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useGitHubStore } from '@/lib/stores/github-store';

interface RepoSelectorProps {
  className?: string;
}

export function RepoSelector({ className }: RepoSelectorProps) {
  const { isConnected, selectedRepo, newRepoName, setSelectedRepo, setNewRepoName } =
    useGitHubStore();
  const [mode, setMode] = useState<'new' | 'existing'>('new');
  const [repoInput, setRepoInput] = useState('');

  if (!isConnected) {
    return (
      <div className={cn('rounded-lg border border-zinc-800 bg-zinc-900 p-4', className)}>
        <p className="text-sm text-zinc-500">Connect GitHub to select a repository</p>
      </div>
    );
  }

  const handleNewRepo = () => {
    if (repoInput.trim()) {
      setNewRepoName(repoInput.trim());
    }
  };

  const handleSelectRepo = (repo: string) => {
    setSelectedRepo(repo);
  };

  // Mock existing repos - in production, fetch from GitHub API
  const mockRepos = [
    'my-flutter-app',
    'awesome-project',
    'mobile-app-v2',
  ];

  return (
    <div className={cn('space-y-4', className)}>
      {/* Mode Toggle */}
      <div className="flex rounded-lg border border-zinc-800 p-1">
        <button
          onClick={() => setMode('new')}
          className={cn(
            'flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors',
            mode === 'new'
              ? 'bg-violet-600 text-white'
              : 'text-zinc-400 hover:text-zinc-200'
          )}
        >
          <Plus className="inline h-4 w-4 mr-1" />
          New Repository
        </button>
        <button
          onClick={() => setMode('existing')}
          className={cn(
            'flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors',
            mode === 'existing'
              ? 'bg-violet-600 text-white'
              : 'text-zinc-400 hover:text-zinc-200'
          )}
        >
          <FolderGit className="inline h-4 w-4 mr-1" />
          Existing
        </button>
      </div>

      {mode === 'new' ? (
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-zinc-300">Repository Name</label>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="my-flutter-app"
                className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none"
              />
              <button
                onClick={handleNewRepo}
                disabled={!repoInput.trim()}
                className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Set
              </button>
            </div>
          </div>
          {newRepoName && (
            <div className="flex items-center gap-2 rounded-lg bg-green-500/10 border border-green-500/30 px-3 py-2">
              <Check className="h-4 w-4 text-green-400" />
              <span className="text-sm text-green-400">
                Will create: <span className="font-mono">{newRepoName}</span>
              </span>
            </div>
          )}
          <p className="text-xs text-zinc-500">
            A new public repository will be created when you generate your app.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <label className="text-sm font-medium text-zinc-300">Select Repository</label>
          <div className="space-y-2">
            {mockRepos.map((repo) => (
              <button
                key={repo}
                onClick={() => handleSelectRepo(repo)}
                className={cn(
                  'w-full flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-colors',
                  selectedRepo === repo
                    ? 'border-violet-500 bg-violet-500/10 text-violet-300'
                    : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-600'
                )}
              >
                <div className="flex items-center gap-2">
                  <FolderGit className="h-4 w-4" />
                  <span className="text-sm font-mono">{repo}</span>
                </div>
                {selectedRepo === repo && <Check className="h-4 w-4 text-violet-400" />}
              </button>
            ))}
          </div>
          <p className="text-xs text-zinc-500">
            Code will be pushed to a new branch in the selected repository.
          </p>
        </div>
      )}
    </div>
  );
}
