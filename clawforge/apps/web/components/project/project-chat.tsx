'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User, Bot, FileCode, Sparkles, AlertCircle } from 'lucide-react';
import { ChatMessage } from '@/lib/stores/project-store';

interface ProjectChatProps {
  messages: ChatMessage[];
  isSending: boolean;
  onSendMessage: (message: string) => void;
  error: string | null;
}

const SUGGESTION_PROMPTS = [
  "Add input validation to all text fields",
  "Implement dark mode support",
  "Add loading states to all async operations",
  "Create unit tests for the main features",
  "Improve error handling with user-friendly messages",
  "Add accessibility labels to all interactive elements",
];

export function ProjectChat({ messages, isSending, onSendMessage, error }: ProjectChatProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (isSending) return;
    onSendMessage(suggestion);
  };

  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-400" />
          <h3 className="font-medium text-white">Iterative Development</h3>
        </div>
        <p className="text-xs text-zinc-500 mt-1">
          Describe changes and the AI will update your code
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <Bot className="w-12 h-12 text-zinc-700 mb-4" />
            <h4 className="text-lg font-medium text-zinc-300 mb-2">
              Continue building your app
            </h4>
            <p className="text-sm text-zinc-500 max-w-sm mb-6">
              Describe what you want to change or add, and I'll update the code for you.
              Like having a conversation with your codebase.
            </p>

            {/* Suggestion chips */}
            <div className="flex flex-wrap justify-center gap-2 max-w-md">
              {SUGGESTION_PROMPTS.slice(0, 4).map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-3 py-1.5 text-xs bg-zinc-800/50 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-full border border-zinc-700/50 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-violet-400" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-violet-600 text-white'
                    : 'bg-zinc-800/50 border border-zinc-700/50'
                }`}
              >
                <p className={`text-sm whitespace-pre-wrap ${
                  message.role === 'assistant' ? 'text-zinc-200' : ''
                }`}>
                  {message.content}
                </p>

                {/* Files changed indicator */}
                {message.filesChanged && message.filesChanged.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-zinc-700/50">
                    <div className="flex items-center gap-1.5 text-xs text-zinc-400 mb-2">
                      <FileCode className="w-3.5 h-3.5" />
                      <span>Files updated ({message.filesChanged.length})</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {message.filesChanged.map((file, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 text-xs bg-zinc-700/50 text-zinc-300 rounded font-mono"
                        >
                          {file.split('/').pop()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <span className="text-[10px] text-zinc-500 mt-2 block">
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>

              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-zinc-300" />
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading indicator */}
        {isSending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-violet-400" />
            </div>
            <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                <span className="text-sm text-zinc-400">Updating your code...</span>
              </div>
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe changes you want to make..."
            disabled={isSending}
            rows={1}
            className="w-full bg-zinc-800/50 border border-zinc-700 rounded-xl pl-4 pr-12 py-3 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isSending}
            className="absolute right-2 bottom-2 p-2 text-zinc-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        <p className="text-[10px] text-zinc-600 mt-2 text-center">
          Press Enter to send, Shift + Enter for new line
        </p>
      </div>
    </div>
  );
}
