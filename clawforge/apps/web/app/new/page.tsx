import { WorkflowCanvas } from '@/components/canvas/workflow-canvas';
import { WorkflowHeader } from '@/components/header/workflow-header';

export default function NewProjectPage() {
  return (
    <div className="h-screen w-screen flex flex-col bg-zinc-950">
      {/* Header */}
      <WorkflowHeader />

      {/* Canvas - takes remaining space */}
      <div className="flex-1 min-h-0">
        <WorkflowCanvas />
      </div>
    </div>
  );
}
