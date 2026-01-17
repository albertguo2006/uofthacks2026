'use client';

import { useMemo } from 'react';
import { RadarProfile } from '@/hooks/useRadar';

interface RadarChartProps {
  profile: RadarProfile | null;
  size?: number;
  showLabels?: boolean;
  showConfidence?: boolean;
  className?: string;
}

interface RadarPoint {
  label: string;
  shortLabel: string;
  key: keyof RadarProfile;
  score: number;
  confidence: number;
}

const RADAR_DIMENSIONS: { label: string; shortLabel: string; key: keyof RadarProfile }[] = [
  { label: 'Verification', shortLabel: 'Ver', key: 'verification' },
  { label: 'Velocity', shortLabel: 'Vel', key: 'velocity' },
  { label: 'Optimization', shortLabel: 'Opt', key: 'optimization' },
  { label: 'Decomposition', shortLabel: 'Dec', key: 'decomposition' },
  { label: 'Debugging', shortLabel: 'Deb', key: 'debugging' },
];

const DEFAULT_PROFILE: RadarProfile = {
  verification: { score: 0.5, confidence: 0.3 },
  velocity: { score: 0.5, confidence: 0.3 },
  optimization: { score: 0.5, confidence: 0.3 },
  decomposition: { score: 0.5, confidence: 0.3 },
  debugging: { score: 0.5, confidence: 0.3 },
};

export function RadarChart({
  profile,
  size = 200,
  showLabels = true,
  showConfidence = false,
  className = '',
}: RadarChartProps) {
  const activeProfile = profile || DEFAULT_PROFILE;
  const centerX = size / 2;
  const centerY = size / 2;
  const maxRadius = (size / 2) - (showLabels ? 30 : 10);
  const numSides = RADAR_DIMENSIONS.length;
  const angleStep = (2 * Math.PI) / numSides;

  const points: RadarPoint[] = useMemo(() => {
    return RADAR_DIMENSIONS.map((dim) => {
      const dimension = activeProfile[dim.key];
      return {
        ...dim,
        score: dimension?.score ?? 0.5,
        confidence: dimension?.confidence ?? 0.3,
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

  // Background grid circles
  const gridCircles = [0.25, 0.5, 0.75, 1.0];

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
  const scorePolygon = getPolygonPoints(points.map((p) => p.score));

  // Confidence polygon (optional)
  const confidencePolygon = showConfidence
    ? getPolygonPoints(points.map((p) => p.score * p.confidence))
    : null;

  // Label positions
  const labelPositions = useMemo(() => {
    return points.map((point, i) => {
      const angle = (i * angleStep) - (Math.PI / 2);
      const labelRadius = maxRadius + 20;
      const x = centerX + labelRadius * Math.cos(angle);
      const y = centerY + labelRadius * Math.sin(angle);
      return { x, y, point };
    });
  }, [points, centerX, centerY, maxRadius, angleStep]);

  return (
    <div className={`relative ${className}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background grid */}
        <g className="fill-none stroke-gray-700/50">
          {/* Concentric circles */}
          {gridCircles.map((ratio) => (
            <polygon
              key={ratio}
              points={getPolygonPoints(Array(numSides).fill(ratio))}
              strokeWidth="1"
              className="stroke-gray-700/30"
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
              className="stroke-gray-700/30"
            />
          ))}
        </g>

        {/* Confidence polygon (inner, more transparent) */}
        {confidencePolygon && (
          <polygon
            points={confidencePolygon}
            className="fill-primary-500/20 stroke-primary-500/40"
            strokeWidth="1"
          />
        )}

        {/* Score polygon */}
        <polygon
          points={scorePolygon}
          className="fill-primary-500/30 stroke-primary-500"
          strokeWidth="2"
        />

        {/* Data points */}
        {points.map((point, i) => {
          const angle = (i * angleStep) - (Math.PI / 2);
          const radius = point.score * maxRadius;
          const x = centerX + radius * Math.cos(angle);
          const y = centerY + radius * Math.sin(angle);

          return (
            <circle
              key={point.key}
              cx={x}
              cy={y}
              r="4"
              className="fill-primary-500 stroke-white"
              strokeWidth="2"
            />
          );
        })}
      </svg>

      {/* Labels */}
      {showLabels && (
        <div className="absolute inset-0 pointer-events-none">
          {labelPositions.map(({ x, y, point }) => {
            // Adjust text anchor based on position
            const relX = x - centerX;
            let textAnchor = 'middle';
            let xOffset = 0;

            if (relX > 10) {
              textAnchor = 'start';
              xOffset = 5;
            } else if (relX < -10) {
              textAnchor = 'end';
              xOffset = -5;
            }

            return (
              <div
                key={point.key}
                className="absolute text-xs text-gray-400"
                style={{
                  left: x + xOffset,
                  top: y,
                  transform: 'translate(-50%, -50%)',
                  textAlign: textAnchor as 'start' | 'end' | 'center',
                }}
              >
                <span className="font-medium">{point.shortLabel}</span>
                <span className="block text-[10px] text-gray-500">
                  {Math.round(point.score * 100)}%
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
 * Compact version of radar chart for small spaces
 */
export function RadarChartMini({
  profile,
  size = 80,
  className = '',
}: {
  profile: RadarProfile | null;
  size?: number;
  className?: string;
}) {
  return (
    <RadarChart
      profile={profile}
      size={size}
      showLabels={false}
      showConfidence={false}
      className={className}
    />
  );
}

/**
 * Radar chart with legend
 */
export function RadarChartWithLegend({
  profile,
  size = 200,
  className = '',
}: {
  profile: RadarProfile | null;
  size?: number;
  className?: string;
}) {
  const activeProfile = profile || DEFAULT_PROFILE;

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      <RadarChart
        profile={profile}
        size={size}
        showLabels={false}
        showConfidence={true}
      />

      {/* Legend */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
        {RADAR_DIMENSIONS.map((dim) => {
          const dimension = activeProfile[dim.key];
          const score = dimension?.score ?? 0.5;
          const confidence = dimension?.confidence ?? 0.3;

          return (
            <div key={dim.key} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary-500" />
              <div>
                <span className="text-gray-300">{dim.label}</span>
                <span className="text-gray-500 ml-1">
                  {Math.round(score * 100)}%
                </span>
                {confidence < 0.5 && (
                  <span className="text-yellow-500 text-xs ml-1" title="Low confidence">
                    *
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
