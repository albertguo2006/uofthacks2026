'use client';

import Link from 'next/link';

export default function RecruiterDashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Recruiter Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-300 mt-2">
          Find candidates with verified skills backed by behavioral evidence
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Link
          href="/recruiter/candidates"
          className="p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
        >
          <h3 className="text-lg font-semibold">Browse Candidates</h3>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            View skill passports and find the right fit for your roles
          </p>
        </Link>

        <Link
          href="/recruiter/candidates?archetype=careful_tester"
          className="p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
        >
          <h3 className="text-lg font-semibold">By Archetype</h3>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Filter candidates by behavioral archetype (Fast Iterators, Careful Testers, etc.)
          </p>
        </Link>

        <Link
          href="/recruiter/security"
          className="p-6 bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md transition-shadow"
        >
          <h3 className="text-lg font-semibold">Security & Privacy</h3>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            View our data collection practices and security posture
          </p>
        </Link>
      </div>
    </div>
  );
}
