"""
Backboard.io Multi-Model AI Service + Direct Gemini API

Model routing:
- Claude for empathetic hints (via Backboard - anthropic/claude-3-haiku)
- GPT-4o for code analysis (via Backboard - openai/gpt-4o-mini)
- Gemini for profile summaries & chat (DIRECT Gemini API - gemini-2.0-flash)
- Cohere for job parsing (via Backboard - cohere/command-r)
"""

import httpx
import json
from typing import Optional
from config import get_settings

BACKBOARD_BASE_URL = "https://api.backboard.io/v1"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class BackboardService:
    """
    Multi-model AI service using Backboard.io for adaptive memory
    and intelligent model switching.
    """

    def __init__(self, user_id: str):
        settings = get_settings()
        self.api_key = settings.backboard_api_key
        self.gemini_api_key = settings.gemini_api_key
        self.user_id = user_id
        # In-memory conversation history for Gemini (keyed by session)
        self._gemini_history: dict[str, list] = {}

    async def _call_model(
        self,
        model: str,
        messages: list,
        memory_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generic model call with optional memory.
        Memory is keyed per-user to enable personalization.
        """
        if not self.api_key:
            return self._fallback_response(messages)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                # Enable Backboard memory for personalization
                if memory_key:
                    payload["memory"] = {
                        "enabled": True,
                        "key": f"{self.user_id}:{memory_key}",
                    }

                response = await client.post(
                    f"{BACKBOARD_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Backboard API error: {e}")
            return self._fallback_response(messages)

    def _fallback_response(self, messages: list) -> str:
        """Provide a fallback response when API is unavailable."""
        # Simple fallback hints
        fallback_hints = [
            "Try breaking down the problem into smaller steps.",
            "Check your variable names and make sure they match what you defined.",
            "Consider adding some print statements to debug your logic.",
            "Review the expected input and output format.",
            "Take a moment to re-read the problem statement.",
        ]
        import random
        return random.choice(fallback_hints)

    # =========================================================================
    # GEMINI API - Direct calls (NOT through Backboard)
    # =========================================================================

    async def _call_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        session_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Direct call to Gemini API (gemini-2.0-flash).
        Supports conversation history via session_key.
        """
        if not self.gemini_api_key:
            return self._fallback_response([{"content": prompt}])

        try:
            # Build contents with history if session_key provided
            contents = []
            
            if session_key and session_key in self._gemini_history:
                contents.extend(self._gemini_history[session_key])
            
            # Add current user message
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }

            # Add system instruction if provided
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{GEMINI_API_URL}/gemini-2.0-flash:generateContent?key={self.gemini_api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                
                result = response.json()
                response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Store conversation history if session_key provided
                if session_key:
                    if session_key not in self._gemini_history:
                        self._gemini_history[session_key] = []
                    
                    # Add user message and response to history
                    self._gemini_history[session_key].append({
                        "role": "user",
                        "parts": [{"text": prompt}]
                    })
                    self._gemini_history[session_key].append({
                        "role": "model",
                        "parts": [{"text": response_text}]
                    })
                    
                    # Keep history limited to last 20 exchanges
                    if len(self._gemini_history[session_key]) > 40:
                        self._gemini_history[session_key] = self._gemini_history[session_key][-40:]
                
                return response_text

        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_response([{"content": prompt}])

    def clear_gemini_history(self, session_key: str):
        """Clear Gemini conversation history for a session."""
        if session_key in self._gemini_history:
            del self._gemini_history[session_key]

    # =========================================================================
    # HINT GENERATION - Claude (empathetic, pedagogical)
    # =========================================================================

    async def generate_hint(self, code: str, error: str, attempt_count: int) -> str:
        """
        Use Claude for empathetic, pedagogical hints.
        Memory: Remembers past hints to avoid repetition.
        """
        return await self._call_model(
            model="anthropic/claude-3-haiku-20240307",
            messages=[
                {
                    "role": "system",
                    "content": """You are an encouraging coding mentor helping a student who is stuck.

Rules:
- Give a brief, helpful hint (1-2 sentences max)
- Don't give away the answer
- Be encouraging and supportive
- If you've given similar hints before (check your memory), try a different approach
- Acknowledge their effort if they've been trying for a while""",
                },
                {
                    "role": "user",
                    "content": f"""The student's current code:
```
{code[:1500]}
```

Error/Issue: {error}

This is attempt #{attempt_count}. Please provide a helpful hint.""",
                },
            ],
            memory_key="hints",
            temperature=0.8,
            max_tokens=150,
        )

    async def generate_encouragement(self, context: str) -> str:
        """Generate pure encouragement when user seems frustrated."""
        return await self._call_model(
            model="anthropic/claude-3-haiku-20240307",
            messages=[
                {
                    "role": "system",
                    "content": "You are a supportive coding mentor. Give a brief (1 sentence) word of encouragement. Be genuine, not cheesy.",
                },
                {"role": "user", "content": f"Context: {context}"},
            ],
            temperature=0.9,
            max_tokens=50,
        )

    # =========================================================================
    # CODE ANALYSIS - GPT-4o (strong code understanding)
    # =========================================================================

    async def analyze_code_error(self, code: str, error: str) -> dict:
        """
        Use GPT-4o for detailed technical code analysis.
        Returns structured analysis of the error.
        """
        response = await self._call_model(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Analyze the code error. Return valid JSON only with this structure:
{
  "error_type": "syntax|runtime|logic|type",
  "root_cause": "brief explanation",
  "affected_lines": "line numbers or description",
  "severity": 1-5,
  "category": "null_reference|off_by_one|type_mismatch|syntax|other"
}""",
                },
                {
                    "role": "user",
                    "content": f"Code:\n```\n{code[:2000]}\n```\n\nError: {error}",
                },
            ],
            temperature=0.3,
            max_tokens=200,
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error_type": "unknown", "root_cause": response, "severity": 3}

    async def suggest_fix(self, code: str, error: str) -> str:
        """
        Use GPT-4o to suggest a specific fix without giving full solution.
        """
        return await self._call_model(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Suggest a specific fix for this code issue. Be concise (2-3 sentences). Point to the exact location and what needs to change, but don't write the full corrected code.",
                },
                {
                    "role": "user",
                    "content": f"```\n{code[:2000]}\n```\n\nError: {error}",
                },
            ],
            temperature=0.5,
            max_tokens=150,
        )

    # =========================================================================
    # PROFILE SUMMARIZATION - Gemini DIRECT API (structured analysis)
    # =========================================================================

    async def summarize_radar_profile(self, radar: dict, recent_events: list) -> str:
        """
        Use Gemini (direct API) for structured profile summarization.
        Uses session key for memory of profile evolution.
        """
        prompt = f"""Summarize this developer's coding style based on their radar profile and recent behavior.

Radar Profile (scores 0-1):
{json.dumps(radar, indent=2)}

Recent Events (last 10):
{json.dumps(recent_events[-10:] if recent_events else [], indent=2, default=str)}

Provide:
1. Their strongest trait (1 sentence)
2. Area for growth (1 sentence)
3. How their style compares to their previous sessions (if you remember them)

Keep it concise and actionable."""

        return await self._call_gemini(
            prompt=prompt,
            session_key=f"{self.user_id}:profile_history",
            temperature=0.6,
            max_tokens=200,
        )

    async def generate_archetype_description(self, archetype: str, radar: dict) -> str:
        """Generate personalized archetype description based on actual scores. Uses direct Gemini API."""
        prompt = f"""The developer has been classified as: "{archetype}"

Their radar scores: {json.dumps(radar, indent=2)}

Write a 2-sentence personalized description of their engineering style that reflects their actual scores. Be specific, not generic."""

        return await self._call_gemini(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100,
        )

    # =========================================================================
    # JOB PARSING - Cohere Command (efficient extraction)
    # =========================================================================

    async def parse_job_requirements(self, job_description: str) -> dict:
        """
        Use Cohere Command for efficient job description parsing.
        Extracts ideal candidate radar profile from text.
        """
        response = await self._call_model(
            model="cohere/command-r",
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract the ideal candidate profile from this job description.

Job Description:
{job_description[:2000]}

Return valid JSON with scores 0.0-1.0 for each dimension:
{{
  "verification": 0.X,    // Testing mindset importance
  "velocity": 0.X,        // Speed of delivery importance
  "optimization": 0.X,    // Algorithmic efficiency importance
  "decomposition": 0.X,   // Code modularity importance
  "debugging": 0.X        // Error resolution importance
}}

Base scores on explicit and implicit requirements in the description.""",
                }
            ],
            temperature=0.3,
            max_tokens=150,
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "verification": 0.5,
                "velocity": 0.5,
                "optimization": 0.5,
                "decomposition": 0.5,
                "debugging": 0.5,
            }

    async def explain_job_match(
        self, candidate_radar: dict, job_radar: dict, fit_score: float
    ) -> str:
        """Explain why a candidate matches (or doesn't match) a job."""
        return await self._call_model(
            model="cohere/command-r",
            messages=[
                {
                    "role": "user",
                    "content": f"""Candidate radar: {json.dumps(candidate_radar)}
Job requirements: {json.dumps(job_radar)}
Match score: {fit_score:.0%}

Explain in 1-2 sentences why this candidate does/doesn't match this role. Be specific about which dimensions align or differ.""",
                }
            ],
            temperature=0.5,
            max_tokens=100,
        )

    # =========================================================================
    # ADAPTIVE INTERVENTION - Intelligent model routing
    # =========================================================================

    async def adaptive_intervention(self, session_context: dict) -> dict:
        """
        Intelligently choose intervention type and model based on context.
        This is the "adaptive" part that makes decisions based on user state.
        """
        code = session_context.get("code", "")
        last_error = session_context.get("last_error")
        error_streak = session_context.get("error_streak", 0)
        time_stuck_ms = session_context.get("time_stuck_ms", 0)
        attempt_count = session_context.get("attempt_count", 1)

        # Decision tree for intervention type
        if error_streak >= 3 and last_error:
            # Technical stuck - use GPT for analysis + Claude for delivery
            analysis = await self.analyze_code_error(code, last_error)
            hint = await self.generate_hint(code, last_error, attempt_count)

            return {
                "type": "technical_hint",
                "analysis": analysis,
                "hint": hint,
                "model_used": ["gpt-4o-mini", "claude-3-haiku"],
            }

        elif time_stuck_ms > 180000:  # 3+ minutes without progress
            # Might need encouragement or different approach
            hint = await self.generate_hint(
                code,
                "User seems stuck (no progress for 3 minutes)",
                attempt_count,
            )
            encouragement = await self.generate_encouragement(
                f"User has been working for {time_stuck_ms // 60000} minutes"
            )

            return {
                "type": "encouragement",
                "hint": hint,
                "encouragement": encouragement,
                "model_used": ["claude-3-haiku"],
            }

        elif error_streak >= 2:
            # Early intervention - quick hint
            hint = await self.generate_hint(
                code, last_error or "struggling", attempt_count
            )

            return {
                "type": "gentle_nudge",
                "hint": hint,
                "model_used": ["claude-3-haiku"],
            }

        return {"type": "none"}

    # =========================================================================
    # MEMORY MANAGEMENT
    # =========================================================================

    async def get_user_memory(self, memory_key: str) -> dict:
        """Fetch user's adaptive memory from Backboard."""
        if not self.api_key:
            return {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BACKBOARD_BASE_URL}/memory/{self.user_id}:{memory_key}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if response.status_code == 200:
                    return response.json()
                return {}
        except Exception:
            return {}

    async def clear_user_memory(self, memory_key: str):
        """Clear a specific memory key for the user."""
        if not self.api_key:
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{BACKBOARD_BASE_URL}/memory/{self.user_id}:{memory_key}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
        except Exception:
            pass

    # =========================================================================
    # CONTEXTUAL HINTS - Enhanced with code history (Feature 1)
    # =========================================================================

    async def generate_contextual_hint(
        self,
        code_history: list,
        current_code: str,
        current_error: str,
        task_description: str,
        session_id: str,
    ) -> dict:
        """
        Generate smarter hints based on the user's code history within the session.
        Uses Claude for empathetic delivery with full context awareness.
        
        Args:
            code_history: List of {code, timestamp, error} entries from this session
            current_code: The current state of the code
            current_error: The current error message (if any)
            task_description: The task the user is working on
            session_id: For session-scoped memory
        """
        # Build code evolution summary
        evolution_summary = []
        for i, entry in enumerate(code_history[-5:]):  # Last 5 snapshots
            error_info = f" (Error: {entry.get('error', 'none')[:50]})" if entry.get('error') else ""
            evolution_summary.append(f"Attempt {i+1}: {len(entry.get('code', ''))} chars{error_info}")
        
        evolution_text = "\n".join(evolution_summary) if evolution_summary else "First attempt"
        
        # Identify patterns in errors
        error_patterns = []
        for entry in code_history:
            if entry.get('error'):
                error_patterns.append(entry['error'][:100])
        
        repeated_errors = len(error_patterns) != len(set(error_patterns))
        
        response = await self._call_model(
            model="anthropic/claude-3-haiku-20240307",
            messages=[
                {
                    "role": "system",
                    "content": """You are an encouraging coding mentor with full context of the student's session.

Rules:
- Give a brief, helpful hint (2-3 sentences max)
- Don't give away the answer
- Reference their progress if they've been improving
- If they keep making the same error, suggest a different approach
- Be encouraging and acknowledge their persistence
- Use your memory to avoid repeating hints you've already given""",
                },
                {
                    "role": "user",
                    "content": f"""Task: {task_description[:500]}

Code evolution in this session:
{evolution_text}

Current code:
```
{current_code[:1500]}
```

Current error: {current_error or 'No specific error, but tests failing'}

Has repeated same error: {repeated_errors}
Total attempts this session: {len(code_history) + 1}

Please provide a contextual hint based on their journey so far.""",
                },
            ],
            memory_key=f"session:{session_id}:hints",
            temperature=0.8,
            max_tokens=200,
        )
        
        return {
            "hint": response,
            "context": {
                "attempts": len(code_history) + 1,
                "repeated_errors": repeated_errors,
                "code_history_length": len(code_history),
            },
        }

    # =========================================================================
    # HIRING SELECTION - AI-ranked candidates (Feature 2)
    # =========================================================================

    async def rank_candidates(
        self,
        candidates: list,
        job_requirements: dict,
        amplitude_data: dict = None,
    ) -> list:
        """
        Rank candidates for a job using GPT-4o for structured analysis.
        
        Args:
            candidates: List of candidate dicts with radar_profile, sessions_completed, etc.
            job_requirements: Job's target_radar and requirements
            amplitude_data: Optional per-user analytics from Amplitude
        
        Returns:
            List of candidates with AI scores and explanations
        """
        # Prepare candidate summaries for the model
        candidate_summaries = []
        for c in candidates[:20]:  # Limit to 20 candidates per request
            summary = {
                "id": c.get("user_id") or c.get("_id"),
                "radar": c.get("radar_profile", {}),
                "sessions": c.get("sessions_completed", 0),
                "archetype": c.get("archetype"),
                "integrity": c.get("integrity_score", 0.5),
            }
            # Add Amplitude data if available
            if amplitude_data and summary["id"] in amplitude_data:
                user_amp = amplitude_data[summary["id"]]
                summary["activity_score"] = user_amp.get("activity_score", 0)
                summary["engagement_trend"] = user_amp.get("trend", "stable")
            candidate_summaries.append(summary)
        
        response = await self._call_model(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI hiring assistant. Rank candidates based on job fit.

Return valid JSON array only:
[
  {
    "id": "candidate_id",
    "score": 0.0-1.0,
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1"],
    "recommendation": "brief 1-sentence recommendation"
  }
]

Score based on:
- Radar profile alignment with job requirements (50%)
- Session completion and engagement (20%)
- Integrity score (15%)
- Archetype fit (15%)""",
                },
                {
                    "role": "user",
                    "content": f"""Job Requirements:
{json.dumps(job_requirements, indent=2)}

Candidates to rank:
{json.dumps(candidate_summaries, indent=2)}

Rank all candidates from best to worst fit.""",
                },
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        
        try:
            rankings = json.loads(response)
            # Merge rankings back with original candidate data
            ranking_map = {r["id"]: r for r in rankings}
            for c in candidates:
                cid = c.get("user_id") or c.get("_id")
                if cid in ranking_map:
                    c["ai_score"] = ranking_map[cid].get("score", 0.5)
                    c["ai_strengths"] = ranking_map[cid].get("strengths", [])
                    c["ai_gaps"] = ranking_map[cid].get("gaps", [])
                    c["ai_recommendation"] = ranking_map[cid].get("recommendation", "")
                else:
                    c["ai_score"] = 0.5
                    c["ai_strengths"] = []
                    c["ai_gaps"] = []
                    c["ai_recommendation"] = "Unable to analyze"
            
            # Sort by AI score
            candidates.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
            return candidates
            
        except json.JSONDecodeError:
            # Return candidates with default scores
            for c in candidates:
                c["ai_score"] = 0.5
                c["ai_recommendation"] = "Analysis unavailable"
            return candidates

    async def explain_candidate_fit(
        self,
        candidate: dict,
        job: dict,
        amplitude_data: dict = None,
    ) -> dict:
        """
        Generate detailed AI analysis for a specific candidate-job match.
        """
        response = await self._call_model(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Provide a detailed hiring analysis. Return valid JSON:
{
  "overall_score": 0.0-1.0,
  "summary": "2-3 sentence overall assessment",
  "dimension_analysis": {
    "verification": {"score": 0.0-1.0, "note": "brief note"},
    "velocity": {"score": 0.0-1.0, "note": "brief note"},
    "optimization": {"score": 0.0-1.0, "note": "brief note"},
    "decomposition": {"score": 0.0-1.0, "note": "brief note"},
    "debugging": {"score": 0.0-1.0, "note": "brief note"}
  },
  "key_strengths": ["strength1", "strength2", "strength3"],
  "areas_of_concern": ["concern1"],
  "interview_focus_areas": ["topic1", "topic2"],
  "hiring_recommendation": "strong_hire|hire|maybe|no_hire"
}""",
                },
                {
                    "role": "user",
                    "content": f"""Candidate Profile:
- Radar: {json.dumps(candidate.get('radar_profile', {}), indent=2)}
- Archetype: {candidate.get('archetype', 'unknown')}
- Sessions Completed: {candidate.get('sessions_completed', 0)}
- Integrity Score: {candidate.get('integrity_score', 'N/A')}
- Activity Data: {json.dumps(amplitude_data or {}, indent=2)}

Job Requirements:
- Target Radar: {json.dumps(job.get('target_radar', {}), indent=2)}
- Role: {job.get('title', 'Unknown')}
- Description: {job.get('description', 'N/A')[:500]}

Provide a comprehensive hiring analysis.""",
                },
            ],
            temperature=0.4,
            max_tokens=800,
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "overall_score": 0.5,
                "summary": response[:200] if response else "Analysis unavailable",
                "hiring_recommendation": "maybe",
            }

    # =========================================================================
    # TASK HELP CHAT - Gemini-powered (Feature 3)
    # =========================================================================

    async def task_help_chat(
        self,
        task: dict,
        current_code: str,
        question: str,
        session_id: str,
        error_context: str = None,
    ) -> str:
        """
        Interactive task help using Gemini for natural conversation.
        Memory enabled for conversation history within the session.
        
        Args:
            task: Task details (title, description, test_cases)
            current_code: User's current code
            question: User's question
            session_id: For conversation memory
            error_context: Optional current error
        """
        task_context = f"""Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'N/A')[:800]}
Difficulty: {task.get('difficulty', 'unknown')}"""

        code_context = f"""Current Code:
```
{current_code[:1500]}
```"""

        error_info = f"\nCurrent Error: {error_context}" if error_context else ""

        system_instruction = """You are a helpful coding assistant for a coding assessment platform.

Rules:
- Help the user understand concepts and debug issues
- Don't give away complete solutions
- Guide them toward the answer with questions and hints
- Be concise but thorough (2-4 sentences typically)
- Remember the conversation context
- If they ask unrelated questions, redirect to the task
- You can explain concepts, syntax, and debugging strategies"""

        prompt = f"""{task_context}

{code_context}{error_info}

User's question: {question}"""

        return await self._call_gemini(
            prompt=prompt,
            system_instruction=system_instruction,
            session_key=f"session:{session_id}:chat",
            temperature=0.7,
            max_tokens=400,
        )
