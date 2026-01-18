import numpy as np
from datetime import datetime
from typing import Optional
from db.collections import Collections
from services.amplitude import update_amplitude_user_properties, get_passport_analytics, get_amplitude_ai_profile
from services.backboard import BackboardService


def compute_job_fit(user_vector: list[float], job_vector: list[float]) -> float:
    """Compute cosine similarity between user and job vectors."""
    if not user_vector or not job_vector:
        return 0.0

    # Pad vectors to same length
    max_len = max(len(user_vector), len(job_vector))
    u = np.array(user_vector + [0.0] * (max_len - len(user_vector)))
    j = np.array(job_vector + [0.0] * (max_len - len(job_vector)))

    # Cosine similarity
    dot = np.dot(u, j)
    norm_u = np.linalg.norm(u)
    norm_j = np.linalg.norm(j)

    if norm_u == 0 or norm_j == 0:
        return 0.0

    return float(dot / (norm_u * norm_j))


async def extract_session_features(user_id: str, session_id: str) -> dict:
    """Extract features from a session's events."""
    cursor = Collections.events().find({
        "user_id": user_id,
        "session_id": session_id,
    }).sort("timestamp", 1)

    events = await cursor.to_list(length=1000)

    if not events:
        return {}

    # Feature extraction - includes AI assistance tracking
    features = {
        "total_events": len(events),
        "run_attempts": 0,
        "test_cases_ran": 0,
        "errors_encountered": 0,
        "fixes_applied": 0,
        "commands_used": set(),
        "code_changes": 0,
        "paste_bursts": 0,
        "time_between_runs": [],
        "time_to_first_run": None,
        "shortcut_usage_ratio": 0,
        # AI assistance metrics
        "hints_requested": 0,
        "hints_acknowledged": 0,
        "chat_help_requests": 0,
        # Integrity metrics
        "violations": 0,
        "tab_switches": 0,
    }

    first_event_time = events[0]["timestamp"] if events else None
    last_run_time = None
    total_commands = 0
    shortcut_commands = 0

    for event in events:
        event_type = event["event_type"]
        props = event.get("properties", {})

        if event_type in ("run_attempted", "test_cases_ran"):
            features["run_attempts"] += 1
            features["test_cases_ran"] += 1
            if features["time_to_first_run"] is None and first_event_time:
                features["time_to_first_run"] = (
                    event["timestamp"] - first_event_time
                ).total_seconds()
            if last_run_time:
                features["time_between_runs"].append(
                    (event["timestamp"] - last_run_time).total_seconds()
                )
            last_run_time = event["timestamp"]

        elif event_type == "error_emitted":
            features["errors_encountered"] += 1

        elif event_type == "fix_applied":
            features["fixes_applied"] += 1

        elif event_type == "editor_command":
            features["commands_used"].add(props.get("command", ""))
            total_commands += 1
            if props.get("source") == "shortcut":
                shortcut_commands += 1

        elif event_type == "code_changed":
            features["code_changes"] += 1

        elif event_type == "paste_burst_detected":
            features["paste_bursts"] += 1

        # AI assistance events
        elif event_type == "contextual_hint_shown":
            features["hints_requested"] += 1

        elif event_type == "hint_acknowledged":
            features["hints_acknowledged"] += 1

        elif event_type == "chat_help_requested":
            features["chat_help_requests"] += 1

        # Integrity events
        elif event_type == "proctoring_violation":
            features["violations"] += 1

        elif event_type == "tab_switch":
            features["tab_switches"] += 1

    # Compute derived metrics
    features["commands_used"] = list(features["commands_used"])
    if total_commands > 0:
        features["shortcut_usage_ratio"] = shortcut_commands / total_commands
    if features["time_between_runs"]:
        features["avg_time_between_runs"] = np.mean(features["time_between_runs"])

    return features


async def compute_skill_vector(user_id: str) -> list[float]:
    """
    Compute aggregate skill vector from all user sessions.
    
    The 5 passport qualities are computed FROM tracked events:
    - iteration_velocity: How quickly they iterate (test runs, code changes)
    - debug_efficiency: How effectively they fix errors (fixes per error)
    - craftsmanship: Code quality (fewer errors, less AI reliance)
    - tool_fluency: Editor proficiency (shortcuts, commands)
    - integrity: Honest work (no violations, minimal paste bursts)
    """
    # Get all sessions
    cursor = Collections.sessions().find({
        "user_id": user_id,
        "submitted": True,
    })
    sessions = await cursor.to_list(length=100)

    if not sessions:
        return []

    # Aggregate features across sessions
    all_features = []
    for session in sessions:
        features = await extract_session_features(user_id, session["session_id"])
        if features:
            all_features.append(features)

    if not all_features:
        return []

    # Aggregate all metrics
    total_runs = sum(f.get("run_attempts", 0) for f in all_features)
    total_test_runs = sum(f.get("test_cases_ran", 0) for f in all_features)
    total_errors = sum(f.get("errors_encountered", 0) for f in all_features)
    total_fixes = sum(f.get("fixes_applied", 0) for f in all_features)
    total_code_changes = sum(f.get("code_changes", 0) for f in all_features)
    total_paste_bursts = sum(f.get("paste_bursts", 0) for f in all_features)
    total_violations = sum(f.get("violations", 0) for f in all_features)
    total_tab_switches = sum(f.get("tab_switches", 0) for f in all_features)
    
    # AI assistance totals
    total_hints = sum(f.get("hints_requested", 0) for f in all_features)
    total_chat_help = sum(f.get("chat_help_requests", 0) for f in all_features)
    total_ai_assists = total_hints + total_chat_help
    
    # Shortcut usage
    avg_shortcuts = np.mean([f.get("shortcut_usage_ratio", 0) for f in all_features])
    
    num_sessions = len(all_features)
    
    # ============================================
    # COMPUTE THE 5 PASSPORT QUALITIES FROM EVENTS
    # ============================================
    
    # 1. ITERATION_VELOCITY: How quickly they iterate
    #    Based on: test runs per session, code changes
    #    More runs + changes = faster iteration
    runs_per_session = total_runs / num_sessions
    changes_per_session = total_code_changes / num_sessions
    iteration_velocity = min(1.0, (runs_per_session / 15.0) * 0.6 + (changes_per_session / 50.0) * 0.4)
    
    # 2. DEBUG_EFFICIENCY: How effectively they fix errors
    #    Based on: fixes applied vs errors encountered
    #    Higher fix rate = better debugging
    if total_errors > 0:
        fix_rate = total_fixes / total_errors
        debug_efficiency = min(1.0, fix_rate)
    else:
        debug_efficiency = 1.0  # No errors = perfect
    
    # 3. CRAFTSMANSHIP: Code quality and independence
    #    Based on: fewer errors, less AI reliance, good fix rate
    #    Penalize heavy AI usage (shows less independent problem-solving)
    error_penalty = min(1.0, total_errors / (num_sessions * 10))  # Errors per session
    ai_reliance = total_ai_assists / max(total_runs + total_code_changes, 1)
    ai_penalty = min(0.3, ai_reliance * 0.5)  # Cap AI penalty at 30%
    craftsmanship = max(0.0, 1.0 - error_penalty * 0.5 - ai_penalty)
    
    # 4. TOOL_FLUENCY: Editor proficiency
    #    Based on: keyboard shortcuts, editor commands
    tool_fluency = avg_shortcuts
    
    # 5. INTEGRITY: Honest, focused work
    #    Based on: violations, paste bursts, tab switches
    #    Penalize suspicious behavior
    violation_penalty = total_violations * 0.15  # -15% per violation
    paste_penalty = min(0.3, total_paste_bursts / (num_sessions * 3) * 0.3)
    tab_penalty = min(0.2, total_tab_switches / (num_sessions * 20) * 0.2)
    integrity = max(0.0, 1.0 - violation_penalty - paste_penalty - tab_penalty)

    return [
        round(iteration_velocity, 3),
        round(debug_efficiency, 3),
        round(craftsmanship, 3),
        round(tool_fluency, 3),
        round(integrity, 3),
    ]


async def get_metrics_breakdown(user_id: str) -> dict:
    """
    Get a detailed breakdown of how each passport metric was calculated.
    Useful for showing users what factors influenced their scores.
    """
    cursor = Collections.sessions().find({
        "user_id": user_id,
        "submitted": True,
    })
    sessions = await cursor.to_list(length=100)

    if not sessions:
        return {"error": "No sessions found"}

    all_features = []
    for session in sessions:
        features = await extract_session_features(user_id, session["session_id"])
        if features:
            all_features.append(features)

    if not all_features:
        return {"error": "No features extracted"}

    num_sessions = len(all_features)
    
    # Aggregate totals
    totals = {
        "sessions": num_sessions,
        "test_runs": sum(f.get("test_cases_ran", 0) for f in all_features),
        "code_changes": sum(f.get("code_changes", 0) for f in all_features),
        "errors": sum(f.get("errors_encountered", 0) for f in all_features),
        "fixes": sum(f.get("fixes_applied", 0) for f in all_features),
        "hints_requested": sum(f.get("hints_requested", 0) for f in all_features),
        "chat_help_requests": sum(f.get("chat_help_requests", 0) for f in all_features),
        "violations": sum(f.get("violations", 0) for f in all_features),
        "paste_bursts": sum(f.get("paste_bursts", 0) for f in all_features),
        "tab_switches": sum(f.get("tab_switches", 0) for f in all_features),
    }
    
    return {
        "totals": totals,
        "metrics_explanation": {
            "iteration_velocity": {
                "description": "How quickly you iterate on code",
                "factors": ["test_runs", "code_changes"],
                "calculation": f"{totals['test_runs']} test runs + {totals['code_changes']} code changes across {num_sessions} sessions",
            },
            "debug_efficiency": {
                "description": "How effectively you fix errors",
                "factors": ["errors", "fixes"],
                "calculation": f"{totals['fixes']} fixes / {totals['errors']} errors = {totals['fixes']/max(totals['errors'],1):.0%} fix rate",
            },
            "craftsmanship": {
                "description": "Code quality and independent problem-solving",
                "factors": ["errors", "hints_requested", "chat_help_requests"],
                "calculation": f"Based on {totals['errors']} errors, {totals['hints_requested']} hints, {totals['chat_help_requests']} chat requests",
            },
            "tool_fluency": {
                "description": "Editor proficiency via shortcuts",
                "factors": ["shortcut_usage"],
                "calculation": "Percentage of commands executed via keyboard shortcuts",
            },
            "integrity": {
                "description": "Honest, focused work",
                "factors": ["violations", "paste_bursts", "tab_switches"],
                "calculation": f"{totals['violations']} violations, {totals['paste_bursts']} paste bursts, {totals['tab_switches']} tab switches",
            },
        },
    }


async def assign_archetype(skill_vector: list[float], user_id: str = None) -> tuple[str, float]:
    """
    Assign archetype using a multi-AI hybrid approach:
    
    AI Models Used:
    1. Amplitude AI (primary if available): ML-computed cohorts & behavioral signals
    2. Backboard GPT-4/ChatGPT (secondary): AI-driven behavioral analysis
    3. Mathematical fallback: Skill vector + local analytics
    
    Weighting Strategy:
    - Base mathematical scores: 30%
    - Local analytics adjustments: 20%
    - Amplitude AI insights: 25% (when available)
    - Backboard GPT-4 insights: 25% (when available)
    
    If no AI data is available, mathematical + local analytics are weighted higher.
    """
    if not skill_vector or len(skill_vector) < 5:
        return None, 0.0

    iteration_velocity = skill_vector[0]
    debug_efficiency = skill_vector[1]
    craftsmanship = skill_vector[2]
    tool_fluency = skill_vector[3]
    integrity = skill_vector[4]

    # Base scores from skill vector (weight: 40%)
    base_scores = {
        "fast_iterator": iteration_velocity * 0.5 + tool_fluency * 0.3 + debug_efficiency * 0.2,
        "careful_tester": craftsmanship * 0.4 + debug_efficiency * 0.4 + integrity * 0.2,
        "debugger": debug_efficiency * 0.5 + iteration_velocity * 0.3 + tool_fluency * 0.2,
        "craftsman": craftsmanship * 0.5 + integrity * 0.3 + debug_efficiency * 0.2,
        "explorer": iteration_velocity * 0.4 + debug_efficiency * 0.3 + craftsmanship * 0.3,
    }

    # Local analytics adjustments (weight: 30%)
    local_adjustments = {
        "fast_iterator": 0.0,
        "careful_tester": 0.0,
        "debugger": 0.0,
        "craftsman": 0.0,
        "explorer": 0.0,
    }
    
    # Amplitude AI adjustments from ML-computed insights (weight: 30%)
    ai_adjustments = {
        "fast_iterator": 0.0,
        "careful_tester": 0.0,
        "debugger": 0.0,
        "craftsman": 0.0,
        "explorer": 0.0,
    }

    if user_id:
        # Fetch both local analytics and Amplitude AI profile in parallel
        try:
            import asyncio
            analytics_task = get_passport_analytics(user_id)
            ai_profile_task = get_amplitude_ai_profile(user_id)
            
            analytics, ai_profile = await asyncio.gather(
                analytics_task, 
                ai_profile_task,
                return_exceptions=True
            )
            
            # Process local analytics
            if isinstance(analytics, dict) and "error" not in analytics:
                session_stats = analytics.get("session_stats", {})
                activity = analytics.get("activity_metrics", {})
                ai_metrics = analytics.get("ai_assistance_metrics", {})
                learning = analytics.get("learning_metrics", {})
                integrity_data = analytics.get("integrity_metrics", {})
                
                pass_rate = session_stats.get("pass_rate", 0)
                avg_score = session_stats.get("average_score", 0) / 100
                runs_per_submission = activity.get("runs_per_submission", 0)
                ai_reliance = ai_metrics.get("ai_reliance_score", 0)
                fix_efficiency = learning.get("fix_efficiency", 0)
                integrity_score = integrity_data.get("integrity_score", 1.0)
                
                # Fast Iterator signals
                if runs_per_submission > 5:
                    local_adjustments["fast_iterator"] += 0.15
                if runs_per_submission > 10:
                    local_adjustments["fast_iterator"] += 0.10
                if ai_reliance < 0.1:
                    local_adjustments["fast_iterator"] += 0.05
                
                # Careful Tester signals
                if pass_rate > 0.8:
                    local_adjustments["careful_tester"] += 0.15
                if avg_score > 0.85:
                    local_adjustments["careful_tester"] += 0.10
                if integrity_score > 0.95:
                    local_adjustments["careful_tester"] += 0.05
                
                # Debugger signalsok
                errors = learning.get("errors_encountered", 0)
                if fix_efficiency > 0.7 and errors > 5:
                    local_adjustments["debugger"] += 0.20
                elif fix_efficiency > 0.5:
                    local_adjustments["debugger"] += 0.10
                
                # Craftsman signals
                if ai_reliance < 0.05 and integrity_score > 0.9:
                    local_adjustments["craftsman"] += 0.15
                if avg_score > 0.9 and pass_rate > 0.7:
                    local_adjustments["craftsman"] += 0.10
                
                # Explorer signals
                hints_requested = ai_metrics.get("hints_requested", 0)
                hints_acked = ai_metrics.get("hints_acknowledged", 0)
                if hints_requested > 0 and hints_acked / max(hints_requested, 1) > 0.5:
                    local_adjustments["explorer"] += 0.10
                if 3 < runs_per_submission < 8:
                    local_adjustments["explorer"] += 0.10
                    
                print(f"[SkillGraph] Local analytics adjustments: {local_adjustments}")
            
            # Process Amplitude AI profile (ML-computed insights)
            if isinstance(ai_profile, dict) and ai_profile.get("has_ai_data"):
                print(f"[SkillGraph] ✓ Received Amplitude AI data for {user_id[:8]}...")
                
                # Get cohort-based archetype hints (from Amplitude's ML segmentation)
                archetype_hints = ai_profile.get("archetype_hints", {})
                for archetype, boost in archetype_hints.items():
                    if archetype in ai_adjustments:
                        ai_adjustments[archetype] += boost
                
                # Get behavioral signals from Amplitude's computations
                signals = ai_profile.get("behavioral_signals", {})
                
                # Engagement score affects Fast Iterator & Explorer
                engagement = signals.get("engagement_score")
                if engagement is not None:
                    if engagement > 0.8:
                        ai_adjustments["fast_iterator"] += 0.15
                        ai_adjustments["explorer"] += 0.10
                    elif engagement > 0.5:
                        ai_adjustments["explorer"] += 0.15
                
                # Power user score affects Fast Iterator & Craftsman
                power_user = signals.get("power_user_score")
                if power_user is not None:
                    if power_user > 0.7:
                        ai_adjustments["fast_iterator"] += 0.10
                        ai_adjustments["craftsman"] += 0.10
                
                # Churn risk inversely affects Careful Tester
                churn_risk = signals.get("churn_risk")
                if churn_risk is not None:
                    if churn_risk < 0.2:  # Low churn = high engagement
                        ai_adjustments["careful_tester"] += 0.10
                        ai_adjustments["craftsman"] += 0.05
                
                # User segment from Amplitude's ML
                user_segment = signals.get("user_segment")
                if user_segment:
                    segment_lower = str(user_segment).lower()
                    if "power" in segment_lower or "advanced" in segment_lower:
                        ai_adjustments["craftsman"] += 0.15
                    elif "beginner" in segment_lower or "new" in segment_lower:
                        ai_adjustments["explorer"] += 0.15
                    elif "consistent" in segment_lower or "regular" in segment_lower:
                        ai_adjustments["careful_tester"] += 0.10
                
                # Skill level from Amplitude's computations
                skill_level = signals.get("skill_level")
                if skill_level:
                    level_lower = str(skill_level).lower()
                    if "expert" in level_lower or "advanced" in level_lower:
                        ai_adjustments["craftsman"] += 0.20
                        ai_adjustments["debugger"] += 0.10
                    elif "intermediate" in level_lower:
                        ai_adjustments["careful_tester"] += 0.10
                
                # Cohort count as a proxy for behavioral diversity
                cohort_count = ai_profile.get("cohort_count", 0)
                if cohort_count > 5:
                    ai_adjustments["explorer"] += 0.10  # In many cohorts = diverse behavior
                
                print(f"[SkillGraph] Amplitude AI adjustments: {ai_adjustments}")
            else:
                print(f"[SkillGraph] No Amplitude AI data available, using local analytics only")
                
        except Exception as e:
            print(f"[SkillGraph] Failed to fetch analytics: {e}, using base scores only")

    # =========================================================================
    # BACKBOARD GPT-4 AI - Secondary/Backup AI for archetype assignment
    # =========================================================================
    backboard_adjustments = {
        "fast_iterator": 0.0,
        "careful_tester": 0.0,
        "debugger": 0.0,
        "craftsman": 0.0,
        "explorer": 0.0,
    }
    has_backboard_ai = False
    
    if user_id:
        try:
            # Prepare behavioral history for GPT-4 analysis
            behavioral_history = {
                "session_stats": {},
                "activity_metrics": {},
                "ai_assistance_metrics": {},
                "learning_metrics": {},
                "integrity_metrics": {},
            }
            
            # Get analytics data if available
            analytics = await get_passport_analytics(user_id)
            if isinstance(analytics, dict) and "error" not in analytics:
                behavioral_history = {
                    "session_stats": analytics.get("session_stats", {}),
                    "activity_metrics": analytics.get("activity_metrics", {}),
                    "ai_assistance_metrics": analytics.get("ai_assistance_metrics", {}),
                    "learning_metrics": analytics.get("learning_metrics", {}),
                    "integrity_metrics": analytics.get("integrity_metrics", {}),
                }
            
            # Call Backboard GPT-4 for AI-driven archetype assignment
            backboard_service = BackboardService(user_id=user_id)
            gpt4_result = await backboard_service.ai_assign_archetype(
                skill_vector=skill_vector,
                behavioral_history=behavioral_history,
                analytics_summary={
                    "skill_vector_summary": {
                        "iteration_velocity": iteration_velocity,
                        "debug_efficiency": debug_efficiency,
                        "craftsmanship": craftsmanship,
                        "tool_fluency": tool_fluency,
                        "integrity": integrity,
                    },
                    "amplitude_ai_available": any(v > 0 for v in ai_adjustments.values()),
                },
            )
            
            if gpt4_result.get("ai_source") == "backboard":
                has_backboard_ai = True
                
                # Use the adjustments from GPT-4
                for archetype, score in gpt4_result.get("adjustments", {}).items():
                    if archetype in backboard_adjustments:
                        backboard_adjustments[archetype] = score
                
                print(f"[SkillGraph] ✓ Backboard GPT-4 AI assigned: {gpt4_result.get('archetype')} "
                      f"(confidence: {gpt4_result.get('confidence', 0):.2f})")
                print(f"[SkillGraph] Backboard AI adjustments: {backboard_adjustments}")
            else:
                print(f"[SkillGraph] Backboard AI fallback used (no GPT-4 response)")
                
        except Exception as e:
            print(f"[SkillGraph] Backboard GPT-4 AI failed: {e}")

    # =========================================================================
    # COMBINE ALL AI SIGNALS WITH DYNAMIC WEIGHTING
    # =========================================================================
    
    # Determine which AI sources are available
    has_amplitude_ai = any(v > 0 for v in ai_adjustments.values())
    has_local_analytics = any(v > 0 for v in local_adjustments.values())
    
    # Dynamic weighting based on available AI sources:
    # - Both AIs available: math=25%, local=15%, amplitude=30%, backboard=30%
    # - Only Amplitude AI: math=30%, local=25%, amplitude=45%
    # - Only Backboard AI: math=30%, local=25%, backboard=45%
    # - No AI: math=50%, local=50%
    
    if has_amplitude_ai and has_backboard_ai:
        weights = {"base": 0.25, "local": 0.15, "amplitude": 0.30, "backboard": 0.30}
        print(f"[SkillGraph] Using FULL AI mode (Amplitude + Backboard GPT-4)")
    elif has_amplitude_ai:
        weights = {"base": 0.30, "local": 0.25, "amplitude": 0.45, "backboard": 0.0}
        print(f"[SkillGraph] Using Amplitude AI mode only")
    elif has_backboard_ai:
        weights = {"base": 0.30, "local": 0.25, "amplitude": 0.0, "backboard": 0.45}
        print(f"[SkillGraph] Using Backboard GPT-4 AI mode only")
    else:
        weights = {"base": 0.50, "local": 0.50, "amplitude": 0.0, "backboard": 0.0}
        print(f"[SkillGraph] Using MATHEMATICAL mode (no AI available)")

    final_scores = {}
    for archetype in base_scores:
        base = base_scores[archetype]
        local = local_adjustments[archetype]
        amplitude = ai_adjustments[archetype]
        backboard = backboard_adjustments[archetype]
        
        final_scores[archetype] = (
            base * weights["base"] +
            local * weights["local"] +
            amplitude * weights["amplitude"] +
            backboard * weights["backboard"]
        )
        
        # Synergy bonus when multiple AI sources agree
        if has_amplitude_ai and has_backboard_ai:
            if amplitude > 0.1 and backboard > 0.1:
                final_scores[archetype] += 0.05  # Agreement bonus

    best_archetype = max(final_scores, key=final_scores.get)
    confidence = min(final_scores[best_archetype], 1.0)  # Cap at 1.0
    
    # Log the AI sources used
    ai_sources_used = []
    if has_amplitude_ai:
        ai_sources_used.append("Amplitude ML")
    if has_backboard_ai:
        ai_sources_used.append("Backboard GPT-4")
    if not ai_sources_used:
        ai_sources_used.append("Mathematical only")
    
    print(f"[SkillGraph] ========================================")
    print(f"[SkillGraph] FINAL ARCHETYPE: {best_archetype.upper()}")
    print(f"[SkillGraph] Confidence: {confidence:.3f}")
    print(f"[SkillGraph] AI Sources: {', '.join(ai_sources_used)}")
    print(f"[SkillGraph] All scores: {final_scores}")
    print(f"[SkillGraph] ========================================")

    return best_archetype, round(confidence, 3)


async def update_passport_after_submit(
    user_id: str,
    session_id: str,
    task_id: str,
    passed: bool,
    score: int,
):
    """Update user's passport after task submission."""
    # Extract session features
    features = await extract_session_features(user_id, session_id)

    # Compute new skill vector
    skill_vector = await compute_skill_vector(user_id)

    # Assign archetype (uses Amplitude analytics for smarter assignment)
    archetype, confidence = await assign_archetype(skill_vector, user_id)

    # Build metrics
    metrics = {
        "iteration_velocity": skill_vector[0] if len(skill_vector) > 0 else 0.0,
        "debug_efficiency": skill_vector[1] if len(skill_vector) > 1 else 0.0,
        "craftsmanship": skill_vector[2] if len(skill_vector) > 2 else 0.0,
        "tool_fluency": skill_vector[3] if len(skill_vector) > 3 else 0.0,
        "integrity": skill_vector[4] if len(skill_vector) > 4 else 1.0,
    }

    # Create notable moment if high score
    notable_session = None
    if passed and score >= 90:
        notable_session = {
            "session_id": session_id,
            "task_id": task_id,
            "highlight": f"Scored {score}% on {task_id}",
            "timestamp": datetime.utcnow(),
            "type": "achievement",
        }

    # Update passport
    update_doc = {
        "$set": {
            "skill_vector": skill_vector,
            "archetype": archetype,
            "archetype_confidence": confidence,
            "metrics": metrics,
            "updated_at": datetime.utcnow(),
        }
    }

    if notable_session:
        update_doc["$push"] = {"notable_sessions": notable_session}

    await Collections.passports().update_one(
        {"user_id": user_id},
        update_doc,
    )

    # Update user document too
    await Collections.users().update_one(
        {"_id": user_id},
        {
            "$set": {
                "skill_vector": skill_vector,
                "archetype": archetype,
                "integrity_score": metrics["integrity"],
            }
        },
    )

    # Update Amplitude user properties
    await update_amplitude_user_properties(
        user_id=user_id,
        properties={
            "skill_archetype": archetype,
            "skill_vector": skill_vector,
            "integrity_score": metrics["integrity"],
        },
    )


async def update_skill_proficiencies_after_submit(
    user_id: str,
    task_id: str,
    passed: bool,
    score: int,
):
    """Update user's skill proficiencies after task submission."""
    # Get task details to extract skills
    task = await Collections.tasks().find_one({"task_id": task_id})
    if not task:
        return

    # Get skills from task tags and category
    skills = []
    if task.get("tags"):
        skills.extend(task["tags"])
    if task.get("category"):
        skills.append(task["category"])

    if not skills:
        return

    # Get or create skill proficiencies document
    prof_doc = await Collections.skill_proficiencies().find_one({"user_id": user_id})
    proficiencies = prof_doc.get("proficiencies", {}) if prof_doc else {}

    # Update each skill's proficiency
    for skill in skills:
        skill_key = skill.lower().replace(" ", "_")

        if skill_key not in proficiencies:
            proficiencies[skill_key] = {
                "name": skill,
                "score": 0.0,
                "tasks_completed": 0,
                "total_score": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

        prof = proficiencies[skill_key]
        prof["tasks_completed"] += 1
        prof["total_score"] += score
        prof["score"] = prof["total_score"] / prof["tasks_completed"] / 100.0  # Normalize to 0-1
        prof["last_updated"] = datetime.utcnow().isoformat()

    # Upsert skill proficiencies document
    await Collections.skill_proficiencies().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "proficiencies": proficiencies,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "user_id": user_id,
            },
        },
        upsert=True,
    )
