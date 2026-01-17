'use client';

import { useParams, useRouter } from 'next/navigation';
import { TimelineReplay } from '@/components/replay';

export default function SessionReplayPage() {
  const params = useParams();
  const router = useRouter();

  const candidateId = params.id as string;
  const sessionId = params.sessionId as string;

  const handleBack = () => {
    router.push(`/recruiter/candidates/${candidateId}`);
  };

  return (
    <TimelineReplay
      sessionId={sessionId}
      onBack={handleBack}
    />
  );
}
