"""
Backboard.io Multi-Model AI Service

Provides adaptive memory and intelligent model switching for different tasks:
- Claude for empathetic hints (anthropic/claude-3-haiku)
- GPT-4o for code analysis (openai/gpt-4o-mini)
- Gemini for profile summaries (google/gemini-1.5-flash)
- Cohere for job parsing (cohere/command-r)
"""

import httpx
import json
from typing import Optional
from config import get_settings

BACKBOARD_BASE_URL = "https://api.backboard.io/v1"


class BackboardService:
    """
    Multi-model AI service using Backboard.io for adaptive memory
    and intelligent model switching.
    """

    def __init__(self, user_id: str):
        settings = get_settings()
        self.api_key = settings.backboard_api_key
        self.user_id = user_id

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
    # PROFILE SUMMARIZATION - Gemini (structured analysis)
    # =========================================================================

    async def summarize_radar_profile(self, radar: dict, recent_events: list) -> str:
        """
        Use Gemini for structured profile summarization.
        Memory: Tracks how profile has evolved over time.
        """
        return await self._call_model(
            model="google/gemini-1.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize this developer's coding style based on their radar profile and recent behavior.

Radar Profile (scores 0-1):
{json.dumps(radar, indent=2)}

Recent Events (last 10):
{json.dumps(recent_events[-10:] if recent_events else [], indent=2, default=str)}

Provide:
1. Their strongest trait (1 sentence)
2. Area for growth (1 sentence)
3. How their style compares to their previous sessions (if you remember them)

Keep it concise and actionable.""",
                }
            ],
            memory_key="profile_history",
            temperature=0.6,
            max_tokens=200,
        )

    async def generate_archetype_description(self, archetype: str, radar: dict) -> str:
        """Generate personalized archetype description based on actual scores."""
        return await self._call_model(
            model="google/gemini-1.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": f"""The developer has been classified as: "{archetype}"

Their radar scores: {json.dumps(radar, indent=2)}

Write a 2-sentence personalized description of their engineering style that reflects their actual scores. Be specific, not generic.""",
                }
            ],
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
