'use client';

import { useState } from 'react';
import { Github, LogOut, Check, Loader2, Key, ExternalLink, FolderGit } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useGitHubStore } from '@/lib/stores/github-store';

interface GitHubConnectProps {
  variant?: 'button' | 'compact';
  className?: string;
}

export function GitHubConnect({ variant = 'button', className }: GitHubConnectProps) {
  const { isConnected, user, disconnect, connect, newRepoName, setNewRepoName } = useGitHubStore();
  const [isLoading, setIsLoading] = useState(false);
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [showRepoInput, setShowRepoInput] = useState(false);
  const [token, setToken] = useState('');
  const [repoName, setRepoName] = useState('');
  const [error, setError] = useState('');

  const handleConnect = async () => {
    if (!token.trim()) {
      setError('Please enter a token');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Validate token by fetching user info from GitHub API
      const response = await fetch('https://api.github.com/user', {
        headers: {
          Authorization: `Bearer ${token.trim()}`,
          Accept: 'application/vnd.github.v3+json',
        },
      });

      if (!response.ok) {
        throw new Error('Invalid token or API error');
      }

      const userData = await response.json();

      connect(
        {
          login: userData.login,
          id: userData.id,
          avatar_url: userData.avatar_url,
          name: userData.name,
        },
        token.trim()
      );

      setShowTokenInput(false);
      setToken('');
    } catch (err) {
      setError('Invalid token. Make sure it has repo permissions.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    disconnect();
  };

  const handleSetRepo = () => {
    if (repoName.trim()) {
      setNewRepoName(repoName.trim().toLowerCase().replace(/\s+/g, '-'));
      setShowRepoInput(false);
    }
  };

  if (variant === 'compact') {
    return (
      <div className={cn('flex items-center gap-2 relative', className)}>
        {isConnected ? (
          <>
            <div className="flex items-center gap-2">
              {user?.avatar_url && (
                <img
                  src={user.avatar_url}
                  alt={user.login}
                  className="h-6 w-6 rounded-full border border-zinc-700"
                />
              )}
              <span className="text-sm text-zinc-300">{user?.login}</span>
              <Check className="h-4 w-4 text-green-400" />
            </div>

            {/* Repo name button/display */}
            {newRepoName ? (
              <button
                onClick={() => setShowRepoInput(true)}
                className="flex items-center gap-1 rounded-md bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                title="Change repository name"
              >
                <FolderGit className="h-3 w-3" />
                {newRepoName}
              </button>
            ) : (
              <button
                onClick={() => setShowRepoInput(true)}
                className="flex items-center gap-1 rounded-md bg-amber-500/20 px-2 py-1 text-xs text-amber-400 hover:bg-amber-500/30"
              >
                <FolderGit className="h-3 w-3" />
                Set Repo Name
              </button>
            )}

            <button
              onClick={handleDisconnect}
              className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300"
              title="Disconnect GitHub"
            >
              <LogOut className="h-4 w-4" />
            </button>

            {/* Repo name dropdown */}
            {showRepoInput && (
              <div className="absolute right-0 top-full mt-2 w-72 rounded-lg border border-zinc-700 bg-zinc-900 p-4 shadow-xl z-50">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-zinc-200">Repository Name</h3>
                    <button
                      onClick={() => setShowRepoInput(false)}
                      className="text-zinc-500 hover:text-zinc-300"
                    >
                      ×
                    </button>
                  </div>
                  <p className="text-xs text-zinc-400">
                    A new repository will be created with this name.
                  </p>
                  <input
                    type="text"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    placeholder="my-flutter-app"
                    className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none"
                    onKeyDown={(e) => e.key === 'Enter' && handleSetRepo()}
                  />
                  <button
                    onClick={handleSetRepo}
                    disabled={!repoName.trim()}
                    className="w-full rounded-md bg-violet-600 px-3 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
                  >
                    Set Repository
                  </button>
                </div>
              </div>
            )}
          </>
        ) : showTokenInput ? (
          <div className="absolute right-0 top-full mt-2 w-80 rounded-lg border border-zinc-700 bg-zinc-900 p-4 shadow-xl z-50">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-zinc-200">Connect GitHub</h3>
                <button
                  onClick={() => setShowTokenInput(false)}
                  className="text-zinc-500 hover:text-zinc-300"
                >
                  ×
                </button>
              </div>
              <p className="text-xs text-zinc-400">
                Enter a Personal Access Token with <code className="text-violet-400">repo</code> scope.
              </p>
              <a
                href="https://github.com/settings/tokens/new?scopes=repo&description=ClawForge"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300"
              >
                <ExternalLink className="h-3 w-3" />
                Create token on GitHub
              </a>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxx"
                className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none"
              />
              {error && <p className="text-xs text-red-400">{error}</p>}
              <button
                onClick={handleConnect}
                disabled={isLoading || !token.trim()}
                className="w-full flex items-center justify-center gap-2 rounded-md bg-violet-600 px-3 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Key className="h-4 w-4" />
                )}
                Connect
              </button>
            </div>
          </div>
        ) : null}
        {!isConnected && (
          <button
            onClick={() => setShowTokenInput(true)}
            className="flex items-center gap-2 rounded-md bg-zinc-800 px-3 py-1.5 text-sm text-zinc-200 hover:bg-zinc-700"
          >
            <Github className="h-4 w-4" />
            Connect GitHub
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {isConnected ? (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {user?.avatar_url && (
                <img
                  src={user.avatar_url}
                  alt={user.login}
                  className="h-10 w-10 rounded-full border-2 border-green-500/50"
                />
              )}
              <div>
                <p className="font-medium text-zinc-100">{user?.name || user?.login}</p>
                <p className="text-sm text-zinc-400">@{user?.login}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 rounded-full bg-green-500/20 px-2 py-1 text-xs text-green-400">
                <Check className="h-3 w-3" />
                Connected
              </span>
              <button
                onClick={handleDisconnect}
                className="p-2 rounded-md hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                title="Disconnect GitHub"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-zinc-400">
            Connect your GitHub account to push generated code to your repositories.
          </p>
          <a
            href="https://github.com/settings/tokens/new?scopes=repo&description=ClawForge"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300"
          >
            <ExternalLink className="h-4 w-4" />
            Create a Personal Access Token with repo scope
          </a>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="ghp_xxxxxxxxxxxx"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            onClick={handleConnect}
            disabled={isLoading || !token.trim()}
            className={cn(
              'w-full flex items-center justify-center gap-3 rounded-lg px-4 py-3',
              'text-white font-medium transition-all',
              token.trim()
                ? 'bg-violet-600 hover:bg-violet-700'
                : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <Github className="h-5 w-5" />
                <span>Connect GitHub</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
