import Link from 'next/link';
import NodeGraphBackground from '@/components/ui/NodeGraphBackground';

export default function Home() {
  return (
    <>
      {/* Ombre gradient background - dark at top, lighter at bottom */}
      <div 
        className="fixed inset-0"
        style={{ 
          zIndex: -1,
          background: 'linear-gradient(to bottom, rgb(15, 23, 42) 0%, rgb(30, 41, 59) 40%, rgb(51, 65, 85) 70%, rgb(71, 85, 105) 100%)'
        }}
      />
      <NodeGraphBackground
        nodeCount={100}
        connectionDistance={150}
        cursorInfluenceRadius={150}
        cursorRepelStrength={0.25}
        cursorTrailDelay={0.05}
      />
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-6">
            Simply Authentic
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Your professional identity shouldn&apos;t be self-reported.
            It should be <strong>behavioral proof</strong>: how you work,
            how you debug, how you communicate, and how you improve over time.
          </p>

          <div className="flex gap-4 justify-center mb-12">
            <Link
              href="/auth/login"
              className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/auth/register"
              className="px-6 py-3 border border-primary-600 text-primary-600 rounded-lg hover:bg-primary-50 transition-colors"
            >
              Get Started
            </Link>
          </div>

          <div className="grid md:grid-cols-3 gap-8 text-left">
            <div className="p-6 rounded-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-sm">
              <h3 className="text-lg font-semibold mb-2">For Candidates</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Complete real tasks in our sandbox. Build a Skill Passport backed
                by behavioral evidence. Unlock premium jobs as your identity evolves.
              </p>
            </div>

            <div className="p-6 rounded-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-sm">
              <h3 className="text-lg font-semibold mb-2">For Recruiters</h3>
              <p className="text-gray-600 dark:text-gray-300">
                See how candidates actually work, not just what they claim.
                Review behavioral signatures and interview highlights.
              </p>
            </div>

            <div className="p-6 rounded-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-sm">
              <h3 className="text-lg font-semibold mb-2">Trustable Signal</h3>
              <p className="text-gray-600 dark:text-gray-300">
                AI-powered identity verification. Anti-cheat detection.
                Transparent security with 1Password integration.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
