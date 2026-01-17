"""
Helper functions for behavioral analysis data manipulation
Phase 1: Utility functions for working with behavioral schemas
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from apps.api.models.behavioral_analysis import (
    BehaviorType,
    SeverityLevel,
    SuspiciousSegment,
    BehavioralMetrics,
    BehavioralAnalysis,
    ProctoringMetrics,
    ReviewStatus,
    IntegrityThresholds
)


class BehavioralAnalysisHelper:
    """Helper class for behavioral analysis operations"""

    # Default thresholds
    DEFAULT_THRESHOLDS = IntegrityThresholds()

    # Behavior severity mapping
    BEHAVIOR_SEVERITY_MAP = {
        BehaviorType.MULTIPLE_PEOPLE: SeverityLevel.HIGH,
        BehaviorType.PHONE_USAGE: SeverityLevel.HIGH,
        BehaviorType.COVERING_CAMERA: SeverityLevel.HIGH,
        BehaviorType.MULTIPLE_VOICES: SeverityLevel.HIGH,
        BehaviorType.LOOKING_AWAY: SeverityLevel.MEDIUM,
        BehaviorType.READING_EXTERNAL: SeverityLevel.MEDIUM,
        BehaviorType.WHISPERING: SeverityLevel.MEDIUM,
        BehaviorType.ENVIRONMENT_CHANGE: SeverityLevel.MEDIUM,
        BehaviorType.BACKGROUND_VOICES: SeverityLevel.MEDIUM,
        BehaviorType.SCREEN_SHARING_ISSUES: SeverityLevel.MEDIUM,
        BehaviorType.TYPING_WHILE_SPEAKING: SeverityLevel.LOW,
        BehaviorType.SUSPICIOUS_MOVEMENT: SeverityLevel.LOW,
    }

    @classmethod
    def calculate_integrity_score(
        cls,
        suspicious_segments: List[SuspiciousSegment],
        behavioral_metrics: BehavioralMetrics
    ) -> float:
        """
        Calculate overall integrity score based on segments and metrics

        Args:
            suspicious_segments: List of detected suspicious segments
            behavioral_metrics: Aggregated behavioral metrics

        Returns:
            Float between 0 and 1 representing integrity score
        """
        # Base score from metrics (70% weight)
        metrics_values = [
            behavioral_metrics.eye_contact_consistency,
            behavioral_metrics.environment_stability,
            behavioral_metrics.audio_consistency,
            behavioral_metrics.focus_score
        ]
        metric_score = sum(metrics_values) / len(metrics_values)

        # Penalty based on suspicious segments (30% weight)
        segment_penalty = 0.0
        for segment in suspicious_segments:
            severity_multiplier = {
                SeverityLevel.LOW: 0.02,
                SeverityLevel.MEDIUM: 0.05,
                SeverityLevel.HIGH: 0.10
            }
            penalty = severity_multiplier.get(segment.severity, 0.02)
            segment_penalty += penalty * segment.confidence

        segment_score = max(0, 1 - segment_penalty)

        # Weighted combination
        integrity_score = (metric_score * 0.7) + (segment_score * 0.3)

        return round(max(0.0, min(1.0, integrity_score)), 3)

    @classmethod
    def should_flag_for_review(
        cls,
        integrity_score: float,
        suspicious_segments: List[SuspiciousSegment],
        thresholds: Optional[IntegrityThresholds] = None
    ) -> Tuple[bool, List[str]]:
        """
        Determine if a session should be flagged for review

        Args:
            integrity_score: Overall integrity score
            suspicious_segments: List of detected segments
            thresholds: Optional custom thresholds

        Returns:
            Tuple of (should_flag, reasons)
        """
        if thresholds is None:
            thresholds = cls.DEFAULT_THRESHOLDS

        reasons = []
        should_flag = False

        # Check integrity score threshold
        if integrity_score < thresholds.review_threshold:
            should_flag = True
            reasons.append(f"Integrity score {integrity_score:.2f} below threshold {thresholds.review_threshold}")

        # Check high severity count
        high_severity_count = sum(
            1 for segment in suspicious_segments
            if segment.severity == SeverityLevel.HIGH and segment.confidence > 0.7
        )
        if high_severity_count >= thresholds.max_high_severity_behaviors:
            should_flag = True
            reasons.append(f"Found {high_severity_count} high-severity behaviors")

        # Check total suspicious segments
        if len(suspicious_segments) > thresholds.max_total_suspicious_segments:
            should_flag = True
            reasons.append(f"Too many suspicious segments: {len(suspicious_segments)}")

        return should_flag, reasons

    @classmethod
    def aggregate_behavioral_metrics(
        cls,
        suspicious_segments: List[SuspiciousSegment]
    ) -> BehavioralMetrics:
        """
        Calculate behavioral metrics from suspicious segments

        Args:
            suspicious_segments: List of detected segments

        Returns:
            Aggregated behavioral metrics
        """
        metrics = BehavioralMetrics()

        for segment in suspicious_segments:
            behavior = segment.behavior_type
            confidence = segment.confidence
            severity_weight = {
                SeverityLevel.LOW: 0.1,
                SeverityLevel.MEDIUM: 0.2,
                SeverityLevel.HIGH: 0.3
            }
            weight = severity_weight.get(segment.severity, 0.1)

            # Adjust metrics based on behavior type
            if behavior in [BehaviorType.LOOKING_AWAY, BehaviorType.COVERING_CAMERA]:
                metrics.eye_contact_consistency -= weight * confidence

            if behavior in [BehaviorType.ENVIRONMENT_CHANGE, BehaviorType.SCREEN_SHARING_ISSUES]:
                metrics.environment_stability -= weight * confidence

            if behavior in [BehaviorType.MULTIPLE_VOICES, BehaviorType.WHISPERING,
                           BehaviorType.BACKGROUND_VOICES]:
                metrics.audio_consistency -= weight * confidence

            if behavior in [BehaviorType.PHONE_USAGE, BehaviorType.READING_EXTERNAL,
                           BehaviorType.MULTIPLE_PEOPLE]:
                metrics.focus_score -= weight * confidence

        # Ensure metrics stay in 0-1 range
        metrics.eye_contact_consistency = max(0, min(1, metrics.eye_contact_consistency))
        metrics.environment_stability = max(0, min(1, metrics.environment_stability))
        metrics.audio_consistency = max(0, min(1, metrics.audio_consistency))
        metrics.focus_score = max(0, min(1, metrics.focus_score))

        return metrics

    @classmethod
    def generate_anomaly_summary(
        cls,
        suspicious_segments: List[SuspiciousSegment]
    ) -> str:
        """
        Generate human-readable summary of detected anomalies

        Args:
            suspicious_segments: List of detected segments

        Returns:
            Summary string
        """
        if not suspicious_segments:
            return "No suspicious behaviors detected during the interview."

        # Count behaviors by type
        behavior_counts: Dict[BehaviorType, int] = {}
        for segment in suspicious_segments:
            behavior = segment.behavior_type
            behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1

        # Build summary
        summary_parts = []

        # High severity behaviors
        high_severity = [s for s in suspicious_segments if s.severity == SeverityLevel.HIGH]
        if high_severity:
            summary_parts.append(f"Detected {len(high_severity)} high-severity behavior(s)")

        # Most frequent behaviors
        if behavior_counts:
            top_behaviors = sorted(
                behavior_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            behavior_summary = ", ".join(
                f"{behavior.value.replace('_', ' ')} ({count}x)"
                for behavior, count in top_behaviors
            )
            summary_parts.append(f"Most frequent: {behavior_summary}")

        return ". ".join(summary_parts) if summary_parts else "Minor anomalies detected."

    @classmethod
    def update_proctoring_metrics(
        cls,
        current_metrics: Optional[ProctoringMetrics],
        new_analysis: BehavioralAnalysis
    ) -> ProctoringMetrics:
        """
        Update proctoring metrics with new analysis results

        Args:
            current_metrics: Existing proctoring metrics (or None)
            new_analysis: New behavioral analysis results

        Returns:
            Updated proctoring metrics
        """
        if current_metrics is None:
            current_metrics = ProctoringMetrics()

        # Update session counts
        total_sessions = current_metrics.total_sessions_analyzed
        current_score = current_metrics.overall_integrity_score

        # Calculate new average integrity score
        new_total = total_sessions + 1
        new_score = (
            (current_score * total_sessions + new_analysis.overall_integrity_score)
            / new_total
        )

        current_metrics.overall_integrity_score = round(new_score, 3)
        current_metrics.total_sessions_analyzed = new_total

        if new_analysis.flagged_for_review:
            current_metrics.flagged_sessions_count += 1

        # Update behavioral patterns
        if new_analysis.overall_integrity_score < 0.7:
            if new_analysis.behavioral_metrics.environment_stability < 0.7:
                current_metrics.behavioral_patterns.consistent_environment = False
            if new_analysis.behavioral_metrics.focus_score < 0.7:
                current_metrics.behavioral_patterns.maintains_focus = False

        # Update common flags
        for segment in new_analysis.suspicious_segments:
            # Find or create common flag entry
            flag_entry = next(
                (f for f in current_metrics.common_flags
                 if f.behavior_type == segment.behavior_type),
                None
            )

            if flag_entry:
                flag_entry.frequency += 1
                flag_entry.last_occurrence = datetime.now(timezone.utc)
            else:
                from apps.api.models.behavioral_analysis import CommonFlag
                current_metrics.common_flags.append(
                    CommonFlag(
                        behavior_type=segment.behavior_type,
                        frequency=1,
                        last_occurrence=datetime.now(timezone.utc)
                    )
                )

        # Update review status
        if new_score < 0.7 or current_metrics.flagged_sessions_count >= 2:
            current_metrics.review_status = ReviewStatus.PENDING_REVIEW

        return current_metrics

    @classmethod
    def format_time(cls, seconds: float) -> str:
        """
        Format seconds to MM:SS format

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    @classmethod
    def get_behavior_description(cls, behavior_type: BehaviorType) -> str:
        """
        Get human-readable description for behavior type

        Args:
            behavior_type: Type of behavior

        Returns:
            Description string
        """
        descriptions = {
            BehaviorType.LOOKING_AWAY: "Candidate looking away from screen",
            BehaviorType.MULTIPLE_PEOPLE: "Multiple people detected in frame",
            BehaviorType.PHONE_USAGE: "Phone or mobile device usage",
            BehaviorType.READING_EXTERNAL: "Reading from external sources",
            BehaviorType.COVERING_CAMERA: "Camera being covered or obscured",
            BehaviorType.MULTIPLE_VOICES: "Multiple voices detected",
            BehaviorType.WHISPERING: "Whispering or quiet communication",
            BehaviorType.BACKGROUND_VOICES: "Other voices in background",
            BehaviorType.TYPING_WHILE_SPEAKING: "Keyboard typing during explanation",
            BehaviorType.ENVIRONMENT_CHANGE: "Environment or lighting change",
            BehaviorType.SCREEN_SHARING_ISSUES: "External screens visible",
            BehaviorType.SUSPICIOUS_MOVEMENT: "Excessive movement or fidgeting",
        }
        return descriptions.get(behavior_type, behavior_type.value.replace('_', ' '))

    @classmethod
    def prioritize_segments(
        cls,
        segments: List[SuspiciousSegment],
        max_segments: int = 10
    ) -> List[SuspiciousSegment]:
        """
        Prioritize segments by severity and confidence

        Args:
            segments: List of all segments
            max_segments: Maximum number to return

        Returns:
            Prioritized list of segments
        """
        # Sort by severity (high to low) and then by confidence
        priority_map = {
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1
        }

        sorted_segments = sorted(
            segments,
            key=lambda s: (priority_map.get(s.severity, 0), s.confidence),
            reverse=True
        )

        return sorted_segments[:max_segments]

    @classmethod
    def merge_overlapping_segments(
        cls,
        segments: List[SuspiciousSegment],
        overlap_threshold: float = 2.0  # seconds
    ) -> List[SuspiciousSegment]:
        """
        Merge segments that overlap in time

        Args:
            segments: List of segments
            overlap_threshold: Time threshold for considering overlap

        Returns:
            List with merged segments
        """
        if not segments:
            return []

        # Sort by start time
        sorted_segments = sorted(segments, key=lambda s: s.start_time)
        merged = [sorted_segments[0]]

        for current in sorted_segments[1:]:
            last = merged[-1]

            # Check if segments overlap or are very close
            if current.start_time <= last.end_time + overlap_threshold:
                # Merge segments
                last.end_time = max(last.end_time, current.end_time)
                # Use higher severity
                if priority := {
                    SeverityLevel.HIGH: 3,
                    SeverityLevel.MEDIUM: 2,
                    SeverityLevel.LOW: 1
                }:
                    if priority.get(current.severity, 0) > priority.get(last.severity, 0):
                        last.severity = current.severity
                # Average confidence
                last.confidence = (last.confidence + current.confidence) / 2
            else:
                merged.append(current)

        return merged