'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  ExternalLink,
  GitBranch,
  Loader2,
  Upload,
  Code2,
  MessageSquare,
  Settings,
  Check,
  X,
  RefreshCw,
} from 'lucide-react';
import { useProjectStore } from '@/lib/stores/project-store';
import { useGitHubStore } from '@/lib/stores/github-store';
import { FileTree } from '@/components/project/file-tree';
import { CodeViewer } from '@/components/project/code-viewer';
import { ProjectChat } from '@/components/project/project-chat';

type ViewMode = 'code' | 'chat';

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const {
    currentProject,
    selectedFile,
    isLoading,
    isSending,
    isPushing,
    error,
    fetchProject,
    setSelectedFile,
    sendMessage,
    pushToGithub,
    setError,
  } = useProjectStore();

  const { accessToken, isConnected } = useGitHubStore();

  const [viewMode, setViewMode] = useState<ViewMode>('chat');
  const [showPushModal, setShowPushModal] = useState(false);
  const [commitMessage, setCommitMessage] = useState('');
  const [pushSuccess, setPushSuccess] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchProject(projectId);
    }
  }, [projectId, fetchProject]);

  const handleSendMessage = async (message: string) => {
    await sendMessage(projectId, message);
  };

  const handlePush = async () => {
    if (!accessToken) {
      setError('GitHub token not found. Please reconnect GitHub.');
      return;
    }

    const success = await pushToGithub(
      projectId,
      accessToken,
      commitMessage || 'Update from ClawForge'
    );

    if (success) {
      setPushSuccess(true);
      setTimeout(() => {
        setShowPushModal(false);
        setPushSuccess(false);
        setCommitMessage('');
      }, 2000);
    }
  };

  if (isLoading && !currentProject) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin mx-auto mb-4" />
          <p className="text-zinc-400">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!currentProject) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-zinc-400 mb-4">Project not found</p>
          <Link
            href="/"
            className="text-violet-400 hover:text-violet-300 flex items-center gap-2 justify-center"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-semibold text-white">
                {currentProject.appName}
              </h1>
              <p className="text-xs text-zinc-500 line-clamp-1 max-w-md">
                {currentProject.appIdea}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex bg-zinc-800/50 rounded-lg p-1">
              <button
                onClick={() => setViewMode('code')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
                  viewMode === 'code'
                    ? 'bg-zinc-700 text-white'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <Code2 className="w-4 h-4" />
                Code
              </button>
              <button
                onClick={() => setViewMode('chat')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
                  viewMode === 'chat'
                    ? 'bg-zinc-700 text-white'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                Chat
                {currentProject.messages.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs bg-violet-500/20 text-violet-400 rounded-full">
                    {currentProject.messages.length}
                  </span>
                )}
              </button>
            </div>

            {/* Refresh button */}
            <button
              onClick={() => fetchProject(projectId)}
              disabled={isLoading}
              className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh project"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            {/* GitHub link */}
            {currentProject.githubRepo && (
              <a
                href={`https://github.com/${currentProject.githubRepo}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <GitBranch className="w-4 h-4" />
                <span className="hidden sm:inline">{currentProject.githubRepo}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}

            {/* Push to GitHub button */}
            <button
              onClick={() => setShowPushModal(true)}
              disabled={isPushing || !isConnected}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
            >
              {isPushing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              Push Changes
            </button>
          </div>
        </div>

        {/* Project stats bar */}
        <div className="flex items-center gap-6 px-4 py-2 border-t border-zinc-800/50 text-xs text-zinc-500">
          <span>{currentProject.files.length} files</span>
          <span>{currentProject.iterationCount} iterations</span>
          <span>${(currentProject.totalCostCents / 100).toFixed(2)} spent</span>
          <span>Updated {new Date(currentProject.updatedAt).toLocaleDateString()}</span>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - File Tree (always visible) */}
        <aside className="w-64 border-r border-zinc-800 bg-zinc-900/30 shrink-0">
          <FileTree
            files={currentProject.files}
            selectedFile={selectedFile}
            onSelectFile={setSelectedFile}
          />
        </aside>

        {/* Main panel - Code or Chat based on mode */}
        <main className="flex-1 flex overflow-hidden">
          {viewMode === 'code' ? (
            <div className="flex-1">
              <CodeViewer file={selectedFile} />
            </div>
          ) : (
            <div className="flex-1 flex">
              {/* Chat panel */}
              <div className="flex-1 border-r border-zinc-800">
                <ProjectChat
                  messages={currentProject.messages}
                  isSending={isSending}
                  onSendMessage={handleSendMessage}
                  error={error}
                />
              </div>
              {/* Code preview (narrower) */}
              <div className="w-1/2 hidden lg:block">
                <CodeViewer file={selectedFile} />
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Push Modal */}
      {showPushModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
              <h3 className="text-lg font-semibold text-white">Push to GitHub</h3>
              <button
                onClick={() => setShowPushModal(false)}
                className="text-zinc-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {pushSuccess ? (
                <div className="text-center py-4">
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Check className="w-6 h-6 text-green-400" />
                  </div>
                  <p className="text-white font-medium">Changes pushed successfully!</p>
                  <p className="text-sm text-zinc-400 mt-1">
                    View your repository on GitHub
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-sm text-zinc-400 mb-4">
                    Push your latest changes to the repository:
                    <span className="text-white ml-1 font-mono">
                      {currentProject.githubRepo}
                    </span>
                  </p>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-zinc-300 mb-2">
                        Commit Message
                      </label>
                      <input
                        type="text"
                        value={commitMessage}
                        onChange={(e) => setCommitMessage(e.target.value)}
                        placeholder="Update from ClawForge"
                        className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                      />
                    </div>

                    {error && (
                      <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                        <p className="text-sm text-red-400">{error}</p>
                      </div>
                    )}

                    <button
                      onClick={handlePush}
                      disabled={isPushing}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 text-white font-medium rounded-lg transition-colors"
                    >
                      {isPushing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Pushing...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Push Changes
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
