'use client';

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';
import { cn } from '@/lib/utils';
import {
  Lightbulb,
  Users,
  ListChecks,
  Palette,
  Cog,
  Server,
  Key,
  Code,
  Sparkles,
  Rocket,
  type LucideIcon,
} from 'lucide-react';

export type WorkflowNodeData = {
  label: string;
  description: string;
  icon: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  stepNumber: number;
  section: 'basic' | 'advanced';
  agent: string;
  defaultValue?: Record<string, unknown>;
};

const iconMap: Record<string, LucideIcon> = {
  lightbulb: Lightbulb,
  users: Users,
  'list-checks': ListChecks,
  palette: Palette,
  cog: Cog,
  server: Server,
  key: Key,
  code: Code,
  sparkles: Sparkles,
  rocket: Rocket,
};

const statusColors: Record<WorkflowNodeData['status'], string> = {
  idle: 'border-zinc-700 bg-zinc-900',
  running: 'border-blue-500 bg-blue-500/10 animate-pulse',
  completed: 'border-green-500 bg-green-500/10',
  error: 'border-red-500 bg-red-500/10',
};

const sectionStyles: Record<WorkflowNodeData['section'], string> = {
  basic: 'border-l-4 border-l-violet-500',
  advanced: 'border-l-4 border-l-amber-500 opacity-75 hover:opacity-100',
};

type WorkflowNodeProps = NodeProps & {
  data: WorkflowNodeData;
};

export const WorkflowNode = memo(({ data, selected }: WorkflowNodeProps) => {
  const Icon = iconMap[data.icon] || Lightbulb;
  const isAdvanced = data.section === 'advanced';

  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-zinc-500 !w-3 !h-3 !border-2 !border-zinc-900"
      />
      <div
        className={cn(
          'min-w-[220px] max-w-[280px] rounded-lg border-2 p-4 shadow-lg transition-all cursor-pointer',
          statusColors[data.status],
          sectionStyles[data.section],
          selected && 'ring-2 ring-violet-500 ring-offset-2 ring-offset-zinc-950'
        )}
      >
        <div className="flex items-start gap-3">
          <div className={cn(
            'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
            isAdvanced ? 'bg-amber-500/20' : 'bg-violet-500/20'
          )}>
            <Icon className={cn(
              'h-5 w-5',
              isAdvanced ? 'text-amber-400' : 'text-violet-400'
            )} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              {data.stepNumber > 0 && (
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-violet-500/30 text-xs font-medium text-violet-300">
                  {data.stepNumber}
                </span>
              )}
              {isAdvanced && (
                <span className="text-[10px] uppercase tracking-wider text-amber-500 font-medium">
                  Advanced
                </span>
              )}
              <h3 className="font-medium text-zinc-100 truncate">{data.label}</h3>
            </div>
            <p className="mt-1 text-xs text-zinc-400 line-clamp-2">{data.description}</p>
          </div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-zinc-500 !w-3 !h-3 !border-2 !border-zinc-900"
      />
    </>
  );
});

WorkflowNode.displayName = 'WorkflowNode';
