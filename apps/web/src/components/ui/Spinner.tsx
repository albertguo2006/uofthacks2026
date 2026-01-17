'use client';

import { cn } from '@/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizes = {
    sm: { container: 'h-4 w-4', dot: 'h-1 w-1' },
    md: { container: 'h-8 w-8', dot: 'h-1.5 w-1.5' },
    lg: { container: 'h-12 w-12', dot: 'h-2 w-2' },
  };

  return (
    <div
      className={cn(
        'relative animate-spin',
        sizes[size].container,
        className
      )}
    >
      {/* Create 8 glowing dots around the circle */}
      {[...Array(8)].map((_, i) => (
        <div
          key={i}
          className="absolute"
          style={{
            top: '50%',
            left: '50%',
            transform: `rotate(${i * 45}deg) translateY(-150%)`,
          }}
        >
          <div
            className={cn(
              'rounded-full bg-white',
              sizes[size].dot
            )}
            style={{
              opacity: 1 - (i * 0.1),
              boxShadow: '0 0 6px 2px rgba(255, 255, 255, 0.8), 0 0 12px 4px rgba(255, 255, 255, 0.4)',
            }}
          />
        </div>
      ))}
    </div>
  );
}
