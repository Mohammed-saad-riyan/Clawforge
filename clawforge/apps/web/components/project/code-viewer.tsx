'use client';

import { useMemo } from 'react';
import { Copy, Check, FileCode } from 'lucide-react';
import { useState } from 'react';
import { ProjectFile } from '@/lib/stores/project-store';

interface CodeViewerProps {
  file: ProjectFile | null;
}

// Simple syntax highlighting for Dart
function highlightDart(code: string): string {
  // Keywords
  const keywords = [
    'abstract', 'as', 'assert', 'async', 'await', 'break', 'case', 'catch',
    'class', 'const', 'continue', 'covariant', 'default', 'deferred', 'do',
    'dynamic', 'else', 'enum', 'export', 'extends', 'extension', 'external',
    'factory', 'false', 'final', 'finally', 'for', 'Function', 'get', 'hide',
    'if', 'implements', 'import', 'in', 'interface', 'is', 'late', 'library',
    'mixin', 'new', 'null', 'on', 'operator', 'part', 'required', 'rethrow',
    'return', 'set', 'show', 'static', 'super', 'switch', 'sync', 'this',
    'throw', 'true', 'try', 'typedef', 'var', 'void', 'while', 'with', 'yield',
  ];

  const types = [
    'String', 'int', 'double', 'bool', 'List', 'Map', 'Set', 'Future', 'Stream',
    'Widget', 'BuildContext', 'State', 'StatelessWidget', 'StatefulWidget',
    'Container', 'Text', 'Column', 'Row', 'Scaffold', 'AppBar', 'Icon',
    'IconButton', 'ElevatedButton', 'TextButton', 'Card', 'Padding', 'Center',
    'SizedBox', 'Expanded', 'Flexible', 'ListView', 'GridView', 'Navigator',
  ];

  let result = code
    // Escape HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Comments
    .replace(/(\/\/.*$)/gm, '<span class="text-zinc-500">$1</span>')
    .replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="text-zinc-500">$1</span>')
    // Strings
    .replace(/('(?:[^'\\]|\\.)*')/g, '<span class="text-amber-400">$1</span>')
    .replace(/("(?:[^"\\]|\\.)*")/g, '<span class="text-amber-400">$1</span>')
    // Numbers
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="text-orange-400">$1</span>')
    // Annotations
    .replace(/(@\w+)/g, '<span class="text-purple-400">$1</span>');

  // Keywords
  keywords.forEach((kw) => {
    const regex = new RegExp(`\\b(${kw})\\b`, 'g');
    result = result.replace(regex, '<span class="text-pink-400">$1</span>');
  });

  // Types
  types.forEach((type) => {
    const regex = new RegExp(`\\b(${type})\\b`, 'g');
    result = result.replace(regex, '<span class="text-cyan-400">$1</span>');
  });

  return result;
}

function getLanguageFromPath(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase();
  const langMap: Record<string, string> = {
    dart: 'dart',
    yaml: 'yaml',
    yml: 'yaml',
    json: 'json',
    md: 'markdown',
    xml: 'xml',
    gradle: 'groovy',
    kt: 'kotlin',
    swift: 'swift',
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
  };
  return langMap[ext || ''] || 'text';
}

export function CodeViewer({ file }: CodeViewerProps) {
  const [copied, setCopied] = useState(false);

  const highlightedCode = useMemo(() => {
    if (!file) return '';
    const lang = getLanguageFromPath(file.path);
    if (lang === 'dart') {
      return highlightDart(file.content);
    }
    // For other languages, just escape HTML
    return file.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }, [file]);

  const copyToClipboard = async () => {
    if (!file) return;
    await navigator.clipboard.writeText(file.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!file) {
    return (
      <div className="h-full flex items-center justify-center bg-zinc-900/50">
        <div className="text-center text-zinc-500">
          <FileCode className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Select a file to view its contents</p>
        </div>
      </div>
    );
  }

  const lines = file.content.split('\n');
  const lineNumberWidth = String(lines.length).length;

  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-zinc-500" />
          <span className="text-sm text-zinc-300 font-mono">{file.path}</span>
        </div>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 px-2 py-1 text-xs text-zinc-400 hover:text-white hover:bg-zinc-800 rounded transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-400" />
              <span className="text-green-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code */}
      <div className="flex-1 overflow-auto">
        <pre className="p-4 text-sm font-mono leading-relaxed">
          <code>
            {lines.map((line, i) => (
              <div key={i} className="flex hover:bg-zinc-800/30">
                <span
                  className="select-none text-zinc-600 pr-4 text-right"
                  style={{ minWidth: `${lineNumberWidth + 2}ch` }}
                >
                  {i + 1}
                </span>
                <span
                  className="text-zinc-300 flex-1"
                  dangerouslySetInnerHTML={{
                    __html: highlightDart(line) || '&nbsp;',
                  }}
                />
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
}
