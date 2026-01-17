# TwelveLabs Suspicious Behavior Detection Integration Plan

## Overview
Integration of TwelveLabs video analysis for detecting suspicious behaviors during recorded candidate interviews, with behavioral tracking and anomaly detection.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Video Recording & Analysis Pipeline              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Candidate Interview Recording                                   │
│     └─> Video Upload to TwelveLabs                                 │
│                                                                      │
│  2. TwelveLabs Processing                                          │
│     ├─> Standard Analysis (existing)                               │
│     │   ├─> Communication style                                    │
│     │   ├─> Problem-solving approach                               │
│     │   └─> Technical discussion highlights                        │
│     │                                                              │
│     └─> Suspicious Behavior Detection (NEW)                        │
│         ├─> Visual anomaly detection                               │
│         ├─> Audio pattern analysis                                 │
│         ├─> Environmental consistency check                        │
│         └─> Behavioral timeline generation                         │
│                                                                      │
│  3. Results Aggregation                                            │
│     ├─> Calculate integrity score                                  │
│     ├─> Flag suspicious segments                                   │
│     └─> Generate behavioral summary                                │
│                                                                      │
│  4. Profile Integration                                            │
│     ├─> Update candidate passport                                  │
│     ├─> Store proctoring metrics                                   │
│     └─> Trigger review if needed                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Data Schema Extensions

### 1.1 Extend Video Document Schema

```javascript
// videos collection - add behavioral_analysis field
{
  "_id": ObjectId,
  "user_id": String,
  "session_id": String,
  // ... existing fields ...

  "behavioral_analysis": {
    "analyzed_at": ISODate,
    "analysis_version": "1.0",

    "suspicious_segments": [
      {
        "segment_id": String,
        "start_time": Number,  // seconds
        "end_time": Number,
        "behavior_type": String,  // from enum
        "confidence": Number,  // 0-1
        "description": String,
        "severity": "low" | "medium" | "high",
        "thumbnail_url": String  // from TwelveLabs
      }
    ],

    "behavioral_metrics": {
      "eye_contact_consistency": Number,  // 0-1
      "environment_stability": Number,    // 0-1
      "audio_consistency": Number,         // 0-1
      "focus_score": Number               // 0-1
    },

    "overall_integrity_score": Number,  // 0-1
    "flagged_for_review": Boolean,
    "review_required_reasons": [String],
    "anomaly_summary": String,

    "detection_stats": {
      "total_segments_analyzed": Number,
      "suspicious_segments_count": Number,
      "high_confidence_flags": Number
    }
  }
}
```

### 1.2 Extend Passport Schema

```javascript
// passports collection - add proctoring_metrics
{
  "_id": ObjectId,
  "user_id": String,
  // ... existing fields ...

  "proctoring_metrics": {
    "overall_integrity_score": Number,  // 0-1, averaged across sessions
    "total_sessions_analyzed": Number,
    "flagged_sessions_count": Number,

    "behavioral_patterns": {
      "consistent_environment": Boolean,
      "maintains_focus": Boolean,
      "professional_conduct": Boolean
    },

    "common_flags": [
      {
        "behavior_type": String,
        "frequency": Number,
        "last_occurrence": ISODate
      }
    ],

    "review_status": "clean" | "pending_review" | "reviewed" | "cleared",
    "reviewer_notes": String,
    "last_reviewed_at": ISODate,
    "reviewed_by": String
  }
}
```

## Phase 2: TwelveLabs Service Extensions

### 2.1 New Behavior Detection Methods

```python
# apps/api/services/twelvelabs_behavior.py

from typing import List, Dict, Tuple
import asyncio
from services.twelvelabs import TwelveLabsService

class BehaviorAnalyzer(TwelveLabsService):
    """Extended TwelveLabs service for behavioral analysis."""

    # Define suspicious behavior queries
    SUSPICIOUS_BEHAVIORS = [
        # Visual behaviors
        ("looking_away", "person looking away from camera repeatedly", "high"),
        ("multiple_people", "multiple people visible in video frame", "high"),
        ("phone_usage", "person using phone or mobile device", "high"),
        ("reading_external", "person reading from paper or another screen", "medium"),
        ("covering_camera", "camera being covered or obscured", "high"),

        # Audio behaviors
        ("multiple_voices", "multiple different voices speaking", "high"),
        ("whispering", "whispering or very quiet speaking", "medium"),
        ("background_voices", "other people talking in background", "medium"),
        ("typing_while_speaking", "keyboard typing sounds during explanation", "low"),

        # Environmental
        ("environment_change", "significant background or lighting change", "medium"),
        ("screen_sharing_issues", "external monitors or screens visible", "medium"),
        ("suspicious_movement", "excessive movement or fidgeting", "low"),
    ]

    async def analyze_suspicious_behaviors(
        self,
        video_id: str,
        session_id: str
    ) -> Dict:
        """
        Comprehensive behavioral analysis of interview video.
        Returns detailed suspicious behavior report.
        """

        # Run parallel searches for all behavior types
        search_tasks = [
            self.search_for_behavior(video_id, behavior, query, severity)
            for behavior, query, severity in self.SUSPICIOUS_BEHAVIORS
        ]

        results = await asyncio.gather(*search_tasks)

        # Aggregate and analyze results
        suspicious_segments = []
        for behavior_type, segments in results:
            if segments:
                suspicious_segments.extend(segments)

        # Sort by timestamp
        suspicious_segments.sort(key=lambda x: x["start_time"])

        # Calculate metrics
        metrics = self.calculate_behavioral_metrics(suspicious_segments)
        integrity_score = self.calculate_integrity_score(suspicious_segments, metrics)

        # Determine if review is needed
        high_severity_count = sum(
            1 for s in suspicious_segments
            if s.get("severity") == "high" and s.get("confidence", 0) > 0.7
        )

        flagged_for_review = (
            integrity_score < 0.7 or
            high_severity_count >= 2 or
            len(suspicious_segments) > 5
        )

        return {
            "analyzed_at": datetime.utcnow(),
            "suspicious_segments": suspicious_segments,
            "behavioral_metrics": metrics,
            "overall_integrity_score": integrity_score,
            "flagged_for_review": flagged_for_review,
            "anomaly_summary": self.generate_anomaly_summary(suspicious_segments),
            "detection_stats": {
                "total_segments_analyzed": len(results),
                "suspicious_segments_count": len(suspicious_segments),
                "high_confidence_flags": high_severity_count
            }
        }

    async def search_for_behavior(
        self,
        video_id: str,
        behavior_type: str,
        query: str,
        severity: str
    ) -> Tuple[str, List[Dict]]:
        """Search for specific suspicious behavior pattern."""

        try:
            segments = await self.search_interview_moments(video_id, query)

            # Filter and enrich segments
            enriched_segments = []
            for segment in segments:
                if segment.get("confidence", 0) > 0.5:  # Confidence threshold
                    enriched_segments.append({
                        "segment_id": f"{behavior_type}_{segment['start']}",
                        "start_time": segment["start"],
                        "end_time": segment["end"],
                        "behavior_type": behavior_type,
                        "confidence": segment["confidence"],
                        "description": f"Detected: {query}",
                        "severity": severity,
                        "thumbnail_url": segment.get("thumbnail_url")
                    })

            return (behavior_type, enriched_segments)

        except Exception as e:
            print(f"Error searching for {behavior_type}: {e}")
            return (behavior_type, [])

    def calculate_behavioral_metrics(self, segments: List[Dict]) -> Dict:
        """Calculate behavioral metrics from detected segments."""

        # Initialize metrics
        metrics = {
            "eye_contact_consistency": 1.0,
            "environment_stability": 1.0,
            "audio_consistency": 1.0,
            "focus_score": 1.0
        }

        # Adjust based on detected behaviors
        for segment in segments:
            behavior = segment["behavior_type"]
            confidence = segment["confidence"]
            severity_weight = {"low": 0.1, "medium": 0.2, "high": 0.3}
            weight = severity_weight.get(segment["severity"], 0.1)

            if behavior in ["looking_away", "covering_camera"]:
                metrics["eye_contact_consistency"] -= weight * confidence

            if behavior in ["environment_change", "screen_sharing_issues"]:
                metrics["environment_stability"] -= weight * confidence

            if behavior in ["multiple_voices", "whispering", "background_voices"]:
                metrics["audio_consistency"] -= weight * confidence

            if behavior in ["phone_usage", "reading_external", "multiple_people"]:
                metrics["focus_score"] -= weight * confidence

        # Ensure metrics stay in 0-1 range
        for key in metrics:
            metrics[key] = max(0, min(1, metrics[key]))

        return metrics

    def calculate_integrity_score(
        self,
        segments: List[Dict],
        metrics: Dict
    ) -> float:
        """
        Calculate overall integrity score.
        Weighted combination of metrics and segment analysis.
        """

        # Base score from metrics (70% weight)
        metric_score = sum(metrics.values()) / len(metrics)

        # Penalty based on suspicious segments (30% weight)
        segment_penalty = 0
        for segment in segments:
            severity_multiplier = {
                "low": 0.02,
                "medium": 0.05,
                "high": 0.10
            }
            penalty = severity_multiplier.get(segment["severity"], 0.02)
            segment_penalty += penalty * segment["confidence"]

        segment_score = max(0, 1 - segment_penalty)

        # Weighted combination
        integrity_score = (metric_score * 0.7) + (segment_score * 0.3)

        return round(integrity_score, 3)

    def generate_anomaly_summary(self, segments: List[Dict]) -> str:
        """Generate human-readable summary of detected anomalies."""

        if not segments:
            return "No suspicious behaviors detected during the interview."

        # Count behaviors by type
        behavior_counts = {}
        for segment in segments:
            behavior = segment["behavior_type"]
            behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1

        # Build summary
        summary_parts = []

        high_severity = [s for s in segments if s["severity"] == "high"]
        if high_severity:
            summary_parts.append(
                f"Detected {len(high_severity)} high-severity behavior(s)"
            )

        if behavior_counts:
            top_behaviors = sorted(
                behavior_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            behavior_summary = ", ".join(
                f"{behavior.replace('_', ' ')} ({count}x)"
                for behavior, count in top_behaviors
            )
            summary_parts.append(f"Most frequent: {behavior_summary}")

        return ". ".join(summary_parts) if summary_parts else "Minor anomalies detected."
```

## Phase 3: API Endpoints

### 3.1 Extended Proctoring Routes

```python
# apps/api/routes/proctoring_analysis.py

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from services.twelvelabs_behavior import BehaviorAnalyzer
from db.collections import Collections

router = APIRouter()

@router.post("/{session_id}/analyze-video")
async def analyze_proctoring_video(
    session_id: str,
    video_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Trigger behavioral analysis for a proctoring video."""

    # Verify session and video exist
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"]
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    video = await Collections.videos().find_one({"_id": video_id})
    if not video or video.get("status") != "ready":
        raise HTTPException(status_code=400, detail="Video not ready for analysis")

    # Trigger analysis in background
    background_tasks.add_task(
        analyze_video_behaviors,
        video_id=video_id,
        session_id=session_id,
        user_id=current_user["user_id"]
    )

    return {
        "message": "Behavioral analysis started",
        "video_id": video_id,
        "session_id": session_id
    }

async def analyze_video_behaviors(
    video_id: str,
    session_id: str,
    user_id: str
):
    """Background task to analyze video for suspicious behaviors."""

    analyzer = BehaviorAnalyzer()

    # Get TwelveLabs video ID
    video_doc = await Collections.videos().find_one({"_id": video_id})
    if not video_doc or not video_doc.get("twelvelabs_video_id"):
        return

    twelvelabs_video_id = video_doc["twelvelabs_video_id"]

    # Perform behavioral analysis
    analysis_result = await analyzer.analyze_suspicious_behaviors(
        video_id=twelvelabs_video_id,
        session_id=session_id
    )

    # Update video document with analysis
    await Collections.videos().update_one(
        {"_id": video_id},
        {"$set": {"behavioral_analysis": analysis_result}}
    )

    # Update passport with proctoring metrics
    await update_passport_proctoring_metrics(user_id, analysis_result)

    # Update proctoring session
    await Collections.proctoring_sessions().update_one(
        {"session_id": session_id},
        {"$set": {
            "video_analyzed": True,
            "integrity_score": analysis_result["overall_integrity_score"],
            "flagged_for_review": analysis_result["flagged_for_review"]
        }}
    )

async def update_passport_proctoring_metrics(
    user_id: str,
    analysis_result: dict
):
    """Update user's passport with proctoring metrics."""

    passport = await Collections.passports().find_one({"user_id": user_id})

    if not passport:
        # Create new passport entry
        passport = {
            "user_id": user_id,
            "proctoring_metrics": {
                "overall_integrity_score": analysis_result["overall_integrity_score"],
                "total_sessions_analyzed": 1,
                "flagged_sessions_count": 1 if analysis_result["flagged_for_review"] else 0
            }
        }
        await Collections.passports().insert_one(passport)
    else:
        # Update existing passport
        current_metrics = passport.get("proctoring_metrics", {})

        # Calculate new average integrity score
        total_sessions = current_metrics.get("total_sessions_analyzed", 0)
        current_score = current_metrics.get("overall_integrity_score", 1.0)

        new_total = total_sessions + 1
        new_score = (
            (current_score * total_sessions + analysis_result["overall_integrity_score"])
            / new_total
        )

        await Collections.passports().update_one(
            {"user_id": user_id},
            {"$set": {
                "proctoring_metrics.overall_integrity_score": new_score,
                "proctoring_metrics.total_sessions_analyzed": new_total,
                "proctoring_metrics.flagged_sessions_count":
                    current_metrics.get("flagged_sessions_count", 0) +
                    (1 if analysis_result["flagged_for_review"] else 0)
            }}
        )

@router.get("/{session_id}/behavioral-analysis")
async def get_behavioral_analysis(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get behavioral analysis results for a session."""

    # Get session
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id
    })

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get associated video analysis
    video = await Collections.videos().find_one({
        "session_id": session_id
    })

    if not video or "behavioral_analysis" not in video:
        return {
            "session_id": session_id,
            "analysis_status": "pending",
            "message": "Behavioral analysis not yet available"
        }

    analysis = video["behavioral_analysis"]

    return {
        "session_id": session_id,
        "analysis_status": "complete",
        "integrity_score": analysis["overall_integrity_score"],
        "flagged_for_review": analysis["flagged_for_review"],
        "suspicious_segments": analysis["suspicious_segments"],
        "behavioral_metrics": analysis["behavioral_metrics"],
        "anomaly_summary": analysis["anomaly_summary"],
        "analyzed_at": analysis["analyzed_at"]
    }
```

## Phase 4: Frontend Integration

### 4.1 React Components for Analysis Display

```typescript
// apps/web/src/components/proctoring/BehavioralAnalysis.tsx

import React from 'react';
import { Card, Badge, Progress, Timeline, Alert } from '@/components/ui';

interface BehavioralAnalysisProps {
  analysis: {
    integrity_score: number;
    flagged_for_review: boolean;
    suspicious_segments: Array<{
      start_time: number;
      end_time: number;
      behavior_type: string;
      confidence: number;
      severity: string;
      description: string;
    }>;
    behavioral_metrics: {
      eye_contact_consistency: number;
      environment_stability: number;
      audio_consistency: number;
      focus_score: number;
    };
    anomaly_summary: string;
  };
  onSegmentClick?: (startTime: number) => void;
}

export const BehavioralAnalysis: React.FC<BehavioralAnalysisProps> = ({
  analysis,
  onSegmentClick
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'yellow';
    return 'red';
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'blue',
      medium: 'yellow',
      high: 'red'
    };
    return <Badge color={colors[severity]}>{severity}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Overall Integrity Score */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Proctoring Analysis</h3>

          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-600">Overall Integrity Score</span>
            <span className={`text-2xl font-bold text-${getScoreColor(analysis.integrity_score)}-600`}>
              {(analysis.integrity_score * 100).toFixed(0)}%
            </span>
          </div>

          <Progress
            value={analysis.integrity_score * 100}
            color={getScoreColor(analysis.integrity_score)}
          />

          {analysis.flagged_for_review && (
            <Alert type="warning" className="mt-4">
              This session has been flagged for manual review
            </Alert>
          )}
        </div>
      </Card>

      {/* Behavioral Metrics */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Behavioral Metrics</h3>

          <div className="space-y-3">
            {Object.entries(analysis.behavioral_metrics).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center space-x-2">
                  <Progress
                    value={value * 100}
                    className="w-32"
                    color={getScoreColor(value)}
                  />
                  <span className="text-sm font-medium w-12 text-right">
                    {(value * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Suspicious Segments Timeline */}
      {analysis.suspicious_segments.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              Detected Behaviors ({analysis.suspicious_segments.length})
            </h3>

            <Timeline>
              {analysis.suspicious_segments.map((segment, index) => (
                <Timeline.Item
                  key={index}
                  onClick={() => onSegmentClick?.(segment.start_time)}
                  className="cursor-pointer hover:bg-gray-50 p-3 rounded"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium">
                          {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                        </span>
                        {getSeverityBadge(segment.severity)}
                        <Badge variant="outline">
                          {(segment.confidence * 100).toFixed(0)}% confidence
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">
                        {segment.description}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Type: {segment.behavior_type.replace(/_/g, ' ')}
                      </p>
                    </div>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </div>
        </Card>
      )}

      {/* Summary */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-2">Analysis Summary</h3>
          <p className="text-sm text-gray-600">{analysis.anomaly_summary}</p>
        </div>
      </Card>
    </div>
  );
};

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
```

## Phase 5: Testing & Validation

### 5.1 Test Scenarios

1. **Normal Behavior Baseline**
   - Record clean interview videos
   - Verify low false positive rate
   - Ensure integrity scores > 0.85

2. **Suspicious Behavior Detection**
   - Test each behavior type individually
   - Verify detection accuracy
   - Validate severity classifications

3. **Edge Cases**
   - Poor lighting conditions
   - Network interruptions
   - Background noise

### 5.2 Sample Test Code

```python
# tests/test_behavioral_analysis.py

import pytest
from services.twelvelabs_behavior import BehaviorAnalyzer

@pytest.mark.asyncio
async def test_suspicious_behavior_detection():
    analyzer = BehaviorAnalyzer()

    # Test with known video containing suspicious behaviors
    test_video_id = "test_video_with_behaviors"
    test_session_id = "test_session_123"

    result = await analyzer.analyze_suspicious_behaviors(
        video_id=test_video_id,
        session_id=test_session_id
    )

    assert "suspicious_segments" in result
    assert "overall_integrity_score" in result
    assert 0 <= result["overall_integrity_score"] <= 1

    # Verify flagging logic
    if len(result["suspicious_segments"]) > 5:
        assert result["flagged_for_review"] == True

@pytest.mark.asyncio
async def test_integrity_score_calculation():
    analyzer = BehaviorAnalyzer()

    # Test with different segment combinations
    segments = [
        {"behavior_type": "looking_away", "confidence": 0.8, "severity": "high"},
        {"behavior_type": "phone_usage", "confidence": 0.9, "severity": "high"},
    ]

    metrics = analyzer.calculate_behavioral_metrics(segments)
    score = analyzer.calculate_integrity_score(segments, metrics)

    assert score < 0.7  # Should be flagged
    assert metrics["focus_score"] < 0.8
```

## Deployment Checklist

- [ ] Update MongoDB schema migrations
- [ ] Configure TwelveLabs API credentials
- [ ] Set up video processing background workers
- [ ] Deploy API endpoints
- [ ] Update frontend with analysis components
- [ ] Configure review workflow for flagged candidates
- [ ] Set up monitoring for false positive rates
- [ ] Document behavior detection thresholds
- [ ] Train reviewers on manual verification process
- [ ] Create candidate notification system for flagged sessions

## Security & Privacy Considerations

1. **Data Protection**
   - Store only necessary video segments
   - Implement retention policies
   - Encrypt sensitive behavioral data

2. **Transparency**
   - Inform candidates about proctoring
   - Provide clear behavior guidelines
   - Allow candidates to dispute flags

3. **Fairness**
   - Regular audit of detection accuracy
   - Bias testing across demographics
   - Human review for all flags

## Success Metrics

- **Detection Accuracy**: > 85% true positive rate
- **False Positive Rate**: < 10%
- **Processing Time**: < 2 minutes per video
- **Reviewer Agreement**: > 80% on flagged cases
- **Candidate Experience**: < 5% dispute rate

## Next Steps

1. Implement Phase 1 (Schema Design) ✅
2. Develop behavioral analyzer service
3. Create API endpoints
4. Build frontend components
5. Conduct testing with sample videos
6. Deploy to staging environment
7. Run pilot with volunteer candidates
8. Refine detection thresholds
9. Full production deployment