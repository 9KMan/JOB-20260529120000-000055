import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AgentFlow - AI Orchestration Platform',
  description: 'Multi-agent orchestration with human-in-the-loop approvals',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}