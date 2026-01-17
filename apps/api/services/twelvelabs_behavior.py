"""
TwelveLabs Behavioral Analysis Service
Phase 2: Extended TwelveLabs service for detecting suspicious behaviors in interview videos
"""

import asyncio
import httpx
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import json

from services.twelvelabs import TwelveLabsService
from models.behavioral_analysis import (
    BehaviorType,
    SeverityLevel,
    SuspiciousSegment,
    BehavioralMetrics,
    BehavioralAnalysis,
    DetectionStats,
    BehaviorQuery
)
from utils.behavioral_helpers import BehavioralAnalysisHelper
from behavioral_config.behavioral_config import get_behavioral_config
from db.collections import Collections


class TwelveLabsBehaviorAnalyzer(TwelveLabsService):
    """
    Extended TwelveLabs service for behavioral analysis of interview videos.
    Detects suspicious behaviors and calculates integrity scores.
    """

    def __init__(self, environment: str = "development"):
        """
        Initialize the behavioral analyzer with configuration

        Args:
            environment: Environment name (development/production/testing)
        """
        super().__init__()
        self.config = get_behavioral_config(environment)
        self.helper = BehavioralAnalysisHelper()

    async def analyze_suspicious_behaviors(
        self,
        video_id: str,
        session_id: str,
        user_id: str
    ) -> BehavioralAnalysis:
        """
        Comprehensive behavioral analysis of interview video.
        Main entry point for analyzing a video for suspicious behaviors.

        Args:
            video_id: TwelveLabs video ID
            session_id: Interview session ID
            user_id: Candidate user ID

        Returns:
            Complete BehavioralAnalysis object with all detected behaviors
        """
        print(f"Starting behavioral analysis for video {video_id}, session {session_id}")

        try:
            # Get all behavior queries from configuration
            behavior_queries = self.config.BEHAVIOR_QUERIES

            # Run searches in parallel or sequentially based on config
            if self.config.ANALYSIS_SETTINGS["parallel_search"]:
                suspicious_segments = await self._parallel_behavior_search(
                    video_id, behavior_queries
                )
            else:
                suspicious_segments = await self._sequential_behavior_search(
                    video_id, behavior_queries
                )

            # Merge overlapping segments
            if suspicious_segments:
                suspicious_segments = self.helper.merge_overlapping_segments(
                    suspicious_segments,
                    overlap_threshold=self.config.TIME_SETTINGS["segment_merge_threshold"]
                )

            # Calculate behavioral metrics from segments
            behavioral_metrics = self.helper.aggregate_behavioral_metrics(suspicious_segments)

            # Calculate overall integrity score
            integrity_score = self.helper.calculate_integrity_score(
                suspicious_segments, behavioral_metrics
            )

            # Determine if review is needed
            should_flag, review_reasons = self.helper.should_flag_for_review(
                integrity_score, suspicious_segments
            )

            # Generate anomaly summary
            anomaly_summary = self.helper.generate_anomaly_summary(suspicious_segments)

            # Calculate detection statistics
            high_confidence_flags = sum(
                1 for s in suspicious_segments
                if s.severity == SeverityLevel.HIGH and s.confidence > 0.7
            )

            detection_stats = DetectionStats(
                total_segments_analyzed=len(behavior_queries),
                suspicious_segments_count=len(suspicious_segments),
                high_confidence_flags=high_confidence_flags
            )

            # Create and return behavioral analysis
            analysis = BehavioralAnalysis(
                analyzed_at=datetime.now(timezone.utc),
                analysis_version="1.0",
                suspicious_segments=suspicious_segments,
                behavioral_metrics=behavioral_metrics,
                overall_integrity_score=integrity_score,
                flagged_for_review=should_flag,
                review_required_reasons=review_reasons,
                anomaly_summary=anomaly_summary,
                detection_stats=detection_stats
            )

            print(f"Behavioral analysis complete. Integrity score: {integrity_score:.2f}")
            return analysis

        except Exception as e:
            print(f"Error during behavioral analysis: {e}")
            # Return a default analysis with error state
            return BehavioralAnalysis(
                analyzed_at=datetime.now(timezone.utc),
                anomaly_summary=f"Analysis failed: {str(e)}",
                overall_integrity_score=1.0,  # Default to clean on error
                flagged_for_review=False
            )

    async def _parallel_behavior_search(
        self,
        video_id: str,
        behavior_queries: List[Dict]
    ) -> List[SuspiciousSegment]:
        """
        Search for all behaviors in parallel using asyncio

        Args:
            video_id: TwelveLabs video ID
            behavior_queries: List of behavior query configurations

        Returns:
            List of all detected suspicious segments
        """
        # Create tasks for each behavior search
        tasks = []
        for query_config in behavior_queries:
            task = self._search_for_behavior(
                video_id=video_id,
                behavior_type=query_config["behavior_type"],
                query=query_config["query"],
                severity=query_config["severity"],
                confidence_threshold=query_config["confidence_threshold"]
            )
            tasks.append(task)

        # Execute all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all segments
        all_segments = []
        for result in results:
            if isinstance(result, list):  # Success
                all_segments.extend(result)
            elif isinstance(result, Exception):  # Error
                print(f"Search error: {result}")

        return all_segments

    async def _sequential_behavior_search(
        self,
        video_id: str,
        behavior_queries: List[Dict]
    ) -> List[SuspiciousSegment]:
        """
        Search for behaviors sequentially (for testing/debugging)

        Args:
            video_id: TwelveLabs video ID
            behavior_queries: List of behavior query configurations

        Returns:
            List of all detected suspicious segments
        """
        all_segments = []

        for query_config in behavior_queries:
            try:
                segments = await self._search_for_behavior(
                    video_id=video_id,
                    behavior_type=query_config["behavior_type"],
                    query=query_config["query"],
                    severity=query_config["severity"],
                    confidence_threshold=query_config["confidence_threshold"]
                )
                all_segments.extend(segments)
            except Exception as e:
                print(f"Error searching for {query_config['behavior_type']}: {e}")

        return all_segments

    async def _search_for_behavior(
        self,
        video_id: str,
        behavior_type: BehaviorType,
        query: str,
        severity: SeverityLevel,
        confidence_threshold: float
    ) -> List[SuspiciousSegment]:
        """
        Search for a specific suspicious behavior pattern in the video

        Args:
            video_id: TwelveLabs video ID
            behavior_type: Type of behavior to search for
            query: Search query for TwelveLabs
            severity: Severity level of the behavior
            confidence_threshold: Minimum confidence to include segment

        Returns:
            List of suspicious segments for this behavior
        """
        try:
            # Use parent class method to search
            search_results = await self.search_interview_moments(video_id, query)

            # Filter and convert to suspicious segments
            segments = []
            for idx, result in enumerate(search_results):
                # Check confidence threshold
                if result.get("confidence", 0) < confidence_threshold:
                    continue

                # Validate segment duration
                start_time = result.get("start", 0)
                end_time = result.get("end", start_time + 1)
                duration = end_time - start_time

                if duration < self.config.TIME_SETTINGS["min_segment_duration"]:
                    continue
                if duration > self.config.TIME_SETTINGS["max_segment_duration"]:
                    # Split long segments
                    end_time = start_time + self.config.TIME_SETTINGS["max_segment_duration"]

                # Create suspicious segment
                segment = SuspiciousSegment(
                    segment_id=f"{behavior_type.value}_{start_time:.1f}",
                    start_time=start_time,
                    end_time=end_time,
                    behavior_type=behavior_type,
                    confidence=result.get("confidence", 0.5),
                    description=self.helper.get_behavior_description(behavior_type),
                    severity=severity,
                    thumbnail_url=result.get("thumbnail_url")
                )
                segments.append(segment)

            if segments:
                print(f"Found {len(segments)} segments for {behavior_type.value}")

            return segments

        except Exception as e:
            print(f"Error searching for {behavior_type.value}: {e}")
            return []

    async def analyze_video_with_retry(
        self,
        video_id: str,
        session_id: str,
        user_id: str,
        max_retries: int = 3
    ) -> Optional[BehavioralAnalysis]:
        """
        Analyze video with retry logic for resilience

        Args:
            video_id: TwelveLabs video ID
            session_id: Session ID
            user_id: User ID
            max_retries: Maximum number of retry attempts

        Returns:
            BehavioralAnalysis or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                return await self.analyze_suspicious_behaviors(
                    video_id, session_id, user_id
                )
            except Exception as e:
                print(f"Analysis attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None

    async def get_behavior_highlights(
        self,
        video_id: str,
        behavior_type: BehaviorType,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Get highlighted moments for a specific behavior type

        Args:
            video_id: TwelveLabs video ID
            behavior_type: Type of behavior to search for
            max_results: Maximum number of highlights to return

        Returns:
            List of highlight dictionaries with timestamps and descriptions
        """
        # Get query configuration for this behavior
        query_config = self.config.get_query_for_behavior(behavior_type)
        if not query_config:
            return []

        # Search for the behavior
        segments = await self._search_for_behavior(
            video_id=video_id,
            behavior_type=behavior_type,
            query=query_config["query"],
            severity=query_config["severity"],
            confidence_threshold=query_config["confidence_threshold"]
        )

        # Convert to highlights format
        highlights = []
        for segment in segments[:max_results]:
            highlights.append({
                "timestamp": self.helper.format_time(segment.start_time),
                "end_time": self.helper.format_time(segment.end_time),
                "behavior": behavior_type.value,
                "description": segment.description,
                "confidence": f"{segment.confidence * 100:.0f}%",
                "severity": segment.severity.value,
                "thumbnail_url": segment.thumbnail_url
            })

        return highlights

    async def generate_proctoring_report(
        self,
        video_id: str,
        analysis: BehavioralAnalysis
    ) -> Dict:
        """
        Generate a comprehensive proctoring report from analysis

        Args:
            video_id: TwelveLabs video ID
            analysis: Completed behavioral analysis

        Returns:
            Dictionary containing formatted proctoring report
        """
        # Group segments by behavior type
        behavior_groups = {}
        for segment in analysis.suspicious_segments:
            behavior = segment.behavior_type.value
            if behavior not in behavior_groups:
                behavior_groups[behavior] = []
            behavior_groups[behavior].append({
                "time": f"{self.helper.format_time(segment.start_time)} - {self.helper.format_time(segment.end_time)}",
                "confidence": segment.confidence,
                "severity": segment.severity.value
            })

        # Get top concerns
        top_concerns = []
        high_severity_segments = [
            s for s in analysis.suspicious_segments
            if s.severity == SeverityLevel.HIGH
        ]
        for segment in high_severity_segments[:3]:
            top_concerns.append({
                "behavior": segment.behavior_type.value.replace("_", " ").title(),
                "timestamp": self.helper.format_time(segment.start_time),
                "confidence": f"{segment.confidence * 100:.0f}%"
            })

        # Create report
        report = {
            "video_id": video_id,
            "analysis_date": analysis.analyzed_at.isoformat(),
            "overall_assessment": {
                "integrity_score": analysis.overall_integrity_score,
                "status": self._get_status_label(analysis.overall_integrity_score),
                "requires_review": analysis.flagged_for_review,
                "summary": analysis.anomaly_summary
            },
            "behavioral_metrics": {
                "eye_contact": f"{analysis.behavioral_metrics.eye_contact_consistency * 100:.0f}%",
                "environment": f"{analysis.behavioral_metrics.environment_stability * 100:.0f}%",
                "audio": f"{analysis.behavioral_metrics.audio_consistency * 100:.0f}%",
                "focus": f"{analysis.behavioral_metrics.focus_score * 100:.0f}%"
            },
            "detected_behaviors": behavior_groups,
            "top_concerns": top_concerns,
            "statistics": {
                "total_behaviors_detected": analysis.detection_stats.suspicious_segments_count,
                "high_severity_count": analysis.detection_stats.high_confidence_flags,
                "segments_analyzed": analysis.detection_stats.total_segments_analyzed
            },
            "review_reasons": analysis.review_required_reasons
        }

        return report

    def _get_status_label(self, integrity_score: float) -> str:
        """Get status label based on integrity score"""
        if integrity_score >= self.config.INTEGRITY_THRESHOLDS["clean"]:
            return "Clean"
        elif integrity_score >= self.config.INTEGRITY_THRESHOLDS["review"]:
            return "Minor Concerns"
        elif integrity_score >= self.config.INTEGRITY_THRESHOLDS["flag"]:
            return "Review Recommended"
        else:
            return "Flagged for Review"

    async def compare_sessions(
        self,
        user_id: str,
        current_analysis: BehavioralAnalysis,
        previous_analyses: List[BehavioralAnalysis]
    ) -> Dict:
        """
        Compare current session with previous sessions for pattern detection

        Args:
            user_id: User ID
            current_analysis: Current session analysis
            previous_analyses: List of previous session analyses

        Returns:
            Comparison report dictionary
        """
        if not previous_analyses:
            return {
                "has_history": False,
                "message": "No previous sessions to compare"
            }

        # Calculate averages from previous sessions
        prev_scores = [a.overall_integrity_score for a in previous_analyses]
        avg_prev_score = sum(prev_scores) / len(prev_scores)

        # Check for improvement or decline
        score_change = current_analysis.overall_integrity_score - avg_prev_score
        if abs(score_change) < 0.05:
            trend = "stable"
        elif score_change > 0:
            trend = "improving"
        else:
            trend = "declining"

        # Find recurring behaviors
        current_behaviors = set(s.behavior_type for s in current_analysis.suspicious_segments)

        behavior_frequency = {}
        for analysis in previous_analyses:
            for segment in analysis.suspicious_segments:
                behavior = segment.behavior_type
                behavior_frequency[behavior] = behavior_frequency.get(behavior, 0) + 1

        recurring_behaviors = [
            b.value for b in current_behaviors
            if behavior_frequency.get(b, 0) >= len(previous_analyses) / 2
        ]

        return {
            "has_history": True,
            "sessions_compared": len(previous_analyses),
            "current_score": current_analysis.overall_integrity_score,
            "average_previous_score": round(avg_prev_score, 3),
            "score_change": round(score_change, 3),
            "trend": trend,
            "recurring_behaviors": recurring_behaviors,
            "consistency_rating": "consistent" if len(recurring_behaviors) <= 2 else "inconsistent"
        }


# Standalone functions for background task processing

async def analyze_video_background(
    video_id: str,
    session_id: str,
    user_id: str,
    twelvelabs_video_id: str
):
    """
    Background task to analyze video for suspicious behaviors

    Args:
        video_id: Database video document ID
        session_id: Session ID
        user_id: User ID
        twelvelabs_video_id: TwelveLabs video ID
    """
    print(f"Starting background behavioral analysis for video {video_id}")

    try:
        # Initialize analyzer
        analyzer = TwelveLabsBehaviorAnalyzer()

        # Perform analysis
        analysis = await analyzer.analyze_suspicious_behaviors(
            video_id=twelvelabs_video_id,
            session_id=session_id,
            user_id=user_id
        )

        # Convert to dictionary for MongoDB
        analysis_dict = analysis.model_dump()

        # Update video document with analysis
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {
                "behavioral_analysis": analysis_dict,
                "behavioral_analysis_completed": True
            }}
        )

        # Update passport with proctoring metrics
        await update_passport_proctoring_metrics(user_id, analysis)

        # Update proctoring session if exists
        await Collections.proctoring_sessions().update_one(
            {"session_id": session_id},
            {"$set": {
                "video_analyzed": True,
                "integrity_score": analysis.overall_integrity_score,
                "flagged_for_review": analysis.flagged_for_review,
                "behavioral_analysis_id": video_id
            }}
        )

        # Generate and store proctoring report
        report = await analyzer.generate_proctoring_report(
            twelvelabs_video_id, analysis
        )

        # Store report in database
        await Collections.db().proctoring_reports.insert_one({
            "video_id": video_id,
            "session_id": session_id,
            "user_id": user_id,
            "report": report,
            "created_at": datetime.now(timezone.utc)
        })

        print(f"Background analysis complete for video {video_id}. Score: {analysis.overall_integrity_score:.2f}")

    except Exception as e:
        print(f"Error in background analysis for video {video_id}: {e}")

        # Mark as failed
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {
                "behavioral_analysis_completed": False,
                "behavioral_analysis_error": str(e)
            }}
        )


async def update_passport_proctoring_metrics(
    user_id: str,
    analysis: BehavioralAnalysis
):
    """
    Update user's passport with proctoring metrics from analysis

    Args:
        user_id: User ID
        analysis: Completed behavioral analysis
    """
    from models.behavioral_analysis import ProctoringMetrics

    try:
        # Get existing passport
        passport = await Collections.passports().find_one({"user_id": user_id})

        if passport and "proctoring_metrics" in passport:
            # Update existing metrics
            current_metrics = ProctoringMetrics(**passport["proctoring_metrics"])
        else:
            # Create new metrics
            current_metrics = ProctoringMetrics()

        # Update metrics with new analysis
        helper = BehavioralAnalysisHelper()
        updated_metrics = helper.update_proctoring_metrics(current_metrics, analysis)

        # Save to database
        await Collections.passports().update_one(
            {"user_id": user_id},
            {"$set": {"proctoring_metrics": updated_metrics.model_dump()}},
            upsert=True
        )

        print(f"Updated passport proctoring metrics for user {user_id}")

    except Exception as e:
        print(f"Error updating passport metrics: {e}")