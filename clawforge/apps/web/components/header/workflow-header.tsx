'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Play, Save, Loader2, ExternalLink, AlertCircle, CheckCircle, User, LogOut, LayoutDashboard, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { GitHubConnect } from '@/components/github/github-connect';
import { useGitHubStore } from '@/lib/stores/github-store';
import { useWorkflowStore } from '@/lib/stores/workflow-store';
import { useAuthStore } from '@/lib/stores/auth-store';

interface WorkflowResult {
  success: boolean;
  message: string;
  project_id?: string;
  github_repo_url?: string;
  pr_url?: string;
  error?: string;
  hint?: string;
  mayHaveSucceeded?: boolean;  // True if workflow might have completed despite error
}

export function WorkflowHeader() {
  const router = useRouter();
  const { isConnected: isGitHubConnected, accessToken, newRepoName, selectedRepo } = useGitHubStore();
  const { isRunning, nodeInputValues, startWorkflow, stopWorkflow, setError } = useWorkflowStore();
  const { user, signOut, isInitialized } = useAuthStore();
  const [isSaving, setIsSaving] = useState(false);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
  };

  // Check if basic nodes have input
  const basicNodeIds = ['app-idea', 'target-users', 'features', 'ui-design'];
  const hasRequiredInputs = basicNodeIds.every((id) => nodeInputValues[id]);
  const filledNodes = basicNodeIds.filter((id) => nodeInputValues[id]);

  // Check if repo name is set
  const hasRepoName = !!(newRepoName || selectedRepo);

  // Check if token exists
  const hasToken = !!accessToken;

  const canRun = isGitHubConnected && hasRequiredInputs && hasRepoName && hasToken;

  // Debug logging (remove in production)
  console.log('Generate Button State:', {
    isGitHubConnected,
    hasToken,
    hasRepoName,
    repoName: newRepoName || selectedRepo,
    hasRequiredInputs,
    filledNodes,
    nodeInputValues,
    canRun,
  });

  const handleSave = () => {
    setIsSaving(true);
    // The state is already persisted via Zustand persist middleware
    setIsSaving(false);
  };

  const handleRun = async () => {
    if (!canRun || !accessToken) return;

    setResult(null);
    startWorkflow();

    try {
      const response = await fetch('/api/workflow/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appIdea: nodeInputValues['app-idea'],
          targetUsers: nodeInputValues['target-users'],
          features: nodeInputValues['features'],
          uiDesign: nodeInputValues['ui-design'],
          // Advanced options if set
          architecture: nodeInputValues['architecture'],
          backend: nodeInputValues['backend'],
          codeSettings: nodeInputValues['code-settings'],
          quality: nodeInputValues['quality'],
          environment: nodeInputValues['environment'],
          // GitHub config
          github: {
            token: accessToken,
            repoName: newRepoName || selectedRepo || 'my-flutter-app',
            isNewRepo: !!newRepoName,
          },
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setResult({
          success: true,
          message: data.message || 'App generated successfully!',
          project_id: data.project_id || data.workflow_id,
          github_repo_url: data.github_repo_url,
          pr_url: data.pr_url,
        });
      } else {
        // Check if this might be a timeout/connection issue where workflow actually succeeded
        const mayHaveSucceeded = data.hint?.includes('may have completed') ||
                                  data.error?.includes('Connection') ||
                                  data.error?.includes('interrupted') ||
                                  response.status === 503;
        setResult({
          success: false,
          message: data.error || 'Workflow failed',
          error: data.details?.toString(),
          hint: data.hint,
          mayHaveSucceeded,
        });
        setError(data.error);
      }
    } catch (err) {
      // Network errors might mean the workflow actually completed
      setResult({
        success: false,
        message: 'Connection to server was lost',
        error: err instanceof Error ? err.message : 'Unknown error',
        hint: 'The workflow may have completed successfully. Check your GitHub account for a new repository.',
        mayHaveSucceeded: true,
      });
      setError('Connection to server was lost');
    } finally {
      stopWorkflow();
    }
  };

  const getButtonTitle = () => {
    if (!isGitHubConnected) return 'Connect GitHub first';
    if (!hasToken) return 'GitHub token missing - reconnect GitHub';
    if (!hasRequiredInputs) {
      const missing = basicNodeIds.filter((id) => !nodeInputValues[id]);
      return `Complete: ${missing.join(', ')} (click nodes to add)`;
    }
    if (!hasRepoName) return 'Set a repository name in GitHub settings';
    return 'Generate your Flutter app';
  };

  return (
    <>
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600 text-white font-bold">
            C
          </div>
          <span className="font-semibold text-zinc-100">ClawForge</span>
          <span className="text-xs text-zinc-500 ml-2">AI Flutter App Builder</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          {/* GitHub Status */}
          <GitHubConnect variant="compact" />

          {/* Divider */}
          <div className="h-6 w-px bg-zinc-800" />

          {/* Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 rounded-md bg-zinc-800 px-3 py-1.5 text-sm font-medium text-zinc-200 hover:bg-zinc-700 disabled:opacity-50"
            >
              {isSaving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save
            </button>

            <button
              onClick={handleRun}
              disabled={!canRun || isRunning}
              className={cn(
                'flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-medium transition-all',
                canRun
                  ? 'bg-violet-600 text-white hover:bg-violet-700'
                  : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
              )}
              title={getButtonTitle()}
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Generate App
                </>
              )}
            </button>
          </div>

          {/* Divider */}
          <div className="h-6 w-px bg-zinc-800" />

          {/* User Menu / Auth */}
          {isInitialized && (
            user ? (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
                    <User className="w-4 h-4" />
                  </div>
                  <span className="text-sm hidden sm:block">{user.email?.split('@')[0]}</span>
                </button>

                {showUserMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowUserMenu(false)}
                    />
                    <div className="absolute right-0 top-full mt-2 w-48 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50">
                      <div className="p-2">
                        <div className="px-3 py-2 border-b border-zinc-800">
                          <p className="text-sm text-white font-medium truncate">{user.email}</p>
                        </div>
                        <Link
                          href="/"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md transition-colors mt-1"
                        >
                          <LayoutDashboard className="w-4 h-4" />
                          Dashboard
                        </Link>
                        <Link
                          href="/settings"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md transition-colors"
                        >
                          <Settings className="w-4 h-4" />
                          Settings
                        </Link>
                        <button
                          onClick={() => {
                            setShowUserMenu(false);
                            handleSignOut();
                          }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-zinc-800 rounded-md transition-colors"
                        >
                          <LogOut className="w-4 h-4" />
                          Sign out
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-sm text-zinc-400 hover:text-white transition-colors px-3 py-1.5"
                >
                  Sign in
                </Link>
                <Link
                  href="/signup"
                  className="text-sm bg-violet-600 hover:bg-violet-500 text-white px-3 py-1.5 rounded-md transition-colors"
                >
                  Sign up
                </Link>
              </div>
            )
          )}
        </div>
      </header>

      {/* Result Modal */}
      {result && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-900 p-6 shadow-2xl">
            <div className="flex items-start gap-4">
              {result.success ? (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-green-500/20">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                </div>
              ) : (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-500/20">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
              )}
              <div className="flex-1">
                <h3 className={cn(
                  'text-lg font-semibold',
                  result.success ? 'text-green-400' : 'text-red-400'
                )}>
                  {result.success ? 'App Generated!' : 'Generation Failed'}
                </h3>
                <p className="mt-1 text-sm text-zinc-400">{result.message}</p>

                {result.error && (
                  <p className="mt-2 text-xs text-red-400 bg-red-500/10 rounded p-2">
                    {result.error}
                  </p>
                )}

                {result.hint && (
                  <p className="mt-2 text-xs text-amber-400 bg-amber-500/10 rounded p-2">
                    💡 {result.hint}
                  </p>
                )}

                {result.mayHaveSucceeded && (
                  <div className="mt-3 flex gap-2">
                    <a
                      href="https://github.com/new"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 flex items-center justify-center gap-2 text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-3 py-2 rounded-lg transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Check GitHub
                    </a>
                    <button
                      onClick={() => {
                        setResult(null);
                        router.push('/');
                      }}
                      className="flex-1 text-sm bg-violet-600 hover:bg-violet-500 text-white px-3 py-2 rounded-lg transition-colors"
                    >
                      Go to Dashboard
                    </button>
                  </div>
                )}

                {result.success && (
                  <div className="mt-4 space-y-2">
                    {result.github_repo_url && (
                      <a
                        href={result.github_repo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300"
                      >
                        <ExternalLink className="h-4 w-4" />
                        View Repository
                      </a>
                    )}
                    {result.pr_url && (
                      <a
                        href={result.pr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300"
                      >
                        <ExternalLink className="h-4 w-4" />
                        View Pull Request
                      </a>
                    )}
                  </div>
                )}

                {result.success && result.project_id && (
                  <button
                    onClick={() => {
                      setResult(null);
                      router.push(`/project/${result.project_id}`);
                    }}
                    className="mt-4 w-full rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
                  >
                    Continue Developing →
                  </button>
                )}
              </div>
            </div>
            <button
              onClick={() => setResult(null)}
              className="mt-6 w-full rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-200 hover:bg-zinc-700"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
