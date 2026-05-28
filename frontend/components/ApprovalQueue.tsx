'use client';

import { useState } from 'react';
import { cn } from '@/lib/types';
import type { ApprovalRequest } from '@/lib/types';
import { formatDistanceToNow } from '@/lib/utils';
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

interface ApprovalQueueProps {
  approvals: ApprovalRequest[];
  onApprove: (id: string) => void;
  onDeny: (id: string, note?: string) => void;
}

export default function ApprovalQueue({ approvals, onApprove, onDeny }: ApprovalQueueProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [note, setNote] = useState('');

  const handleApprove = (id: string) => {
    onApprove(id);
    setNote('');
    setExpandedId(null);
  };

  const handleDeny = (id: string) => {
    onDeny(id, note || undefined);
    setNote('');
    setExpandedId(null);
  };

  if (approvals.length === 0) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <AlertCircle className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-600">Pending Approvals</h3>
        </div>
        <p className="text-sm text-gray-400 text-center py-4">No pending approvals</p>
      </div>
    );
  }

  return (
    <div className="p-4 border-t">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="w-4 h-4 text-orange-500" />
        <h3 className="text-sm font-semibold text-gray-600">
          Pending Approvals ({approvals.length})
        </h3>
      </div>

      <div className="space-y-3">
        {approvals.map((approval) => (
          <div
            key={approval.id}
            className="bg-orange-50 border border-orange-200 rounded-lg p-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-800 text-sm truncate">
                  {approval.workflowName}
                </p>
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                  {approval.taskDescription}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {formatDistanceToNow(approval.requestedAt)}
                </p>
              </div>
            </div>

            {expandedId === approval.id ? (
              <div className="mt-3 space-y-2">
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Add a note (optional)..."
                  className="w-full px-3 py-2 text-sm border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-orange-300"
                  rows={2}
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleApprove(approval.id)}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve
                  </button>
                  <button
                    onClick={() => handleDeny(approval.id)}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                    Deny
                  </button>
                </div>
                <button
                  onClick={() => setExpandedId(null)}
                  className="w-full text-xs text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => handleApprove(approval.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </button>
                <button
                  onClick={() => setExpandedId(approval.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
                >
                  <XCircle className="w-4 h-4" />
                  Deny
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}