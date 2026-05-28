'use client';

import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/types';
import ThreadView from '@/components/ThreadView';
import ApprovalQueue from '@/components/ApprovalQueue';
import SourceCitations from '@/components/SourceCitations';
import type { Message, WorkflowExecution, Citation } from '@/lib/types';

export default function HomePage() {
  const [input, setInput] = useState('');
  const [threads, setThreads] = useState<WorkflowExecution[]>([
    {
      id: 'exec-1',
      name: 'Customer Onboarding Workflow',
      status: 'running',
      startedAt: new Date(Date.now() - 300000),
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Onboard new enterprise customer Acme Corp with SSO and custom branding',
          timestamp: new Date(Date.now() - 300000),
          executionId: 'exec-1',
        },
        {
          id: 'msg-2',
          role: 'assistant',
          content: 'Starting the Acme Corp onboarding workflow. I\'ll need to: 1) Create the tenant configuration, 2) Set up SSO with their IdP, 3) Configure custom branding elements.',
          timestamp: new Date(Date.now() - 240000),
          executionId: 'exec-1',
          sources: [
            {
              source: 'memory:onboarding_checklist',
              type: 'memory',
              content: 'Enterprise onboarding checklist - requires tenant config, SSO setup, branding config',
              relevance: 0.95,
              referenceId: 'doc-123',
            },
          ],
        },
        {
          id: 'msg-3',
          role: 'assistant',
          content: 'I\'m ready to proceed with the SSO configuration for Acme Corp. This requires their IdP metadata URL and certificate.',
          timestamp: new Date(Date.now() - 60000),
          executionId: 'exec-1',
          sources: [
            {
              source: 'memory:sso_requirements',
              type: 'memory',
              content: 'SSO setup requires: metadata URL, signing certificate, attribute mapping',
              relevance: 0.88,
              referenceId: 'doc-456',
            },
          ],
          requiresApproval: true,
        },
      ],
      requiresApproval: true,
    },
  ]);

  const [activeThreadId, setActiveThreadId] = useState<string>('exec-1');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [showSources, setShowSources] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeThread = threads.find((t) => t.id === activeThreadId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [threads, streamingContent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
      executionId: activeThreadId,
    };

    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId
          ? { ...t, messages: [...t.messages, userMessage] }
          : t
      )
    );
    setInput('');
    setIsStreaming(true);
    setStreamingContent('');

    // Simulate streaming response
    const responseText =
      "I'm processing your request. Let me check the database for the relevant information and coordinate with the appropriate agents to complete this task.";
    for (let i = 0; i < responseText.length; i++) {
      await new Promise((r) => setTimeout(r, 20));
      setStreamingContent(responseText.slice(0, i + 1));
    }

    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: responseText,
      timestamp: new Date(),
      executionId: activeThreadId,
      sources: [
        {
          source: 'memory:contextual_help',
          type: 'memory',
          content: 'General contextual assistance with task coordination',
          relevance: 0.72,
          referenceId: 'doc-789',
        },
        {
          source: 'web:docs.example.com/api',
          type: 'web',
          content: 'API documentation for task coordination endpoints',
          relevance: 0.65,
          referenceId: 'web-ref-1',
        },
        {
          source: 'database:tasks_table',
          type: 'database',
          content: 'Task records with status, priority, and assigned agents',
          relevance: 0.58,
          referenceId: 'db-query-1',
        },
      ],
    };

    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId
          ? { ...t, messages: [...t.messages, assistantMessage] }
          : t
      )
    );

    setIsStreaming(false);
    setStreamingContent('');
  };

  const handleApproval = (executionId: string, approved: boolean, note?: string) => {
    setThreads((prev) =>
      prev.map((t) =>
        t.id === executionId
          ? {
              ...t,
              status: approved ? 'running' : 'failed',
              messages: [
                ...t.messages,
                {
                  id: `msg-${Date.now()}`,
                  role: 'system' as const,
                  content: approved
                    ? `Approval granted${note ? `: ${note}` : ''}`
                    : `Approval denied${note ? `: ${note}` : ''}`,
                  timestamp: new Date(),
                },
              ],
              requiresApproval: false,
            }
          : t
      )
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-80 border-r bg-white flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold text-gray-800">AgentFlow</h1>
          <p className="text-sm text-gray-500">AI Orchestration Platform</p>
        </div>

        {/* Approval Queue */}
        <ApprovalQueue
          approvals={threads
            .filter((t) => t.requiresApproval)
            .map((t) => ({
              id: `approval-${t.id}`,
              executionId: t.id,
              workflowName: t.name,
              taskDescription: t.messages[t.messages.length - 1]?.content || '',
              requestedAt: t.startedAt,
              requestedBy: 'System',
              status: 'pending' as const,
            }))}
          onApprove={(id) => {
            const thread = threads.find((t) => `approval-${t.id}` === id);
            if (thread) handleApproval(thread.id, true);
          }}
          onDeny={(id, note) => {
            const thread = threads.find((t) => `approval-${t.id}` === id);
            if (thread) handleApproval(thread.id, false, note);
          }}
        />

        {/* Thread List */}
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-sm font-semibold text-gray-600 mb-3">Conversations</h2>
          <div className="space-y-2">
            {threads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => setActiveThreadId(thread.id)}
                className={cn(
                  'w-full text-left p-3 rounded-lg transition-colors',
                  activeThreadId === thread.id
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-gray-100'
                )}
              >
                <div className="font-medium text-gray-800 truncate">{thread.name}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={cn(
                      'text-xs px-2 py-0.5 rounded-full',
                      thread.status === 'running' && 'bg-yellow-100 text-yellow-700',
                      thread.status === 'completed' && 'bg-green-100 text-green-700',
                      thread.status === 'failed' && 'bg-red-100 text-red-700',
                      thread.status === 'pending_approval' && 'bg-orange-100 text-orange-700'
                    )}
                  >
                    {thread.status}
                  </span>
                  <span className="text-xs text-gray-400">
                    {thread.messages.length} messages
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 border-b bg-white px-6 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-gray-800">{activeThread?.name}</h2>
            <p className="text-sm text-gray-500">
              {activeThread?.status === 'running' ? 'Processing...' : activeThread?.status}
            </p>
          </div>
          <button
            onClick={() => setShowSources(!showSources)}
            className={cn(
              'px-4 py-2 text-sm rounded-lg transition-colors',
              showSources
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            {showSources ? 'Hide Sources' : 'Show Sources'}
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <ThreadView
            thread={activeThread!}
            streamingContent={isStreaming ? streamingContent : undefined}
          />
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t bg-white p-4">
          <div className="flex gap-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isStreaming ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>
      </main>

      {/* Sources Panel */}
      {showSources && activeThread && (
        <SourceCitations
          sources={activeThread.messages.flatMap((m) => m.sources || [])}
        />
      )}
    </div>
  );
}