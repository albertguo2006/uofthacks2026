# Phase 1 Implementation: Data Schema Extensions ✅

## Overview
Phase 1 of the TwelveLabs Behavioral Analysis integration has been successfully implemented. This phase focused on creating the foundational data schemas and models necessary for detecting and tracking suspicious behaviors in candidate interview videos.

## What Was Implemented

### 1. **Behavioral Analysis Models** (`apps/api/models/behavioral_analysis.py`)
Created comprehensive Pydantic models for:

- **BehaviorType Enum**: 12 types of suspicious behaviors
  - Visual: looking_away, multiple_people, phone_usage, etc.
  - Audio: multiple_voices, whispering, background_voices, etc.
  - Environmental: environment_change, screen_sharing_issues, etc.

- **Core Models**:
  - `SuspiciousSegment`: Individual detected behavior with timestamp, confidence, severity
  - `BehavioralMetrics`: Aggregated scores for eye contact, environment, audio, focus
  - `BehavioralAnalysis`: Complete analysis results including integrity score
  - `ProctoringMetrics`: Candidate-level metrics across all sessions

- **Extended Models**:
  - `VideoWithBehavioralAnalysis`: Extended video model with behavioral data
  - `PassportWithProctoring`: Extended passport with proctoring metrics

### 2. **Database Migration Script** (`scripts/migrate_behavioral_schema.py`)
Created migration script that:

- Adds `behavioral_analysis` field to videos collection
- Adds `proctoring_metrics` field to passports collection
- Extends proctoring_sessions with integrity scores
- Creates new `behavioral_analytics` collection
- Includes indexes for efficient querying
- Provides rollback capability

### 3. **Helper Functions** (`apps/api/utils/behavioral_helpers.py`)
Implemented `BehavioralAnalysisHelper` class with:

- `calculate_integrity_score()`: Weighted scoring algorithm
- `should_flag_for_review()`: Automatic flagging logic
- `aggregate_behavioral_metrics()`: Metric calculation from segments
- `generate_anomaly_summary()`: Human-readable summaries
- `update_proctoring_metrics()`: Profile update logic
- `prioritize_segments()`: Segment prioritization
- `merge_overlapping_segments()`: Temporal segment merging

### 4. **Configuration System** (`apps/api/config/behavioral_config.py`)
Comprehensive configuration including:

- **Behavior Queries**: 12 TwelveLabs search queries with confidence thresholds
- **Integrity Thresholds**: clean (0.85), review (0.70), flag (0.50)
- **Scoring Weights**: 70% metrics, 30% segments
- **Severity Penalties**: Low (0.02), Medium (0.05), High (0.10)
- **Environment Configs**: Development, Production, Testing variants

## Key Data Structures

### Behavioral Analysis in Video Document
```javascript
{
  "behavioral_analysis": {
    "analyzed_at": ISODate("2024-01-17T10:00:00Z"),
    "suspicious_segments": [
      {
        "segment_id": "looking_away_45",
        "start_time": 45.2,
        "end_time": 52.8,
        "behavior_type": "looking_away",
        "confidence": 0.87,
        "severity": "high",
        "description": "Candidate looking away from screen"
      }
    ],
    "behavioral_metrics": {
      "eye_contact_consistency": 0.75,
      "environment_stability": 0.90,
      "audio_consistency": 0.95,
      "focus_score": 0.80
    },
    "overall_integrity_score": 0.82,
    "flagged_for_review": false,
    "anomaly_summary": "Minor anomalies detected."
  }
}
```

### Proctoring Metrics in Passport
```javascript
{
  "proctoring_metrics": {
    "overall_integrity_score": 0.88,
    "total_sessions_analyzed": 5,
    "flagged_sessions_count": 1,
    "behavioral_patterns": {
      "consistent_environment": true,
      "maintains_focus": true,
      "professional_conduct": true
    },
    "common_flags": [
      {
        "behavior_type": "looking_away",
        "frequency": 3,
        "last_occurrence": ISODate("2024-01-15T14:30:00Z")
      }
    ],
    "review_status": "clean"
  }
}
```

## How to Use Phase 1 Implementation

### 1. Run Database Migration
```bash
cd scripts
python migrate_behavioral_schema.py

# To verify migration:
python migrate_behavioral_schema.py --verify

# To rollback if needed:
python migrate_behavioral_schema.py --rollback
```

### 2. Import Models in Your Code
```python
from apps.api.models.behavioral_analysis import (
    BehavioralAnalysis,
    SuspiciousSegment,
    BehavioralMetrics,
    ProctoringMetrics,
    BehaviorType,
    SeverityLevel
)
```

### 3. Use Helper Functions
```python
from apps.api.utils.behavioral_helpers import BehavioralAnalysisHelper

# Calculate integrity score
score = BehavioralAnalysisHelper.calculate_integrity_score(
    suspicious_segments=segments,
    behavioral_metrics=metrics
)

# Check if should flag
should_flag, reasons = BehavioralAnalysisHelper.should_flag_for_review(
    integrity_score=score,
    suspicious_segments=segments
)
```

### 4. Access Configuration
```python
from apps.api.config.behavioral_config import get_behavioral_config

config = get_behavioral_config("development")
queries = config.get_all_behavior_queries()
thresholds = config.INTEGRITY_THRESHOLDS
```

## Testing Phase 1

### Unit Tests to Write
1. Test integrity score calculation with various inputs
2. Test flagging logic with edge cases
3. Test segment merging algorithm
4. Test metric aggregation accuracy

### Integration Tests
1. Test database migration script
2. Test model serialization/deserialization
3. Test configuration loading

## Next Steps (Phase 2)

With Phase 1 complete, the next phase will:

1. **Implement TwelveLabs Service Extension** (`services/twelvelabs_behavior.py`)
   - Add behavioral analysis methods
   - Implement parallel search for all behavior types
   - Create video analysis pipeline

2. **Create API Endpoints** (`routes/proctoring_analysis.py`)
   - POST `/proctoring/{session_id}/analyze-video`
   - GET `/proctoring/{session_id}/behavioral-analysis`

3. **Background Task Processing**
   - Async video analysis
   - Result aggregation
   - Profile updates

## Files Created in Phase 1

| File | Purpose |
|------|---------|
| `apps/api/models/behavioral_analysis.py` | Core data models and schemas |
| `scripts/migrate_behavioral_schema.py` | Database migration script |
| `apps/api/utils/behavioral_helpers.py` | Helper functions and utilities |
| `apps/api/config/behavioral_config.py` | Configuration and settings |

## Validation Checklist

- [x] Models can be imported without errors
- [x] Migration script runs successfully
- [x] Helper functions have proper type hints
- [x] Configuration covers all behavior types
- [x] Enums are properly defined
- [x] Scoring algorithm is implemented
- [x] Review thresholds are configured
- [x] Environment-specific configs available

## Notes

- All timestamps use UTC timezone
- Confidence scores are normalized to 0-1 scale
- Severity levels follow HIGH > MEDIUM > LOW priority
- Integrity scores below 0.7 trigger automatic review
- Configuration can be customized per environment

---

**Phase 1 Status: ✅ COMPLETE**

Ready to proceed with Phase 2: TwelveLabs Service Implementation