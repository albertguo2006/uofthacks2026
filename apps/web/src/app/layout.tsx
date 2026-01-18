import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import dynamic from 'next/dynamic';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

// Dynamically import GrainOverlay to avoid SSR issues
const GrainOverlay = dynamic(() => import('@/components/ui/GrainOverlay'), { ssr: false });

export const metadata: Metadata = {
  title: 'SimplyAuthentic',
  description: 'Identity-first freelance marketplace. Prove your skills through behavior, not resumes.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <main className="min-h-screen">
          {children}
        </main>
        <GrainOverlay />
      </body>
    </html>
  );
}
