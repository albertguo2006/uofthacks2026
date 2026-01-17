"""
Backboard.io Multi-Model AI Service + Direct Gemini API

Using the backboard-sdk for proper API integration.

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
from backboard import BackboardClient

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# ANSI color codes for terminal output
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
DIM = "\033[2m"

# Cache for assistants and threads (module-level to persist across requests)
_assistant_cache: dict[str, str] = {}  # assistant_name -> assistant_id
_thread_cache: dict[str, str] = {}  # cache_key -> thread_id


class BackboardService:
    """
    Multi-model AI service using Backboard.io SDK for adaptive memory
    and intelligent model switching.
    """

    def __init__(self, user_id: str):
        settings = get_settings()
        self.api_key = settings.backboard_api_key
        self.gemini_api_key = settings.gemini_api_key
        self.user_id = user_id
        self.client = BackboardClient(api_key=self.api_key) if self.api_key else None
        # In-memory conversation history for Gemini (keyed by session)
        self._gemini_history: dict[str, list] = {}

    async def _get_or_create_assistant(self, name: str, system_prompt: str) -> Optional[str]:
        """Get or create an assistant by name."""
        if not self.client:
            return None

        cache_key = f"{name}"
        if cache_key in _assistant_cache:
            return _assistant_cache[cache_key]

        try:
            # SDK uses 'description' for the system prompt
            assistant = await self.client.create_assistant(
                name=name,
                description=system_prompt
            )
            assistant_id_str = str(assistant.assistant_id)
            _assistant_cache[cache_key] = assistant_id_str
            print(f"{GREEN}[Backboard] Created assistant: {name} ({assistant_id_str[:12]}...){RESET}")
            return assistant_id_str
        except Exception as e:
            print(f"{RED}[Backboard] Failed to create assistant {name}: {e}{RESET}")
            return None

    async def _get_or_create_thread(self, assistant_id: str, thread_key: str) -> Optional[str]:
        """Get or create a thread for a specific context."""
        if not self.client or not assistant_id:
            return None

        cache_key = f"{assistant_id}:{thread_key}"
        if cache_key in _thread_cache:
            return _thread_cache[cache_key]

        try:
            thread = await self.client.create_thread(assistant_id)
            thread_id_str = str(thread.thread_id)
            _thread_cache[cache_key] = thread_id_str
            print(f"{DIM}[Backboard] Created thread for {thread_key[:20]}...{RESET}")
            return thread_id_str
        except Exception as e:
            print(f"{RED}[Backboard] Failed to create thread: {e}{RESET}")
            return None

    async def _call_model(
        self,
        assistant_name: str,
        system_prompt: str,
        user_message: str,
        llm_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        thread_key: Optional[str] = None,
        use_memory: bool = False,
    ) -> str:
        """
        Generic model call using Backboard SDK.
        """
        # Log the prompt
        print(f"\n{CYAN}╭─────────────────────────────────────────────────────────────╮{RESET}")
        print(f"{CYAN}│ [Backboard] Calling {llm_provider}/{model_name}{RESET}")
        print(f"{CYAN}├─────────────────────────────────────────────────────────────┤{RESET}")

        if thread_key:
            print(f"{CYAN}│ Thread Key: {self.user_id[:8]}...:{thread_key[:20]}...{RESET}")

        print(f"{MAGENTA}│ [system] {system_prompt[:150]}...{RESET}" if len(system_prompt) > 150 else f"{MAGENTA}│ [system] {system_prompt}{RESET}")
        print(f"{BLUE}│ [user] {user_message[:200]}...{RESET}" if len(user_message) > 200 else f"{BLUE}│ [user] {user_message}{RESET}")
        print(f"{CYAN}╰─────────────────────────────────────────────────────────────╯{RESET}")

        if not self.client:
            print(f"{YELLOW}[Backboard] Skipped - API key not configured, using fallback{RESET}")
            return self._fallback_response([{"content": user_message}])

        try:
            # Get or create assistant
            assistant_id = await self._get_or_create_assistant(assistant_name, system_prompt)
            if not assistant_id:
                return self._fallback_response([{"content": user_message}])

            # Get or create thread (use user_id + thread_key for uniqueness)
            actual_thread_key = f"{self.user_id}:{thread_key}" if thread_key else f"{self.user_id}:default"
            thread_id = await self._get_or_create_thread(assistant_id, actual_thread_key)
            if not thread_id:
                return self._fallback_response([{"content": user_message}])

            # Send message
            response = await self.client.add_message(
                thread_id=thread_id,
                content=user_message,
                llm_provider=llm_provider,
                model_name=model_name,
                memory="Auto" if use_memory else None,
                stream=False
            )

            result = response.content
            print(f"{GREEN}[Backboard] ✓ {model_name} responded ({len(result)} chars){RESET}")
            print(f"{DIM}[Backboard] Response: {result[:150]}...{RESET}" if len(result) > 150 else f"{DIM}[Backboard] Response: {result}{RESET}")

            return result

        except Exception as e:
            print(f"{RED}[Backboard] ✗ Error calling {model_name}: {e}{RESET}")
            return self._fallback_response([{"content": user_message}])

    def _fallback_response(self, messages: list) -> str:
        """Provide a fallback response when API is unavailable."""
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
        print(f"\n{MAGENTA}╭─────────────────────────────────────────────────────────────╮{RESET}")
        print(f"{MAGENTA}│ [Gemini] Direct API Call (gemini-2.5-flash){RESET}")
        print(f"{MAGENTA}├─────────────────────────────────────────────────────────────┤{RESET}")

        if session_key:
            history_len = len(self._gemini_history.get(session_key, []))
            print(f"{MAGENTA}│ Session: {session_key[:20]}... (history: {history_len} msgs){RESET}")

        if system_instruction:
            print(f"{BLUE}│ [system] {system_instruction[:150]}...{RESET}" if len(system_instruction) > 150 else f"{BLUE}│ [system] {system_instruction}{RESET}")

        print(f"{CYAN}│ [user] {prompt[:200]}...{RESET}" if len(prompt) > 200 else f"{CYAN}│ [user] {prompt}{RESET}")
        print(f"{MAGENTA}╰─────────────────────────────────────────────────────────────╯{RESET}")

        if not self.gemini_api_key:
            print(f"{YELLOW}[Gemini] Skipped - API key not configured, using fallback{RESET}")
            return self._fallback_response([{"content": prompt}])

        try:
            contents = []

            if session_key and session_key in self._gemini_history:
                contents.extend(self._gemini_history[session_key])

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

            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{GEMINI_API_URL}/gemini-2.5-flash:generateContent?key={self.gemini_api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()
                response_text = result["candidates"][0]["content"]["parts"][0]["text"]

                print(f"{GREEN}[Gemini] ✓ Response received ({len(response_text)} chars){RESET}")
                print(f"{DIM}[Gemini] Response: {response_text[:150]}...{RESET}" if len(response_text) > 150 else f"{DIM}[Gemini] Response: {response_text}{RESET}")

                if session_key:
                    if session_key not in self._gemini_history:
                        self._gemini_history[session_key] = []

                    self._gemini_history[session_key].append({
                        "role": "user",
                        "parts": [{"text": prompt}]
                    })
                    self._gemini_history[session_key].append({
                        "role": "model",
                        "parts": [{"text": response_text}]
                    })

                    if len(self._gemini_history[session_key]) > 40:
                        self._gemini_history[session_key] = self._gemini_history[session_key][-40:]

                return response_text

        except Exception as e:
            print(f"{RED}[Gemini] ✗ Error: {e}{RESET}")
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
        print(f"\n{CYAN}[Hint] Generating basic hint (attempt #{attempt_count}){RESET}")

        system_prompt = """You are an encouraging coding mentor helping a student who is stuck.

Rules:
- Give a brief, helpful hint (1-2 sentences max)
- Don't give away the answer
- Be encouraging and supportive
- If you've given similar hints before (check your memory), try a different approach
- Acknowledge their effort if they've been trying for a while"""

        user_message = f"""The student's current code:
```
{code[:1500]}
```

Error/Issue: {error}

This is attempt #{attempt_count}. Please provide a helpful hint."""

        return await self._call_model(
            assistant_name="HintAssistant",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"hints:{self.user_id}",
            use_memory=True,
        )

    async def generate_encouragement(self, context: str) -> str:
        """Generate pure encouragement when user seems frustrated."""
        system_prompt = "You are a supportive coding mentor. Give a brief (1 sentence) word of encouragement. Be genuine, not cheesy."

        return await self._call_model(
            assistant_name="EncouragementAssistant",
            system_prompt=system_prompt,
            user_message=f"Context: {context}",
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"encouragement:{self.user_id}",
        )

    # =========================================================================
    # PERSONALIZED HINTS - Based on error profile (Adaptive Hints Feature)
    # =========================================================================

    async def generate_personalized_hint(
        self,
        code: str,
        error: str,
        attempt_count: int,
        error_profile: dict,
    ) -> dict:
        """
        Generate a personalized hint based on user's error profile.
        """
        dominant_category = error_profile.get("dominant_category", "logic")
        print(f"\n{MAGENTA}[Hint] Generating PERSONALIZED hint (attempt #{attempt_count}, profile: {dominant_category}){RESET}")
        effective_styles = error_profile.get("effective_hint_styles", ["conceptual"])
        hint_style = effective_styles[0] if effective_styles else "conceptual"

        system_prompt = self._get_style_prompt(dominant_category, hint_style)
        badge = self._get_personalization_badge(dominant_category, error_profile)

        user_message = f"""The student's current code:
```
{code[:1500]}
```

Error/Issue: {error}

This is attempt #{attempt_count}. Please provide a helpful hint."""

        hint = await self._call_model(
            assistant_name=f"PersonalizedHintAssistant_{dominant_category}",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"personalized_hints:{self.user_id}",
            use_memory=True,
        )

        return {
            "hint": hint,
            "personalization_badge": badge,
            "hint_style": hint_style,
            "dominant_category": dominant_category
        }

    def _get_style_prompt(self, dominant_category: str, hint_style: str) -> str:
        """Get style-specific system prompt based on user's error patterns."""

        base_rules = """Rules:
- Give a brief, helpful hint (2-3 sentences max)
- Don't give away the answer
- Be encouraging and supportive
- If you've given similar hints before (check your memory), try a different approach"""

        if dominant_category == "syntax":
            return f"""You are an encouraging coding mentor helping a student who often struggles with syntax errors.

{base_rules}

Style guidance for syntax strugglers:
- Be code-focused with specific line numbers when possible
- Show correct syntax patterns with examples
- Point out common syntax pitfalls (missing brackets, semicolons, indentation)
- Use format: "Check line X - [specific issue]. Pattern: `correct_syntax_here`"
"""

        elif dominant_category == "logic":
            return f"""You are an encouraging coding mentor helping a student who often struggles with logical reasoning.

{base_rules}

Style guidance for logic strugglers:
- Use Socratic questioning to guide their thinking
- Ask "What did you expect vs what actually happened?"
- Suggest debugging with print statements to trace values
- Help them think through edge cases and conditions
"""

        elif dominant_category == "type":
            return f"""You are an encouraging coding mentor helping a student who often struggles with type-related errors.

{base_rules}

Style guidance for type strugglers:
- Emphasize type checking and validation
- Suggest using typeof/type() to debug type issues
- Point out common type coercion pitfalls
- Help identify where undefined/null values might originate
"""

        else:  # runtime
            return f"""You are an encouraging coding mentor helping a student who often encounters runtime errors.

{base_rules}

Style guidance for runtime issues:
- Help identify potential infinite loops or recursion issues
- Suggest adding base cases or termination conditions
- Point out memory-intensive operations
- Guide them to optimize or restructure problematic code
"""

    def _get_personalization_badge(self, dominant_category: str, error_profile: dict) -> str:
        """Generate a personalization badge explaining why this hint style was chosen."""
        trend = error_profile.get("recent_trend", "stable")
        total_errors = error_profile.get("total_errors", 0)

        if total_errors < 5:
            return "Personalized hint"

        category_labels = {
            "syntax": "syntax error patterns",
            "logic": "logical reasoning challenges",
            "type": "type-related patterns",
            "runtime": "runtime error history"
        }

        category_label = category_labels.get(dominant_category, "error patterns")

        if trend == "improving":
            return f"Based on your {category_label} (you're improving!)"
        elif trend == "struggling":
            return f"Tailored for your {category_label}"
        else:
            return f"Based on your {category_label}"

    # =========================================================================
    # CODE ANALYSIS - GPT-4o (strong code understanding)
    # =========================================================================

    async def analyze_code_error(self, code: str, error: str) -> dict:
        """
        Use GPT-4o for detailed technical code analysis.
        Returns structured analysis of the error.
        """
        system_prompt = """Analyze the code error. Return valid JSON only with this structure:
{{
  "error_type": "syntax|runtime|logic|type",
  "root_cause": "brief explanation",
  "affected_lines": "line numbers or description",
  "severity": 1-5,
  "category": "null_reference|off_by_one|type_mismatch|syntax|other"
}}"""

        user_message = f"Code:\n```\n{code[:2000]}\n```\n\nError: {error}"

        response = await self._call_model(
            assistant_name="CodeAnalysisAssistant",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"code_analysis:{self.user_id}",
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error_type": "unknown", "root_cause": response, "severity": 3}

    async def suggest_fix(self, code: str, error: str) -> str:
        """
        Use GPT-4o to suggest a specific fix without giving full solution.
        """
        system_prompt = "Suggest a specific fix for this code issue. Be concise (2-3 sentences). Point to the exact location and what needs to change, but don't write the full corrected code."

        return await self._call_model(
            assistant_name="FixSuggestionAssistant",
            system_prompt=system_prompt,
            user_message=f"```\n{code[:2000]}\n```\n\nError: {error}",
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"fix_suggestion:{self.user_id}",
        )

    # =========================================================================
    # PROFILE SUMMARIZATION - Gemini DIRECT API (structured analysis)
    # =========================================================================

    async def summarize_radar_profile(self, radar: dict, recent_events: list) -> str:
        """
        Use Gemini (direct API) for structured profile summarization.
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
        """Generate personalized archetype description based on actual scores."""
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
        """
        system_prompt = "You parse job descriptions and extract ideal candidate profiles. Return only valid JSON."

        user_message = f"""Extract the ideal candidate profile from this job description.

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

Base scores on explicit and implicit requirements in the description."""

        response = await self._call_model(
            assistant_name="JobParsingAssistant",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"job_parsing:{self.user_id}",
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
        system_prompt = "You explain job-candidate fit in concise terms."

        return await self._call_model(
            assistant_name="JobMatchAssistant",
            system_prompt=system_prompt,
            user_message=f"""Candidate radar: {json.dumps(candidate_radar)}
Job requirements: {json.dumps(job_radar)}
Match score: {fit_score:.0%}

Explain in 1-2 sentences why this candidate does/doesn't match this role. Be specific about which dimensions align or differ.""",
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"job_match:{self.user_id}",
        )

    # =========================================================================
    # ADAPTIVE INTERVENTION - Intelligent model routing
    # =========================================================================

    async def adaptive_intervention(self, session_context: dict, error_profile: dict = None) -> dict:
        """
        Intelligently choose intervention type and model based on context.
        """
        code = session_context.get("code", "")
        last_error = session_context.get("last_error")
        error_streak = session_context.get("error_streak", 0)
        time_stuck_ms = session_context.get("time_stuck_ms", 0)
        attempt_count = session_context.get("attempt_count", 1)

        print(f"\n{BLUE}[Intervention] Evaluating... (errors: {error_streak}, stuck: {time_stuck_ms // 1000}s){RESET}")

        use_personalized = error_profile and error_profile.get("has_data", False)

        if error_streak >= 3 and last_error:
            analysis = await self.analyze_code_error(code, last_error)

            if use_personalized:
                hint_result = await self.generate_personalized_hint(
                    code, last_error, attempt_count, error_profile
                )
                return {
                    "type": "technical_hint",
                    "analysis": analysis,
                    "hint": hint_result["hint"],
                    "personalization_badge": hint_result["personalization_badge"],
                    "hint_style": hint_result["hint_style"],
                    "model_used": ["gpt-4o-mini", "claude-3-haiku"],
                }
            else:
                hint = await self.generate_hint(code, last_error, attempt_count)
                return {
                    "type": "technical_hint",
                    "analysis": analysis,
                    "hint": hint,
                    "model_used": ["gpt-4o-mini", "claude-3-haiku"],
                }

        elif time_stuck_ms > 180000:
            if use_personalized:
                hint_result = await self.generate_personalized_hint(
                    code,
                    "User seems stuck (no progress for 3 minutes)",
                    attempt_count,
                    error_profile
                )
                encouragement = await self.generate_encouragement(
                    f"User has been working for {time_stuck_ms // 60000} minutes"
                )
                return {
                    "type": "encouragement",
                    "hint": hint_result["hint"],
                    "encouragement": encouragement,
                    "personalization_badge": hint_result["personalization_badge"],
                    "hint_style": hint_result["hint_style"],
                    "model_used": ["claude-3-haiku"],
                }
            else:
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
            if use_personalized:
                hint_result = await self.generate_personalized_hint(
                    code, last_error or "struggling", attempt_count, error_profile
                )
                return {
                    "type": "gentle_nudge",
                    "hint": hint_result["hint"],
                    "personalization_badge": hint_result["personalization_badge"],
                    "hint_style": hint_result["hint_style"],
                    "model_used": ["claude-3-haiku"],
                }
            else:
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
        """
        print(f"\n{CYAN}[Hint] Generating CONTEXTUAL hint (history: {len(code_history)} snapshots, session: {session_id[:12]}...){RESET}")

        evolution_summary = []
        for i, entry in enumerate(code_history[-5:]):
            error_info = f" (Error: {entry.get('error', 'none')[:50]})" if entry.get('error') else ""
            evolution_summary.append(f"Attempt {i+1}: {len(entry.get('code', ''))} chars{error_info}")

        evolution_text = "\n".join(evolution_summary) if evolution_summary else "First attempt"

        error_patterns = []
        for entry in code_history:
            if entry.get('error'):
                error_patterns.append(entry['error'][:100])

        repeated_errors = len(error_patterns) != len(set(error_patterns))

        system_prompt = """You are an encouraging coding mentor with full context of the student's session.

Rules:
- Give a brief, helpful hint (2-3 sentences max)
- Don't give away the answer
- Reference their progress if they've been improving
- If they keep making the same error, suggest a different approach
- Be encouraging and acknowledge their persistence
- Use your memory to avoid repeating hints you've already given"""

        user_message = f"""Task: {task_description[:500]}

Code evolution in this session:
{evolution_text}

Current code:
```
{current_code[:1500]}
```

Current error: {current_error or 'No specific error, but tests failing'}

Has repeated same error: {repeated_errors}
Total attempts this session: {len(code_history) + 1}

Please provide a contextual hint based on their journey so far."""

        response = await self._call_model(
            assistant_name="ContextualHintAssistant",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"session:{session_id}:hints",
            use_memory=True,
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
        """
        candidate_summaries = []
        for c in candidates[:20]:
            summary = {
                "id": c.get("user_id") or c.get("_id"),
                "radar": c.get("radar_profile", {}),
                "sessions": c.get("sessions_completed", 0),
                "archetype": c.get("archetype"),
                "integrity": c.get("integrity_score", 0.5),
            }
            if amplitude_data and summary["id"] in amplitude_data:
                user_amp = amplitude_data[summary["id"]]
                summary["activity_score"] = user_amp.get("activity_score", 0)
                summary["engagement_trend"] = user_amp.get("trend", "stable")
            candidate_summaries.append(summary)

        system_prompt = """You are an AI hiring assistant. Rank candidates based on job fit.

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
- Archetype fit (15%)"""

        user_message = f"""Job Requirements:
{json.dumps(job_requirements, indent=2)}

Candidates to rank:
{json.dumps(candidate_summaries, indent=2)}

Rank all candidates from best to worst fit."""

        response = await self._call_model(
            assistant_name="CandidateRankingAssistant",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"candidate_ranking:{self.user_id}",
        )

        try:
            rankings = json.loads(response)
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

            candidates.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
            return candidates

        except json.JSONDecodeError:
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
        system_prompt = """Provide a detailed hiring analysis. Return valid JSON:
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
}"""

        user_message = f"""Candidate Profile:
- Radar: {json.dumps(candidate.get('radar_profile', {}), indent=2)}
- Archetype: {candidate.get('archetype', 'unknown')}
- Sessions Completed: {candidate.get('sessions_completed', 0)}
- Integrity Score: {candidate.get('integrity_score', 'N/A')}
- Activity Data: {json.dumps(amplitude_data or {}, indent=2)}

Job Requirements:
- Target Radar: {json.dumps(job.get('target_radar', {}), indent=2)}
- Role: {job.get('title', 'Unknown')}
- Description: {job.get('description', 'N/A')[:500]}

Provide a comprehensive hiring analysis."""

        response = await self._call_model(
            assistant_name="CandidateFitAnalysisAssistant",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="openai",
            model_name="gpt-4o",
            thread_key=f"candidate_fit:{self.user_id}",
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
