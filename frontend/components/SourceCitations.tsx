'use client';

import { useState } from 'react';
import { cn } from '@/lib/types';
import type { Citation } from '@/lib/types';
import { Brain, Globe, Database, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';

interface SourceCitationsProps {
  sources: Citation[];
}

const sourceIcons = {
  memory: Brain,
  web: Globe,
  database: Database,
};

const sourceColors = {
  memory: 'bg-purple-100 text-purple-600 border-purple-200',
  web: 'bg-blue-100 text-blue-600 border-blue-200',
  database: 'bg-green-100 text-green-600 border-green-200',
};

export default function SourceCitations({ sources }: SourceCitationsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) {
    return (
      <aside className="w-80 border-l bg-white p-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">Source Citations</h3>
        <p className="text-sm text-gray-400 text-center py-4">No citations available</p>
      </aside>
    );
  }

  const groupedSources = sources.reduce<{ type: Citation['type']; items: Citation[] }[]>(
    (groups, source) => {
      const existing = groups.find((g) => g.type === source.type);
      if (existing) {
        existing.items.push(source);
      } else {
        groups.push({ type: source.type, items: [source] });
      }
      return groups;
    },
    []
  );

  return (
    <aside className="w-80 border-l bg-white flex flex-col">
      <div className="p-4 border-b">
        <h3 className="text-sm font-semibold text-gray-600">
          Source Citations ({sources.length})
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {groupedSources.map((group) => {
            const Icon = sourceIcons[group.type];
            return (
              <div key={group.type} className="space-y-2">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'p-1.5 rounded-lg',
                      sourceColors[group.type].split(' ')[0],
                      sourceColors[group.type].split(' ')[1]
                    )}
                  >
                    <Icon className="w-4 h-4" />
                  </span>
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {group.type} ({group.items.length})
                  </span>
                </div>

                <div className="space-y-2 pl-4 border-l-2 border-gray-200">
                  {group.items.map((source, idx) => {
                    const globalIdx = sources.indexOf(source);
                    const isExpanded = expandedIndex === globalIdx;

                    return (
                      <div key={idx} className="relative">
                        <button
                          onClick={() => setExpandedIndex(isExpanded ? null : globalIdx)}
                          className="w-full text-left p-2 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            <span className="text-xs font-mono text-gray-500 truncate flex-1">
                              {source.source}
                            </span>
                            {source.relevance && (
                              <span className="text-xs text-gray-400">
                                {Math.round(source.relevance * 100)}%
                              </span>
                            )}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-700">{source.content}</p>
                            {source.referenceId && (
                              <div className="mt-2 flex items-center gap-1 text-xs text-gray-400">
                                <span>ID:</span>
                                <code className="font-mono bg-gray-200 px-1.5 py-0.5 rounded">
                                  {source.referenceId}
                                </code>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t bg-gray-50">
        <p className="text-xs text-gray-500 text-center">
          Citations help verify AI responses
        </p>
      </div>
    </aside>
  );
}