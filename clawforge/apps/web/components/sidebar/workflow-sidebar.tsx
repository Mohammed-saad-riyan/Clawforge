'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  Cog,
  Server,
  Key,
  Code,
  Sparkles,
  ChevronRight,
  GripVertical,
  Info,
  type LucideIcon,
} from 'lucide-react';

export type DraggableNodeType = {
  id: string;
  label: string;
  description: string;
  icon: string;
  defaultValue?: Record<string, unknown>;
};

const advancedComponents: DraggableNodeType[] = [
  {
    id: 'architecture',
    label: 'Architecture',
    description: 'State management, routing, database choices',
    icon: 'cog',
    defaultValue: { state: 'riverpod', nav: 'go_router', db: 'drift' },
  },
  {
    id: 'backend',
    label: 'Backend & APIs',
    description: 'Firebase, Supabase, REST, or offline-first',
    icon: 'server',
    defaultValue: { type: 'offline-first' },
  },
  {
    id: 'environment',
    label: 'Environment',
    description: 'API keys and secrets',
    icon: 'key',
  },
  {
    id: 'code-settings',
    label: 'Code Settings',
    description: 'Tests, docs, defensive prompts',
    icon: 'code',
    defaultValue: { defensive: true, tests: 'basic', docs: 'inline' },
  },
  {
    id: 'quality',
    label: 'Quality & Polish',
    description: 'Accessibility, performance tuning',
    icon: 'sparkles',
    defaultValue: { a11y: 'standard', performance: 'balanced' },
  },
];

const iconMap: Record<string, LucideIcon> = {
  cog: Cog,
  server: Server,
  key: Key,
  code: Code,
  sparkles: Sparkles,
};

interface WorkflowSidebarProps {
  onDragStart: (event: React.DragEvent, nodeType: DraggableNodeType) => void;
  addedNodes: string[];
}

export function WorkflowSidebar({ onDragStart, addedNodes }: WorkflowSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const availableComponents = advancedComponents.filter(
    (comp) => !addedNodes.includes(comp.id)
  );

  return (
    <div
      className={cn(
        'h-full border-r border-zinc-800 bg-zinc-950 transition-all duration-300',
        isCollapsed ? 'w-12' : 'w-72'
      )}
    >
      {/* Header */}
      <div className="flex h-12 items-center justify-between border-b border-zinc-800 px-3">
        {!isCollapsed && (
          <span className="text-sm font-medium text-zinc-300">Components</span>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-zinc-800"
        >
          <ChevronRight
            className={cn(
              'h-4 w-4 text-zinc-400 transition-transform',
              !isCollapsed && 'rotate-180'
            )}
          />
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-3 space-y-4">
          {/* Info box */}
          <div className="rounded-lg bg-violet-500/10 border border-violet-500/30 p-3">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-violet-400 mt-0.5 shrink-0" />
              <p className="text-xs text-violet-300">
                Drag advanced components to the canvas to customize your workflow.
                Basic flow is already set up!
              </p>
            </div>
          </div>

          {/* Advanced Components */}
          <div>
            <h3 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
              Advanced Options
            </h3>
            <div className="space-y-2">
              {availableComponents.length === 0 ? (
                <p className="text-xs text-zinc-500 italic">
                  All components added to canvas
                </p>
              ) : (
                availableComponents.map((component) => (
                  <DraggableComponent
                    key={component.id}
                    component={component}
                    onDragStart={onDragStart}
                  />
                ))
              )}
            </div>
          </div>

          {/* Added components indicator */}
          {addedNodes.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
                On Canvas ({addedNodes.length})
              </h3>
              <div className="flex flex-wrap gap-1">
                {addedNodes.map((id) => {
                  const comp = advancedComponents.find((c) => c.id === id);
                  return comp ? (
                    <span
                      key={id}
                      className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded"
                    >
                      {comp.label}
                    </span>
                  ) : null;
                })}
              </div>
            </div>
          )}

          {/* Defaults info */}
          <div className="border-t border-zinc-800 pt-3">
            <h3 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
              Smart Defaults
            </h3>
            <ul className="text-[11px] text-zinc-500 space-y-1">
              <li>• State: Riverpod 3.0</li>
              <li>• Navigation: go_router</li>
              <li>• Database: Drift (SQLite)</li>
              <li>• Backend: Offline-first</li>
              <li>• Tests: Basic coverage</li>
            </ul>
            <p className="text-[10px] text-zinc-600 mt-2 italic">
              These are used if you don't add advanced components
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function DraggableComponent({
  component,
  onDragStart,
}: {
  component: DraggableNodeType;
  onDragStart: (event: React.DragEvent, nodeType: DraggableNodeType) => void;
}) {
  const Icon = iconMap[component.icon] || Cog;

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, component)}
      className={cn(
        'group flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900 p-3',
        'cursor-grab active:cursor-grabbing',
        'hover:border-amber-500/50 hover:bg-amber-500/5',
        'transition-all duration-200'
      )}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-amber-500/20">
        <Icon className="h-4 w-4 text-amber-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-zinc-200">{component.label}</p>
        <p className="text-[11px] text-zinc-500 truncate">{component.description}</p>
      </div>
      <GripVertical className="h-4 w-4 text-zinc-600 group-hover:text-zinc-400" />
    </div>
  );
}
