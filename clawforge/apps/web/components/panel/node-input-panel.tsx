'use client';

import { useState, useEffect } from 'react';
import { X, Send, Sparkles, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { WorkflowNodeData } from '@/components/nodes/workflow-node';

interface NodeInputPanelProps {
  node: { id: string; data: WorkflowNodeData } | null;
  onClose: () => void;
  onSave: (nodeId: string, value: string | Record<string, unknown>) => void;
  savedValues: Record<string, string | Record<string, unknown>>;
}

export function NodeInputPanel({ node, onClose, onSave, savedValues }: NodeInputPanelProps) {
  const [value, setValue] = useState('');

  // Load saved value when node changes
  useEffect(() => {
    if (node) {
      const saved = savedValues[node.id];
      setValue(typeof saved === 'string' ? saved : '');
    }
  }, [node, savedValues]);

  if (!node) return null;

  const handleSave = () => {
    if (value.trim()) {
      onSave(node.id, value);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSave();
    }
  };

  const isAdvanced = node.data.section === 'advanced';
  const isSaved = !!savedValues[node.id];

  return (
    <div className="w-96 h-full border-l border-zinc-800 bg-zinc-950 flex flex-col">
      {/* Header */}
      <div className={cn(
        'flex items-center justify-between p-4 border-b border-zinc-800',
        isAdvanced ? 'bg-amber-500/5' : 'bg-violet-500/5'
      )}>
        <div className="flex items-center gap-3">
          {node.data.stepNumber > 0 && (
            <span className={cn(
              'flex h-7 w-7 items-center justify-center rounded-full text-sm font-medium',
              isAdvanced ? 'bg-amber-500/20 text-amber-400' : 'bg-violet-500/20 text-violet-400'
            )}>
              {node.data.stepNumber}
            </span>
          )}
          <div>
            <h2 className="font-semibold text-zinc-100">{node.data.label}</h2>
            <p className="text-xs text-zinc-500">{isAdvanced ? 'Advanced' : 'Required'}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-md hover:bg-zinc-800 text-zinc-400"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Description */}
        <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-3">
          <p className="text-sm text-zinc-300">{node.data.description}</p>
        </div>

        {/* Input area based on node type */}
        <NodeInputArea
          nodeId={node.id}
          nodeData={node.data}
          value={value}
          onChange={setValue}
          onKeyDown={handleKeyDown}
        />

        {/* Tips */}
        <NodeTips nodeId={node.id} />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-zinc-800 space-y-3">
        {isSaved && (
          <div className="flex items-center gap-2 text-xs text-green-400">
            <Check className="h-3 w-3" />
            <span>Saved</span>
          </div>
        )}
        <button
          onClick={handleSave}
          disabled={!value.trim()}
          className={cn(
            'w-full flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all',
            value.trim()
              ? 'bg-violet-600 text-white hover:bg-violet-700'
              : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
          )}
        >
          <Send className="h-4 w-4" />
          Save & Continue
        </button>
        <p className="text-[10px] text-zinc-600 text-center">⌘ + Enter to save</p>
      </div>
    </div>
  );
}

function NodeInputArea({
  nodeId,
  nodeData,
  value,
  onChange,
  onKeyDown,
}: {
  nodeId: string;
  nodeData: WorkflowNodeData;
  value: string;
  onChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}) {
  // Different input types based on node
  switch (nodeId) {
    case 'ui-design':
      return (
        <div className="space-y-3">
          <label className="text-sm font-medium text-zinc-300">Choose a style</label>
          <div className="grid grid-cols-2 gap-2">
            {['Modern', 'Minimal', 'Playful', 'Professional'].map((style) => (
              <button
                key={style}
                onClick={() => onChange(style)}
                className={cn(
                  'p-3 rounded-lg border text-sm transition-all',
                  value === style
                    ? 'border-violet-500 bg-violet-500/10 text-violet-300'
                    : 'border-zinc-700 bg-zinc-900 text-zinc-400 hover:border-zinc-600'
                )}
              >
                {style}
              </button>
            ))}
          </div>
          <textarea
            value={value.startsWith('Modern') || value.startsWith('Minimal') || value.startsWith('Playful') || value.startsWith('Professional') ? '' : value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Or describe your own style..."
            className="w-full h-20 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none resize-none"
          />
        </div>
      );

    case 'architecture':
    case 'backend':
    case 'code-settings':
    case 'quality':
      // Advanced options with defaults
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-zinc-300">Configuration</label>
            <span className="text-xs text-amber-500">Using defaults if empty</span>
          </div>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={getPlaceholder(nodeId)}
            className="w-full h-32 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-amber-500 focus:outline-none resize-none font-mono"
          />
          {nodeData.defaultValue && (
            <div className="rounded-lg bg-zinc-900/50 border border-zinc-800 p-2">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Default</p>
              <pre className="text-xs text-zinc-400 overflow-auto">
                {JSON.stringify(nodeData.defaultValue, null, 2)}
              </pre>
            </div>
          )}
        </div>
      );

    case 'environment':
      return (
        <div className="space-y-3">
          <label className="text-sm font-medium text-zinc-300">Environment Variables</label>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="API_KEY=your_key_here&#10;ANOTHER_KEY=value"
            className="w-full h-32 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-amber-500 focus:outline-none resize-none font-mono"
          />
          <p className="text-xs text-zinc-500">
            These will be stored securely and used during code generation.
          </p>
        </div>
      );

    default:
      // Standard text input for basic nodes
      return (
        <div className="space-y-3">
          <label className="text-sm font-medium text-zinc-300">Your input</label>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={getPlaceholder(nodeId)}
            className="w-full h-40 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none resize-none"
          />
        </div>
      );
  }
}

function NodeTips({ nodeId }: { nodeId: string }) {
  const tips: Record<string, string[]> = {
    'app-idea': [
      'Be specific about the problem you\'re solving',
      'Mention what makes your app unique',
      'Example: "A habit tracker that uses AI to suggest optimal times"',
    ],
    'target-users': [
      'Who has this problem the most?',
      'Age range, profession, or lifestyle',
      'Example: "College students managing coursework and jobs"',
    ],
    'features': [
      'List 3-5 core features for MVP',
      'Prioritize what\'s essential vs nice-to-have',
      'Example: "Login, dashboard, notifications, settings"',
    ],
    'ui-design': [
      'Pick a style that matches your users',
      'Modern = clean lines, subtle shadows',
      'Playful = rounded corners, bright colors',
    ],
  };

  const nodeTips = tips[nodeId];
  if (!nodeTips) return null;

  return (
    <div className="rounded-lg bg-violet-500/5 border border-violet-500/20 p-3">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="h-3 w-3 text-violet-400" />
        <span className="text-xs font-medium text-violet-400">Tips</span>
      </div>
      <ul className="space-y-1">
        {nodeTips.map((tip, i) => (
          <li key={i} className="text-xs text-zinc-400">• {tip}</li>
        ))}
      </ul>
    </div>
  );
}

function getPlaceholder(nodeId: string): string {
  const placeholders: Record<string, string> = {
    'app-idea': 'Describe your app idea in a few sentences...\n\nWhat problem does it solve? What makes it special?',
    'target-users': 'Who will use your app?\n\nDescribe their needs, habits, and what they\'re looking for.',
    'features': 'List the main features:\n\n1. User login/signup\n2. Dashboard\n3. ...',
    'architecture': 'Leave empty to use defaults, or specify:\n\nstate: bloc\nnavigation: auto_route\ndb: hive',
    'backend': 'Leave empty for offline-first, or specify:\n\ntype: firebase\nauth: true\nfirestore: true',
    'code-settings': 'Leave empty for defaults, or customize:\n\ndefensive: true\ntests: comprehensive\ndocs: detailed',
    'quality': 'Leave empty for defaults, or specify:\n\na11y: wcag-aa\nperformance: aggressive',
  };
  return placeholders[nodeId] || 'Enter your input...';
}
