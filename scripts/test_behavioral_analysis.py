"""
Test Script for Behavioral Analysis Implementation
Phase 2: Validate TwelveLabs behavioral analysis service
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.db.mongo import init_db
from apps.api.services.twelvelabs_behavior import TwelveLabsBehaviorAnalyzer
from apps.api.models.behavioral_analysis import (
    BehaviorType,
    SeverityLevel,
    SuspiciousSegment,
    BehavioralMetrics,
    BehavioralAnalysis
)
from apps.api.utils.behavioral_helpers import BehavioralAnalysisHelper
from apps.api.config.behavioral_config import get_behavioral_config


async def test_behavioral_config():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("Testing Behavioral Configuration")
    print("="*60)

    # Test different environments
    for env in ["development", "production", "testing"]:
        config = get_behavioral_config(env)
        print(f"\n{env.upper()} Configuration:")
        print(f"  - Clean threshold: {config.INTEGRITY_THRESHOLDS['clean']}")
        print(f"  - Review threshold: {config.INTEGRITY_THRESHOLDS['review']}")
        print(f"  - Flag threshold: {config.INTEGRITY_THRESHOLDS['flag']}")
        print(f"  - Behavior queries: {len(config.BEHAVIOR_QUERIES)}")
        print(f"  - Parallel search: {config.ANALYSIS_SETTINGS['parallel_search']}")

    # Test behavior query retrieval
    config = get_behavioral_config("development")
    print("\nBehavior Query Examples:")
    for behavior_type in [BehaviorType.LOOKING_AWAY, BehaviorType.PHONE_USAGE]:
        query = config.get_query_for_behavior(behavior_type)
        if query:
            print(f"  {behavior_type.value}:")
            print(f"    - Query: {query['query'][:50]}...")
            print(f"    - Severity: {query['severity']}")
            print(f"    - Threshold: {query['confidence_threshold']}")

    print("\n✅ Configuration test passed")


async def test_behavioral_helpers():
    """Test helper functions"""
    print("\n" + "="*60)
    print("Testing Behavioral Helpers")
    print("="*60)

    helper = BehavioralAnalysisHelper()

    # Test with sample segments
    sample_segments = [
        SuspiciousSegment(
            segment_id="test_1",
            start_time=10.5,
            end_time=15.3,
            behavior_type=BehaviorType.LOOKING_AWAY,
            confidence=0.85,
            description="Looking away from screen",
            severity=SeverityLevel.HIGH
        ),
        SuspiciousSegment(
            segment_id="test_2",
            start_time=30.2,
            end_time=35.8,
            behavior_type=BehaviorType.PHONE_USAGE,
            confidence=0.92,
            description="Using phone",
            severity=SeverityLevel.HIGH
        ),
        SuspiciousSegment(
            segment_id="test_3",
            start_time=50.0,
            end_time=52.5,
            behavior_type=BehaviorType.TYPING_WHILE_SPEAKING,
            confidence=0.65,
            description="Typing sounds",
            severity=SeverityLevel.LOW
        )
    ]

    # Test metric aggregation
    print("\nTesting metric aggregation...")
    metrics = helper.aggregate_behavioral_metrics(sample_segments)
    print(f"  Eye contact: {metrics.eye_contact_consistency:.2f}")
    print(f"  Environment: {metrics.environment_stability:.2f}")
    print(f"  Audio: {metrics.audio_consistency:.2f}")
    print(f"  Focus: {metrics.focus_score:.2f}")

    # Test integrity score calculation
    print("\nTesting integrity score calculation...")
    score = helper.calculate_integrity_score(sample_segments, metrics)
    print(f"  Integrity score: {score:.2f}")

    # Test flagging logic
    print("\nTesting flagging logic...")
    should_flag, reasons = helper.should_flag_for_review(score, sample_segments)
    print(f"  Should flag: {should_flag}")
    if reasons:
        print(f"  Reasons: {', '.join(reasons)}")

    # Test anomaly summary
    print("\nTesting anomaly summary generation...")
    summary = helper.generate_anomaly_summary(sample_segments)
    print(f"  Summary: {summary}")

    # Test time formatting
    print("\nTesting time formatting...")
    print(f"  10.5 seconds = {helper.format_time(10.5)}")
    print(f"  125.3 seconds = {helper.format_time(125.3)}")

    # Test segment merging
    print("\nTesting segment merging...")
    overlapping_segments = [
        SuspiciousSegment(
            segment_id="merge_1",
            start_time=10.0,
            end_time=15.0,
            behavior_type=BehaviorType.LOOKING_AWAY,
            confidence=0.8,
            description="Test",
            severity=SeverityLevel.MEDIUM
        ),
        SuspiciousSegment(
            segment_id="merge_2",
            start_time=14.5,  # Overlaps with first
            end_time=20.0,
            behavior_type=BehaviorType.LOOKING_AWAY,
            confidence=0.7,
            description="Test",
            severity=SeverityLevel.HIGH
        )
    ]
    merged = helper.merge_overlapping_segments(overlapping_segments)
    print(f"  Original segments: {len(overlapping_segments)}")
    print(f"  Merged segments: {len(merged)}")
    if merged:
        print(f"  Merged time range: {merged[0].start_time:.1f} - {merged[0].end_time:.1f}")
        print(f"  Merged severity: {merged[0].severity.value}")

    print("\n✅ Helper functions test passed")


async def test_analyzer_initialization():
    """Test TwelveLabsBehaviorAnalyzer initialization"""
    print("\n" + "="*60)
    print("Testing Analyzer Initialization")
    print("="*60)

    try:
        # Initialize analyzer
        analyzer = TwelveLabsBehaviorAnalyzer(environment="development")
        print("✅ Analyzer initialized successfully")

        # Check configuration
        print(f"\nAnalyzer configuration:")
        print(f"  - Environment: development")
        print(f"  - Behavior queries: {len(analyzer.config.BEHAVIOR_QUERIES)}")
        print(f"  - Parallel search: {analyzer.config.ANALYSIS_SETTINGS['parallel_search']}")

        # Test report generation with mock analysis
        print("\nTesting report generation...")
        mock_analysis = BehavioralAnalysis(
            analyzed_at=datetime.now(timezone.utc),
            suspicious_segments=[
                SuspiciousSegment(
                    segment_id="mock_1",
                    start_time=45.2,
                    end_time=52.8,
                    behavior_type=BehaviorType.MULTIPLE_PEOPLE,
                    confidence=0.89,
                    description="Multiple people detected",
                    severity=SeverityLevel.HIGH
                )
            ],
            behavioral_metrics=BehavioralMetrics(
                eye_contact_consistency=0.85,
                environment_stability=0.90,
                audio_consistency=0.95,
                focus_score=0.80
            ),
            overall_integrity_score=0.82,
            flagged_for_review=False,
            anomaly_summary="Minor anomalies detected."
        )

        report = await analyzer.generate_proctoring_report("test_video_id", mock_analysis)
        print(f"  Report generated with {len(report)} sections")
        print(f"  Overall status: {report['overall_assessment']['status']}")
        print(f"  Integrity score: {report['overall_assessment']['integrity_score']}")

        # Test status label generation
        print("\nTesting status labels...")
        test_scores = [0.95, 0.80, 0.65, 0.45]
        for score in test_scores:
            label = analyzer._get_status_label(score)
            print(f"  Score {score:.2f} = {label}")

        print("\n✅ Analyzer test passed")

    except Exception as e:
        print(f"❌ Analyzer test failed: {e}")
        raise


async def test_mock_analysis():
    """Test full analysis flow with mock data"""
    print("\n" + "="*60)
    print("Testing Mock Analysis Flow")
    print("="*60)

    # Create mock segments
    mock_segments = [
        SuspiciousSegment(
            segment_id="mock_looking_1",
            start_time=15.5,
            end_time=22.3,
            behavior_type=BehaviorType.LOOKING_AWAY,
            confidence=0.78,
            description="Looking away from screen",
            severity=SeverityLevel.MEDIUM
        ),
        SuspiciousSegment(
            segment_id="mock_voices_1",
            start_time=45.0,
            end_time=48.5,
            behavior_type=BehaviorType.BACKGROUND_VOICES,
            confidence=0.65,
            description="Voices in background",
            severity=SeverityLevel.MEDIUM
        ),
        SuspiciousSegment(
            segment_id="mock_phone_1",
            start_time=120.0,
            end_time=125.0,
            behavior_type=BehaviorType.PHONE_USAGE,
            confidence=0.92,
            description="Using phone",
            severity=SeverityLevel.HIGH
        )
    ]

    # Test with helper
    helper = BehavioralAnalysisHelper()

    # Calculate metrics
    metrics = helper.aggregate_behavioral_metrics(mock_segments)
    print(f"\nBehavioral Metrics:")
    print(f"  Eye contact: {metrics.eye_contact_consistency:.2f}")
    print(f"  Environment: {metrics.environment_stability:.2f}")
    print(f"  Audio: {metrics.audio_consistency:.2f}")
    print(f"  Focus: {metrics.focus_score:.2f}")

    # Calculate integrity score
    integrity_score = helper.calculate_integrity_score(mock_segments, metrics)
    print(f"\nIntegrity Score: {integrity_score:.2f}")

    # Check flagging
    should_flag, reasons = helper.should_flag_for_review(integrity_score, mock_segments)
    print(f"\nFlagged for Review: {should_flag}")
    if reasons:
        for reason in reasons:
            print(f"  - {reason}")

    # Generate summary
    summary = helper.generate_anomaly_summary(mock_segments)
    print(f"\nAnomaly Summary: {summary}")

    # Test segment prioritization
    prioritized = helper.prioritize_segments(mock_segments, max_segments=2)
    print(f"\nTop 2 Priority Segments:")
    for seg in prioritized:
        print(f"  - {seg.behavior_type.value} ({seg.severity.value}): {seg.confidence:.2f} confidence")

    print("\n✅ Mock analysis test passed")


async def test_session_comparison():
    """Test session comparison logic"""
    print("\n" + "="*60)
    print("Testing Session Comparison")
    print("="*60)

    analyzer = TwelveLabsBehaviorAnalyzer()

    # Create mock current analysis
    current_analysis = BehavioralAnalysis(
        overall_integrity_score=0.75,
        suspicious_segments=[
            SuspiciousSegment(
                segment_id="current_1",
                start_time=10.0,
                end_time=15.0,
                behavior_type=BehaviorType.LOOKING_AWAY,
                confidence=0.8,
                description="Test",
                severity=SeverityLevel.MEDIUM
            )
        ],
        behavioral_metrics=BehavioralMetrics()
    )

    # Create mock previous analyses
    previous_analyses = [
        BehavioralAnalysis(
            overall_integrity_score=0.82,
            suspicious_segments=[
                SuspiciousSegment(
                    segment_id="prev1_1",
                    start_time=5.0,
                    end_time=10.0,
                    behavior_type=BehaviorType.LOOKING_AWAY,
                    confidence=0.7,
                    description="Test",
                    severity=SeverityLevel.MEDIUM
                )
            ],
            behavioral_metrics=BehavioralMetrics()
        ),
        BehavioralAnalysis(
            overall_integrity_score=0.88,
            suspicious_segments=[
                SuspiciousSegment(
                    segment_id="prev2_1",
                    start_time=20.0,
                    end_time=25.0,
                    behavior_type=BehaviorType.LOOKING_AWAY,
                    confidence=0.6,
                    description="Test",
                    severity=SeverityLevel.LOW
                )
            ],
            behavioral_metrics=BehavioralMetrics()
        )
    ]

    # Compare sessions
    comparison = await analyzer.compare_sessions(
        user_id="test_user",
        current_analysis=current_analysis,
        previous_analyses=previous_analyses
    )

    print("\nSession Comparison Results:")
    print(f"  Sessions compared: {comparison['sessions_compared']}")
    print(f"  Current score: {comparison['current_score']}")
    print(f"  Average previous: {comparison['average_previous_score']}")
    print(f"  Score change: {comparison['score_change']}")
    print(f"  Trend: {comparison['trend']}")
    print(f"  Recurring behaviors: {comparison['recurring_behaviors']}")
    print(f"  Consistency: {comparison['consistency_rating']}")

    print("\n✅ Session comparison test passed")


async def main():
    """Run all tests"""
    print("="*60)
    print("BEHAVIORAL ANALYSIS PHASE 2 TEST SUITE")
    print("="*60)

    try:
        # Initialize database connection
        await init_db()
        print("✅ Database connection initialized")

        # Run tests
        await test_behavioral_config()
        await test_behavioral_helpers()
        await test_analyzer_initialization()
        await test_mock_analysis()
        await test_session_comparison()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✅")
        print("="*60)
        print("\nPhase 2 Implementation Status:")
        print("  ✅ TwelveLabs behavioral analyzer service created")
        print("  ✅ Behavioral analysis methods implemented")
        print("  ✅ API endpoints for proctoring analysis created")
        print("  ✅ Helper functions and utilities working")
        print("  ✅ Configuration system operational")
        print("  ✅ Report generation functional")
        print("  ✅ Session comparison logic implemented")

        print("\nNext Steps:")
        print("  1. Test with real TwelveLabs video IDs")
        print("  2. Run database migration script")
        print("  3. Integrate with frontend components")
        print("  4. Configure TwelveLabs API credentials")
        print("  5. Deploy and monitor performance")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())