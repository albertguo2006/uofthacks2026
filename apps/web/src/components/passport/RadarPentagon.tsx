'use client';

import { useMemo } from 'react';
import { RadarProfile } from '@/hooks/useRadar';

interface RadarPentagonProps {
  profile: RadarProfile | null;
  size?: number;
  showLabels?: boolean;
  className?: string;
}

interface RadarPoint {
  label: string;
  shortLabel: string;
  key: keyof RadarProfile;
  value: number;
}

const RADAR_DIMENSIONS: { label: string; shortLabel: string; key: keyof RadarProfile }[] = [
  { label: 'Verification', shortLabel: 'Verification', key: 'verification' },
  { label: 'Velocity', shortLabel: 'Velocity', key: 'velocity' },
  { label: 'Optimization', shortLabel: 'Optimization', key: 'optimization' },
  { label: 'Decomposition', shortLabel: 'Decomposition', key: 'decomposition' },
  { label: 'Debugging', shortLabel: 'Debugging', key: 'debugging' },
];

const DEFAULT_PROFILE: RadarProfile = {
  verification: { score: 0.5, confidence: 0.3 },
  velocity: { score: 0.5, confidence: 0.3 },
  optimization: { score: 0.5, confidence: 0.3 },
  decomposition: { score: 0.5, confidence: 0.3 },
  debugging: { score: 0.5, confidence: 0.3 },
};

export function RadarPentagon({
  profile,
  size = 250,
  showLabels = true,
  className = '',
}: RadarPentagonProps) {
  const activeProfile = profile || DEFAULT_PROFILE;
  const centerX = size / 2;
  const centerY = size / 2;
  const maxRadius = (size / 2) - (showLabels ? 50 : 15);
  const numSides = RADAR_DIMENSIONS.length;
  const angleStep = (2 * Math.PI) / numSides;

  const points: RadarPoint[] = useMemo(() => {
    return RADAR_DIMENSIONS.map((dim) => {
      const dimension = activeProfile[dim.key];
      return {
        ...dim,
        value: dimension?.score ?? 0.5,
      };
    });
  }, [activeProfile]);

  // Calculate polygon points for a given set of values
  const getPolygonPoints = (values: number[]): string => {
    return values
      .map((value, i) => {
        const angle = (i * angleStep) - (Math.PI / 2); // Start from top
        const radius = value * maxRadius;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        return `${x},${y}`;
      })
      .join(' ');
  };

  // Background grid levels
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];

  // Background grid lines (from center to each vertex)
  const gridLines = useMemo(() => {
    return Array.from({ length: numSides }, (_, i) => {
      const angle = (i * angleStep) - (Math.PI / 2);
      const x = centerX + maxRadius * Math.cos(angle);
      const y = centerY + maxRadius * Math.sin(angle);
      return { x, y };
    });
  }, [centerX, centerY, maxRadius, angleStep, numSides]);

  // Score polygon
  const scorePolygon = getPolygonPoints(points.map((p) => p.value));

  // Label positions
  const labelPositions = useMemo(() => {
    return points.map((point, i) => {
      const angle = (i * angleStep) - (Math.PI / 2);
      const labelRadius = maxRadius + 35;
      const x = centerX + labelRadius * Math.cos(angle);
      const y = centerY + labelRadius * Math.sin(angle);
      return { x, y, point };
    });
  }, [points, centerX, centerY, maxRadius, angleStep]);

  return (
    <div className={`relative ${className}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background gradient */}
        <defs>
          <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.3" />
          </linearGradient>
          <linearGradient id="radarStrokeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>

        {/* Background grid */}
        <g className="fill-none">
          {/* Concentric pentagons */}
          {gridLevels.map((ratio) => (
            <polygon
              key={ratio}
              points={getPolygonPoints(Array(numSides).fill(ratio))}
              strokeWidth="1"
              className="stroke-gray-300 dark:stroke-gray-600"
              fill="none"
            />
          ))}

          {/* Radial lines */}
          {gridLines.map((line, i) => (
            <line
              key={i}
              x1={centerX}
              y1={centerY}
              x2={line.x}
              y2={line.y}
              strokeWidth="1"
              className="stroke-gray-300 dark:stroke-gray-600"
            />
          ))}
        </g>

        {/* Score polygon with gradient fill */}
        <polygon
          points={scorePolygon}
          fill="url(#radarGradient)"
          stroke="url(#radarStrokeGradient)"
          strokeWidth="2.5"
        />

        {/* Data points */}
        {points.map((point, i) => {
          const angle = (i * angleStep) - (Math.PI / 2);
          const radius = point.value * maxRadius;
          const x = centerX + radius * Math.cos(angle);
          const y = centerY + radius * Math.sin(angle);

          return (
            <g key={point.key}>
              {/* Outer glow */}
              <circle
                cx={x}
                cy={y}
                r="8"
                className="fill-primary-500/20"
              />
              {/* Inner point */}
              <circle
                cx={x}
                cy={y}
                r="5"
                className="fill-white dark:fill-slate-800"
                stroke="url(#radarStrokeGradient)"
                strokeWidth="2"
              />
            </g>
          );
        })}

        {/* Center point */}
        <circle
          cx={centerX}
          cy={centerY}
          r="3"
          className="fill-gray-400 dark:fill-gray-500"
        />
      </svg>

      {/* Labels */}
      {showLabels && (
        <div className="absolute inset-0 pointer-events-none">
          {labelPositions.map(({ x, y, point }) => {
            // Adjust text positioning based on angle
            const relX = x - centerX;
            const relY = y - centerY;

            let translateX = '-50%';
            let translateY = '-50%';

            // Top label
            if (relY < -maxRadius * 0.5) {
              translateY = '-100%';
            }
            // Bottom labels
            else if (relY > maxRadius * 0.5) {
              translateY = '0%';
            }

            // Left labels
            if (relX < -maxRadius * 0.3) {
              translateX = '-100%';
            }
            // Right labels
            else if (relX > maxRadius * 0.3) {
              translateX = '0%';
            }

            return (
              <div
                key={point.key}
                className="absolute text-center"
                style={{
                  left: x,
                  top: y,
                  transform: `translate(${translateX}, ${translateY})`,
                }}
              >
                <span className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                  {point.shortLabel}
                </span>
                <span className="block text-sm font-bold text-primary-600 dark:text-primary-400">
                  {Math.round(point.value * 100)}%
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/**
 * Compact version of radar pentagon for small spaces
 */
export function RadarPentagonMini({
  profile,
  size = 100,
  className = '',
}: {
  profile: RadarProfile | null;
  size?: number;
  className?: string;
}) {
  return (
    <RadarPentagon
      profile={profile}
      size={size}
      showLabels={false}
      className={className}
    />
  );
}
