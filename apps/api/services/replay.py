"""
Replay Service for Session Timeline Building and Q&A

Provides functionality to:
- Build unified timelines from events, code history, and interventions
- Generate code diffs between snapshots
- Handle natural language Q&A about sessions
- Synchronize timeline with video timestamps
"""

import difflib
import json
from datetime import datetime
from typing import Optional
from bson import ObjectId

from db.collections import Collections
from models.timeline import (
    TimelineEntry,
    Timeline,
    TimelineJump,
    VideoSegment,
    AskResponse,
    QuickInsight,
    QuickInsightsResponse,
)
from services.backboard import BackboardService
from services.twelvelabs import TwelveLabsService


class ReplayService:
    """
    Service for building and querying session replays.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.backboard = BackboardService(user_id)
        self.twelvelabs = TwelveLabsService()

    def _generate_diff(self, old_code: str, new_code: str) -> str:
        """Generate unified diff between two code snapshots."""
        if not old_code or not new_code:
            return ""

        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='previous',
            tofile='current',
            lineterm=''
        )
        return ''.join(diff)

    def _get_event_label(self, event_type: str, properties: dict) -> str:
        """Generate human-readable label for an event."""
        labels = {
            "code_changed": "Code edited",
            "run_attempted": "Run attempted",
            "test_passed": "Test passed",
            "test_failed": "Test failed",
            "error_emitted": f"Error: {properties.get('error_type', 'unknown')}",
            "submission_attempted": "Submission attempted",
            "submission_passed": "All tests passed",
            "submission_failed": f"Failed ({properties.get('tests_passed', 0)}/{properties.get('tests_total', 0)} tests)",
            "hint_requested": "Hint requested",
            "hint_shown": "AI hint shown",
            "contextual_hint_shown": "Contextual hint shown",
            "format_command": "Code formatted",
            "find_command": "Find/Replace used",
            "paste_burst": f"Pasted {properties.get('chars_pasted', '?')} chars",
            "session_started": "Session started",
            "session_ended": "Session ended",
        }
        return labels.get(event_type, event_type.replace("_", " ").title())

    def _get_event_severity(self, event_type: str, properties: dict) -> str:
        """Determine severity/color for an event."""
        if event_type in ["test_passed", "submission_passed"]:
            return "success"
        elif event_type in ["test_failed", "submission_failed", "error_emitted"]:
            return "error"
        elif event_type in ["hint_shown", "contextual_hint_shown", "hint_requested"]:
            return "warning"
        return "info"

    async def build_timeline(self, session_id: str) -> Optional[Timeline]:
        """
        Build a unified timeline for a coding session.
        Combines events, code history, and interventions.
        """
        # Fetch session
        session = await Collections.sessions().find_one({"session_id": session_id})
        if not session:
            return None

        user_id = session.get("user_id")
        task_id = session.get("task_id")

        # Fetch task info
        task = await Collections.tasks().find_one({"task_id": task_id})
        task_title = task.get("title", "Unknown Task") if task else "Unknown Task"

        # Fetch events for this session
        events_cursor = Collections.events().find(
            {"session_id": session_id}
        ).sort("timestamp", 1)
        events = await events_cursor.to_list(length=1000)

        # Fetch interventions for this session
        interventions_cursor = Collections.interventions().find(
            {"session_id": session_id}
        ).sort("created_at", 1)
        interventions = await interventions_cursor.to_list(length=100)

        # Get code history from session
        code_history = session.get("code_history", [])

        # Fetch linked video if any
        video = await Collections.videos().find_one({
            "session_id": session_id,
            "status": "ready"
        })

        # Determine session time bounds
        start_time = session.get("started_at")
        if not start_time and events:
            start_time = events[0].get("timestamp")
        if not start_time:
            start_time = datetime.utcnow()

        end_time = session.get("ended_at")
        if not end_time and events:
            end_time = events[-1].get("timestamp")
        if not end_time:
            end_time = datetime.utcnow()

        # Calculate video offset (difference between session start and video start)
        video_start_offset = 0.0
        if video and video.get("uploaded_at"):
            # If video was uploaded during session, calculate offset
            video_upload_time = video.get("uploaded_at")
            if isinstance(video_upload_time, datetime):
                video_start_offset = (video_upload_time - start_time).total_seconds()
                # Negative offset means video started before session
                video_start_offset = max(0, video_start_offset)

        # Build unified timeline entries
        entries: list[TimelineEntry] = []

        # Create a map of code snapshots by timestamp for quick lookup
        code_snapshot_map = {}
        prev_code = ""
        for snapshot in code_history:
            ts = snapshot.get("timestamp")
            if isinstance(ts, (int, float)):
                ts = datetime.fromtimestamp(ts / 1000)  # Convert ms to datetime
            code_snapshot_map[ts] = {
                "code": snapshot.get("code", ""),
                "prev_code": prev_code,
            }
            prev_code = snapshot.get("code", "")

        # Create intervention map by timestamp
        intervention_map = {}
        for intervention in interventions:
            ts = intervention.get("created_at")
            if ts:
                intervention_map[ts] = intervention

        # Process events and build timeline entries
        prev_code_snapshot = ""
        run_count = 0
        submission_count = 0
        error_count = 0
        intervention_count = len(interventions)
        final_result = None

        for i, event in enumerate(events):
            event_type = event.get("event_type", "unknown")
            timestamp = event.get("timestamp")
            properties = event.get("properties", {})

            # Track statistics
            if event_type == "run_attempted":
                run_count += 1
            elif event_type in ["submission_attempted", "submission_passed", "submission_failed"]:
                submission_count += 1
                if event_type == "submission_passed":
                    final_result = "passed"
                elif event_type == "submission_failed" and final_result != "passed":
                    final_result = "failed"
            elif event_type == "error_emitted":
                error_count += 1

            # Find closest code snapshot
            code_snapshot = None
            code_diff = None
            closest_snapshot_time = None

            for snapshot_time in code_snapshot_map:
                if snapshot_time <= timestamp:
                    if closest_snapshot_time is None or snapshot_time > closest_snapshot_time:
                        closest_snapshot_time = snapshot_time

            if closest_snapshot_time:
                snapshot_data = code_snapshot_map[closest_snapshot_time]
                code_snapshot = snapshot_data["code"]
                if snapshot_data["prev_code"]:
                    code_diff = self._generate_diff(
                        snapshot_data["prev_code"],
                        code_snapshot
                    )
                prev_code_snapshot = code_snapshot

            # Calculate video timestamp
            video_timestamp = None
            if video:
                time_since_start = (timestamp - start_time).total_seconds()
                video_timestamp = time_since_start - video_start_offset
                if video_timestamp < 0:
                    video_timestamp = None

            # Check if this event has an associated intervention
            intervention_data = None
            for int_ts, intervention in intervention_map.items():
                # Check if intervention is within 5 seconds of this event
                time_diff = abs((timestamp - int_ts).total_seconds())
                if time_diff < 5:
                    intervention_data = {
                        "hint": intervention.get("hint"),
                        "type": intervention.get("type"),
                        "personalization_badge": intervention.get("personalization_badge"),
                    }
                    break

            entry = TimelineEntry(
                id=str(event.get("_id", i)),
                timestamp=timestamp,
                type=event_type,
                code_snapshot=code_snapshot,
                code_diff=code_diff,
                event_data=properties,
                video_timestamp_seconds=video_timestamp,
                intervention=intervention_data,
                label=self._get_event_label(event_type, properties),
                severity=self._get_event_severity(event_type, properties),
            )
            entries.append(entry)

        # Add standalone intervention entries (not tied to events)
        for int_ts, intervention in intervention_map.items():
            # Check if this intervention was already attached to an event
            already_attached = False
            for entry in entries:
                if entry.intervention and entry.intervention.get("hint") == intervention.get("hint"):
                    already_attached = True
                    break

            if not already_attached:
                video_timestamp = None
                if video:
                    time_since_start = (int_ts - start_time).total_seconds()
                    video_timestamp = time_since_start - video_start_offset
                    if video_timestamp < 0:
                        video_timestamp = None

                entry = TimelineEntry(
                    id=str(intervention.get("_id", "")),
                    timestamp=int_ts,
                    type="ai_intervention",
                    code_snapshot=None,
                    code_diff=None,
                    event_data=None,
                    video_timestamp_seconds=video_timestamp,
                    intervention={
                        "hint": intervention.get("hint"),
                        "type": intervention.get("type"),
                        "personalization_badge": intervention.get("personalization_badge"),
                    },
                    label="AI Intervention",
                    severity="warning",
                )
                entries.append(entry)

        # Sort entries by timestamp
        entries.sort(key=lambda e: e.timestamp)

        # Calculate duration
        duration_seconds = int((end_time - start_time).total_seconds())

        return Timeline(
            session_id=session_id,
            user_id=user_id,
            task_id=task_id,
            task_title=task_title,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            entries=entries,
            has_video=video is not None,
            video_id=str(video.get("_id")) if video else None,
            video_url=video.get("twelvelabs_video_id") if video else None,
            video_start_offset_seconds=video_start_offset,
            total_runs=run_count,
            total_submissions=submission_count,
            errors_encountered=error_count,
            interventions_received=intervention_count,
            final_result=final_result,
        )

    async def ask_about_session(
        self,
        session_id: str,
        question: str,
        include_video_search: bool = True,
    ) -> AskResponse:
        """
        Answer natural language questions about a session.
        Uses Backboard for intent extraction and TwelveLabs for video search.
        """
        # Build timeline first
        timeline = await self.build_timeline(session_id)
        if not timeline:
            return AskResponse(
                answer="Session not found.",
                timeline_jumps=[],
                video_segments=[],
                confidence=0.0,
            )

        # Prepare timeline summary for AI
        timeline_summary = self._prepare_timeline_summary(timeline)

        # Use Backboard to analyze the question and generate response
        system_prompt = """You are an AI assistant helping recruiters understand coding interview sessions.
You have access to a timeline of events from a coding session.

When answering questions:
1. Reference specific moments by their index number [idx: X]
2. Be specific about what happened and when
3. If asked about approach changes, look for patterns in code diffs and errors
4. If asked about struggles, look for error streaks and time gaps
5. If asked about testing habits, analyze run_attempted and test results patterns

Return JSON with this structure:
{
    "answer": "Your detailed answer here, referencing [idx: X] for specific moments",
    "relevant_indices": [1, 5, 12],  // Timeline indices that support your answer
    "confidence": 0.85  // How confident you are (0-1)
}"""

        user_prompt = f"""Question: {question}

Session Timeline Summary:
{timeline_summary}

Task: {timeline.task_title}
Duration: {timeline.duration_seconds // 60} minutes
Total runs: {timeline.total_runs}
Errors encountered: {timeline.errors_encountered}
Final result: {timeline.final_result or 'incomplete'}"""

        try:
            response = await self.backboard._call_model(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            result = json.loads(response)
            answer = result.get("answer", response)
            relevant_indices = result.get("relevant_indices", [])
            confidence = result.get("confidence", 0.5)
        except (json.JSONDecodeError, Exception):
            answer = "I couldn't analyze this session properly. Please try rephrasing your question."
            relevant_indices = []
            confidence = 0.3

        # Build timeline jumps from relevant indices
        timeline_jumps = []
        for idx in relevant_indices:
            if 0 <= idx < len(timeline.entries):
                entry = timeline.entries[idx]
                timeline_jumps.append(TimelineJump(
                    index=idx,
                    timestamp=entry.timestamp,
                    description=entry.label,
                ))

        # Search video if available and requested
        video_segments = []
        if include_video_search and timeline.has_video and timeline.video_url:
            # Extract search query from question
            search_queries = self._extract_video_search_queries(question)

            for query in search_queries[:3]:  # Limit to 3 queries
                results = await self.twelvelabs.search_interview_moments(
                    timeline.video_url,
                    query
                )
                for result in results[:2]:  # Top 2 per query
                    video_segments.append(VideoSegment(
                        start_time=result.get("start", 0),
                        end_time=result.get("end", 0),
                        confidence=result.get("confidence", 0.5),
                        description=result.get("transcript", "")[:100],
                    ))

        return AskResponse(
            answer=answer,
            timeline_jumps=timeline_jumps,
            video_segments=video_segments,
            confidence=confidence,
        )

    def _prepare_timeline_summary(self, timeline: Timeline) -> str:
        """Prepare a text summary of the timeline for AI analysis."""
        summary_lines = []

        for i, entry in enumerate(timeline.entries):
            time_offset = (entry.timestamp - timeline.start_time).total_seconds()
            minutes = int(time_offset // 60)
            seconds = int(time_offset % 60)

            line = f"[idx: {i}] {minutes:02d}:{seconds:02d} - {entry.label}"

            if entry.severity == "error":
                line += " (ERROR)"
            elif entry.severity == "success":
                line += " (SUCCESS)"

            if entry.intervention:
                line += f" [AI: {entry.intervention.get('type', 'hint')}]"

            if entry.code_diff:
                diff_lines = entry.code_diff.count('\n')
                line += f" [{diff_lines} lines changed]"

            summary_lines.append(line)

        return '\n'.join(summary_lines)

    def _extract_video_search_queries(self, question: str) -> list[str]:
        """Extract relevant video search queries from a question."""
        # Map common question patterns to video search queries
        query_mappings = {
            "approach": ["explaining problem solving approach", "discussing solution strategy"],
            "change": ["changing approach", "trying different solution"],
            "stuck": ["struggling with code", "debugging error"],
            "debug": ["debugging", "fixing error"],
            "test": ["discussing tests", "running tests"],
            "communicate": ["explaining code", "technical communication"],
            "think": ["thinking out loud", "reasoning about problem"],
            "optimize": ["optimizing code", "improving performance"],
        }

        queries = []
        question_lower = question.lower()

        for keyword, search_queries in query_mappings.items():
            if keyword in question_lower:
                queries.extend(search_queries)

        # Default query if nothing specific found
        if not queries:
            queries = ["key moment in coding interview"]

        return queries[:3]

    async def generate_quick_insights(self, session_id: str) -> QuickInsightsResponse:
        """
        Generate pre-computed insights about the session.
        """
        timeline = await self.build_timeline(session_id)
        if not timeline:
            return QuickInsightsResponse(
                session_id=session_id,
                insights=[],
                summary="Session not found.",
            )

        insights = []

        # Find approach changes (large code diffs after errors)
        error_indices = [
            i for i, e in enumerate(timeline.entries)
            if e.type == "error_emitted" or e.severity == "error"
        ]

        for err_idx in error_indices:
            # Look for significant code changes within 5 events after error
            for j in range(err_idx + 1, min(err_idx + 6, len(timeline.entries))):
                entry = timeline.entries[j]
                if entry.code_diff and entry.code_diff.count('\n') > 10:
                    insights.append(QuickInsight(
                        category="approach_change",
                        title="Approach Change Detected",
                        description=f"After encountering an error, the candidate made significant changes (~{entry.code_diff.count(chr(10))} lines)",
                        timeline_index=j,
                        video_timestamp=entry.video_timestamp_seconds,
                    ))
                    break

        # Find debugging efficiency
        if timeline.errors_encountered > 0:
            # Calculate average time between error and next successful run
            avg_debug_time = timeline.duration_seconds / max(timeline.errors_encountered, 1)
            efficiency = "high" if avg_debug_time < 60 else "medium" if avg_debug_time < 180 else "low"

            insights.append(QuickInsight(
                category="debugging_efficiency",
                title=f"Debugging Efficiency: {efficiency.title()}",
                description=f"Average time to recover from errors: ~{int(avg_debug_time)}s",
                timeline_index=None,
                video_timestamp=None,
            ))

        # Find testing habits
        run_events = [e for e in timeline.entries if e.type == "run_attempted"]
        if run_events:
            # Check if they ran code frequently
            runs_per_minute = timeline.total_runs / max(timeline.duration_seconds / 60, 1)
            habit = "iterative" if runs_per_minute > 1 else "batch" if runs_per_minute < 0.3 else "moderate"

            insights.append(QuickInsight(
                category="testing_habit",
                title=f"Testing Style: {habit.title()}",
                description=f"Ran code {timeline.total_runs} times ({runs_per_minute:.1f} runs/minute)",
                timeline_index=None,
                video_timestamp=None,
            ))

        # Find struggle points (multiple errors in sequence)
        consecutive_errors = 0
        max_consecutive = 0
        struggle_idx = None

        for i, entry in enumerate(timeline.entries):
            if entry.severity == "error":
                consecutive_errors += 1
                if consecutive_errors > max_consecutive:
                    max_consecutive = consecutive_errors
                    struggle_idx = i - consecutive_errors + 1
            else:
                consecutive_errors = 0

        if max_consecutive >= 3:
            insights.append(QuickInsight(
                category="struggle_point",
                title="Notable Struggle Point",
                description=f"Encountered {max_consecutive} consecutive errors",
                timeline_index=struggle_idx,
                video_timestamp=timeline.entries[struggle_idx].video_timestamp_seconds if struggle_idx else None,
            ))

        # Generate overall summary
        summary = await self._generate_session_summary(timeline)

        return QuickInsightsResponse(
            session_id=session_id,
            insights=insights,
            summary=summary,
        )

    async def _generate_session_summary(self, timeline: Timeline) -> str:
        """Generate a brief AI summary of the session."""
        try:
            prompt = f"""Summarize this coding session in 2-3 sentences for a recruiter.

Task: {timeline.task_title}
Duration: {timeline.duration_seconds // 60} minutes
Runs: {timeline.total_runs}
Errors: {timeline.errors_encountered}
AI Interventions: {timeline.interventions_received}
Result: {timeline.final_result or 'incomplete'}

Focus on: problem-solving approach, debugging behavior, and overall performance."""

            return await self.backboard._call_gemini(
                prompt=prompt,
                temperature=0.5,
                max_tokens=150,
            )
        except Exception:
            result = timeline.final_result or "incomplete"
            return f"Session lasted {timeline.duration_seconds // 60} minutes with {timeline.total_runs} code runs and {timeline.errors_encountered} errors. Final result: {result}."
