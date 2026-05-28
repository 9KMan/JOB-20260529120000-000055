'use client';

import { cn } from '@/lib/types';
import type { WorkflowExecution, Message } from '@/lib/types';
import { formatDistanceToNow } from '@/lib/utils';

interface ThreadViewProps {
  thread: WorkflowExecution;
  streamingContent?: string;
}

function MessageBubble({ message, isStreaming = false }: { message: Message; isStreaming?: boolean }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="bg-gray-100 text-gray-600 text-sm px-4 py-2 rounded-full">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'max-w-[70%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-primary-600 text-white rounded-tr-md'
            : 'bg-white border border-gray-200 rounded-tl-md',
          isStreaming && 'animate-pulse'
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <div
          className={cn(
            'text-xs mt-1',
            isUser ? 'text-primary-200' : 'text-gray-400'
          )}
        >
          {formatDistanceToNow(message.timestamp)}
        </div>
      </div>
    </div>
  );
}

export default function ThreadView({ thread, streamingContent }: ThreadViewProps) {
  const groupedMessages = thread.messages.reduce<{ executionId: string; messages: Message[] }[]>(
    (groups, message) => {
      const execId = message.executionId || 'unknown';
      const existing = groups.find((g) => g.executionId === execId);
      if (existing) {
        existing.messages.push(message);
      } else {
        groups.push({ executionId: execId, messages: [message] });
      }
      return groups;
    },
    []
  );

  return (
    <div className="p-6 space-y-8">
      {groupedMessages.map((group, idx) => (
        <div key={group.executionId} className="space-y-4">
          {/* Execution Header */}
          <div className="flex items-center gap-2">
            <div className="h-px flex-1 bg-gray-200" />
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              {idx === 0 ? 'Current Workflow' : `Execution ${group.executionId.slice(-6)}`}
            </span>
            <div className="h-px flex-1 bg-gray-200" />
          </div>

          {/* Messages */}
          <div className="space-y-4">
            {group.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>

          {/* Streaming Indicator */}
          {streamingContent && group.executionId === thread.id && (
            <MessageBubble
              message={{
                id: 'streaming',
                role: 'assistant',
                content: streamingContent,
                timestamp: new Date(),
              }}
              isStreaming
            />
          )}
        </div>
      ))}

      {thread.messages.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No messages yet. Start the conversation!</p>
        </div>
      )}
    </div>
  );
}