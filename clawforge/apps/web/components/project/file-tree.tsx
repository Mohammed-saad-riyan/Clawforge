'use client';

import { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, AlertTriangle } from 'lucide-react';
import { ProjectFile } from '@/lib/stores/project-store';

interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: FileTreeNode[];
  file?: ProjectFile;
  isMissing?: boolean;
}

// Internal type for building the tree (uses object for efficient lookup)
interface BuildNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: Record<string, BuildNode>;
  file?: ProjectFile;
  isMissing?: boolean;
}

interface FileTreeProps {
  files: ProjectFile[];
  selectedFile: ProjectFile | null;
  onSelectFile: (file: ProjectFile) => void;
  missingFiles?: string[];
}

function buildFileTree(files: ProjectFile[], missingFiles: string[] = []): FileTreeNode[] {
  const root: Record<string, BuildNode> = {};

  // Add actual files
  files.forEach((file) => {
    const parts = file.path.split('/').filter(Boolean);
    let current = root;

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      const currentPath = parts.slice(0, index + 1).join('/');

      if (!current[part]) {
        current[part] = {
          name: part,
          path: currentPath,
          type: isFile ? 'file' : 'folder',
          children: isFile ? undefined : {},
          file: isFile ? file : undefined,
        };
      }

      if (!isFile && current[part].children) {
        current = current[part].children!;
      }
    });
  });

  // Add missing files (marked differently)
  missingFiles.forEach((filePath) => {
    const parts = filePath.split('/').filter(Boolean);
    let current = root;

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      const currentPath = parts.slice(0, index + 1).join('/');

      if (!current[part]) {
        current[part] = {
          name: part,
          path: currentPath,
          type: isFile ? 'file' : 'folder',
          children: isFile ? undefined : {},
          isMissing: isFile,
        };
      }

      if (!isFile && current[part].children) {
        current = current[part].children!;
      }
    });
  });

  // Convert to array and sort
  function toArray(obj: Record<string, BuildNode>): FileTreeNode[] {
    return Object.values(obj)
      .map((node): FileTreeNode => ({
        name: node.name,
        path: node.path,
        type: node.type,
        file: node.file,
        isMissing: node.isMissing,
        children: node.children ? toArray(node.children) : undefined,
      }))
      .sort((a, b) => {
        // Folders first, then files
        if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
  }

  return toArray(root);
}

function TreeNode({
  node,
  depth,
  selectedFile,
  onSelectFile,
  expandedFolders,
  toggleFolder,
}: {
  node: FileTreeNode;
  depth: number;
  selectedFile: ProjectFile | null;
  onSelectFile: (file: ProjectFile) => void;
  expandedFolders: Set<string>;
  toggleFolder: (path: string) => void;
}) {
  const isExpanded = expandedFolders.has(node.path);
  const isSelected = selectedFile?.path === node.path;

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const colors: Record<string, string> = {
      dart: 'text-blue-400',
      yaml: 'text-yellow-400',
      json: 'text-orange-400',
      md: 'text-zinc-400',
      xml: 'text-green-400',
      gradle: 'text-emerald-400',
      kt: 'text-purple-400',
      swift: 'text-orange-500',
      ts: 'text-blue-500',
      tsx: 'text-blue-500',
    };
    return colors[ext || ''] || 'text-zinc-400';
  };

  if (node.type === 'folder') {
    return (
      <div>
        <button
          onClick={() => toggleFolder(node.path)}
          className="w-full flex items-center gap-1.5 px-2 py-1 hover:bg-zinc-800/50 rounded text-left group"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-zinc-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-zinc-500" />
          )}
          {isExpanded ? (
            <FolderOpen className="w-4 h-4 text-amber-400" />
          ) : (
            <Folder className="w-4 h-4 text-amber-400" />
          )}
          <span className="text-sm text-zinc-300 truncate">{node.name}</span>
        </button>
        {isExpanded && node.children && (
          <div>
            {node.children.map((child) => (
              <TreeNode
                key={child.path}
                node={child}
                depth={depth + 1}
                selectedFile={selectedFile}
                onSelectFile={onSelectFile}
                expandedFolders={expandedFolders}
                toggleFolder={toggleFolder}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File node
  return (
    <button
      onClick={() => node.file && onSelectFile(node.file)}
      disabled={node.isMissing}
      className={`w-full flex items-center gap-1.5 px-2 py-1 rounded text-left group ${
        isSelected
          ? 'bg-violet-500/20 text-violet-300'
          : node.isMissing
          ? 'text-red-400/70 cursor-not-allowed'
          : 'hover:bg-zinc-800/50 text-zinc-400'
      }`}
      style={{ paddingLeft: `${depth * 12 + 28}px` }}
    >
      {node.isMissing ? (
        <AlertTriangle className="w-4 h-4 text-red-400" />
      ) : (
        <File className={`w-4 h-4 ${getFileIcon(node.name)}`} />
      )}
      <span className={`text-sm truncate ${isSelected ? 'text-violet-200' : ''}`}>
        {node.name}
      </span>
      {node.isMissing && (
        <span className="text-xs text-red-400/60 ml-auto">missing</span>
      )}
    </button>
  );
}

export function FileTree({ files, selectedFile, onSelectFile, missingFiles = [] }: FileTreeProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => {
    // Auto-expand lib folder and first level
    const initial = new Set<string>();
    files.forEach((file) => {
      const parts = file.path.split('/');
      if (parts.length > 1) {
        initial.add(parts[0]);
        if (parts[0] === 'lib' && parts.length > 2) {
          initial.add(parts.slice(0, 2).join('/'));
        }
      }
    });
    return initial;
  });

  const tree = useMemo(() => buildFileTree(files, missingFiles), [files, missingFiles]);

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const expandAll = () => {
    const allFolders = new Set<string>();
    const addFolders = (nodes: FileTreeNode[]) => {
      nodes.forEach((node) => {
        if (node.type === 'folder') {
          allFolders.add(node.path);
          if (node.children) addFolders(node.children);
        }
      });
    };
    addFolders(tree);
    setExpandedFolders(allFolders);
  };

  const collapseAll = () => {
    setExpandedFolders(new Set());
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Files ({files.length})
        </span>
        <div className="flex gap-1">
          <button
            onClick={expandAll}
            className="text-xs text-zinc-500 hover:text-zinc-300 px-1.5 py-0.5"
          >
            Expand
          </button>
          <button
            onClick={collapseAll}
            className="text-xs text-zinc-500 hover:text-zinc-300 px-1.5 py-0.5"
          >
            Collapse
          </button>
        </div>
      </div>

      {missingFiles.length > 0 && (
        <div className="px-3 py-2 bg-red-500/10 border-b border-red-500/20">
          <div className="flex items-center gap-2 text-xs text-red-400">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>{missingFiles.length} missing file(s)</span>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-auto py-2">
        {tree.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            depth={0}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
            expandedFolders={expandedFolders}
            toggleFolder={toggleFolder}
          />
        ))}
      </div>
    </div>
  );
}
