"""
Backboard.io Multi-Model AI Service + Direct Gemini API

Using the backboard-sdk for proper API integration.

Model routing (Two AI Models for hints + archetype):
- Claude (anthropic/claude-3-5-sonnet) for empathetic hints [PRIMARY for hints]
  - generate_hint, generate_personalized_hint, generate_targeted_hint
  - generate_encouragement
  - Fallback: Gemini API
  
- GPT-4 (openai/gpt-4o) for behavioral analysis [PRIMARY for archetypes]
  - ai_assign_archetype - AI-driven archetype assignment
  - analyze_code_error - Technical code analysis
  - parse_job_requirements - Job description parsing
  
- Gemini (direct API - gemini-2.5-flash) for:
  - Profile summaries & chat
  - Fallback when Backboard is unavailable
  
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
            # Truncate error message to avoid logging huge HTML responses
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "... [truncated]"
            # Check if it's an HTML response (API error page)
            if "<!doctype" in error_msg.lower() or "<html" in error_msg.lower():
                error_msg = "API returned HTML error page (likely 404 or server error)"
            print(f"{RED}[Backboard] Failed to create assistant {name}: {error_msg}{RESET}")
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
            # Truncate error message to avoid logging huge HTML responses
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "... [truncated]"
            if "<!doctype" in error_msg.lower() or "<html" in error_msg.lower():
                error_msg = "API returned HTML error page (likely 404 or server error)"
            print(f"{RED}[Backboard] Failed to create thread: {error_msg}{RESET}")
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
        Falls back to Gemini if Backboard fails (timeout, no credits, etc.)
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
            print(f"{YELLOW}[Backboard] Skipped - API key not configured, falling back to Gemini{RESET}")
            return await self._gemini_fallback(system_prompt, user_message, thread_key)

        try:
            # Get or create assistant
            assistant_id = await self._get_or_create_assistant(assistant_name, system_prompt)
            if not assistant_id:
                print(f"{YELLOW}[Backboard] Failed to create assistant, falling back to Gemini{RESET}")
                return await self._gemini_fallback(system_prompt, user_message, thread_key)

            # Get or create thread (use user_id + thread_key for uniqueness)
            actual_thread_key = f"{self.user_id}:{thread_key}" if thread_key else f"{self.user_id}:default"
            thread_id = await self._get_or_create_thread(assistant_id, actual_thread_key)
            if not thread_id:
                print(f"{YELLOW}[Backboard] Failed to create thread, falling back to Gemini{RESET}")
                return await self._gemini_fallback(system_prompt, user_message, thread_key)

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
            # Truncate error message to avoid logging huge HTML responses
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "... [truncated]"
            if "<!doctype" in error_msg.lower() or "<html" in error_msg.lower():
                error_msg = "API returned HTML error page (likely 404 or server error)"
            print(f"{RED}[Backboard] ✗ Error calling {model_name}: {error_msg}{RESET}")
            print(f"{YELLOW}[Backboard] Falling back to Gemini...{RESET}")
            return await self._gemini_fallback(system_prompt, user_message, thread_key)

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

    async def _gemini_fallback(
        self,
        system_prompt: str,
        user_message: str,
        thread_key: Optional[str] = None,
    ) -> str:
        """
        Fallback to Gemini when Backboard is unavailable (timeout, no credits, etc.)
        Combines system prompt and user message for Gemini's format.
        """
        print(f"{YELLOW}[Fallback] Using Gemini as fallback for Backboard{RESET}")

        # Build session key for conversation continuity if thread_key provided
        session_key = f"{self.user_id}:fallback:{thread_key}" if thread_key else None

        # Call Gemini with the system prompt as instruction
        result = await self._call_gemini(
            prompt=user_message,
            system_instruction=system_prompt,
            session_key=session_key,
            temperature=0.7,
            max_tokens=500,
        )

        # If Gemini also fails, return the basic fallback
        if not result or result == self._fallback_response([]):
            print(f"{RED}[Fallback] Gemini also failed, using basic fallback{RESET}")
            return self._fallback_response([{"content": user_message}])

        return result

    def _strip_markdown_json(self, response: str) -> str:
        """Strip markdown code blocks from JSON response."""
        clean = response.strip()
        if clean.startswith("```"):
            # Remove opening fence (```json or ```)
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return clean.strip()

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

    async def clear_user_memory(self, memory_key: str):
        """
        Clear memory for a specific context.
        Clears both Backboard thread cache and Gemini history.
        """
        # Clear Gemini history for this key
        self.clear_gemini_history(memory_key)

        # Clear fallback Gemini history as well
        fallback_key = f"{self.user_id}:fallback:{memory_key}"
        self.clear_gemini_history(fallback_key)

        # Clear from thread cache if exists
        keys_to_remove = [k for k in _thread_cache.keys() if memory_key in k]
        for key in keys_to_remove:
            del _thread_cache[key]

        print(f"{DIM}[Memory] Cleared memory for key: {memory_key}{RESET}")

    # =========================================================================
    # HINT GENERATION - Claude (empathetic, pedagogical) with Gemini fallback
    # =========================================================================

    async def generate_hint(self, code: str, error: str, attempt_count: int) -> str:
        """
        Use Claude for empathetic, pedagogical hints.
        Primary: Claude (via Backboard) - Best for empathetic, nuanced responses
        Fallback: Gemini (direct API) - Fast and reliable backup
        
        Memory: Remembers past hints to avoid repetition.
        """
        print(f"\n{CYAN}[Hint] Generating hint with CLAUDE (attempt #{attempt_count}){RESET}")

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
            llm_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",  # Claude for empathetic hints
            thread_key=f"hints:{self.user_id}",
            use_memory=True,
        )

    async def generate_encouragement(self, context: str) -> str:
        """
        Generate pure encouragement when user seems frustrated.
        Uses Claude for empathetic, genuine encouragement.
        """
        system_prompt = "You are a supportive coding mentor. Give a brief (1 sentence) word of encouragement. Be genuine, not cheesy."

        return await self._call_model(
            assistant_name="EncouragementAssistant",
            system_prompt=system_prompt,
            user_message=f"Context: {context}",
            llm_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",  # Claude for empathetic responses
            thread_key=f"encouragement:{self.user_id}",
        )

    # =========================================================================
    # PERSONALIZED HINTS - Based on error profile (Adaptive Hints Feature)
    # Uses Claude for empathetic, personalized hints with Gemini fallback
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
        Primary: Claude (via Backboard) - Best for personalized, empathetic responses
        Fallback: Gemini (direct API) - Fast and reliable backup
        """
        dominant_category = error_profile.get("dominant_category", "logic")
        print(f"\n{MAGENTA}[Hint] Generating PERSONALIZED hint with CLAUDE (attempt #{attempt_count}, profile: {dominant_category}){RESET}")
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
            llm_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",  # Claude for personalized hints
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
            return json.loads(self._strip_markdown_json(response))
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
    # AI-POWERED ARCHETYPE ASSIGNMENT - GPT-4/ChatGPT (behavioral analysis)
    # =========================================================================

    async def ai_assign_archetype(
        self,
        skill_vector: list[float],
        behavioral_history: dict,
        analytics_summary: dict = None,
    ) -> dict:
        """
        Use GPT-4/ChatGPT for AI-driven archetype assignment based on behavioral analysis.
        
        This is used as a backup/secondary AI model when Amplitude AI data is unavailable,
        or as a complementary signal to enhance archetype assignment accuracy.
        
        Args:
            skill_vector: The 5-dimension skill vector [iteration_velocity, debug_efficiency, 
                         craftsmanship, tool_fluency, integrity]
            behavioral_history: Dictionary containing user's behavioral data from sessions
            analytics_summary: Optional summary from local analytics
        
        Returns:
            dict with:
                - archetype: The AI-suggested archetype
                - confidence: Confidence score (0-1)
                - reasoning: Brief explanation of why this archetype was assigned
                - adjustments: Score adjustments for each archetype
        """
        print(f"\n{MAGENTA}[AI Archetype] Using GPT-4/ChatGPT for behavioral analysis...{RESET}")
        
        # Prepare behavioral context for the AI
        skill_labels = ["iteration_velocity", "debug_efficiency", "craftsmanship", "tool_fluency", "integrity"]
        skill_dict = {skill_labels[i]: skill_vector[i] for i in range(min(len(skill_vector), 5))}
        
        system_prompt = """You are an expert at analyzing developer behavior patterns and assigning developer archetypes.

Based on the provided skill vector and behavioral history, assign one of these archetypes:
- "fast_iterator": Developers who iterate quickly, run tests frequently, and move fast
- "careful_tester": Developers who are methodical, have high pass rates, and focus on correctness
- "debugger": Developers who excel at fixing errors and have strong debugging skills
- "craftsman": Developers who write clean code independently with minimal AI assistance
- "explorer": Developers who try different approaches and use hints constructively

Analyze the behavioral patterns holistically. Consider:
1. The skill vector scores (0-1 scale)
2. Session statistics (pass rate, average score)
3. Activity patterns (runs per submission, code changes)
4. AI assistance usage (hints requested, chat help)
5. Integrity metrics (violations, paste bursts)
6. Learning patterns (fix efficiency, error recovery)

Return ONLY valid JSON in this exact format:
{
  "archetype": "archetype_name",
  "confidence": 0.X,
  "reasoning": "Brief 1-2 sentence explanation",
  "adjustments": {
    "fast_iterator": 0.X,
    "careful_tester": 0.X,
    "debugger": 0.X,
    "craftsman": 0.X,
    "explorer": 0.X
  }
}"""

        user_message = f"""Analyze this developer's behavior and assign an archetype:

SKILL VECTOR (0-1 scale):
{json.dumps(skill_dict, indent=2)}

BEHAVIORAL HISTORY:
{json.dumps(behavioral_history, indent=2, default=str)}

ANALYTICS SUMMARY:
{json.dumps(analytics_summary or {}, indent=2, default=str)}

Provide your archetype assignment with confidence and reasoning."""

        try:
            response = await self._call_model(
                assistant_name="ArchetypeAssignmentAssistant",
                system_prompt=system_prompt,
                user_message=user_message,
                llm_provider="openai",
                model_name="gpt-4o",  # Using GPT-4o for best reasoning
                thread_key=f"archetype:{self.user_id}",
                use_memory=False,  # Fresh analysis each time
            )
            
            result = json.loads(self._strip_markdown_json(response))
            
            # Validate the response
            valid_archetypes = ["fast_iterator", "careful_tester", "debugger", "craftsman", "explorer"]
            if result.get("archetype") not in valid_archetypes:
                raise ValueError(f"Invalid archetype: {result.get('archetype')}")
            
            result["confidence"] = min(1.0, max(0.0, float(result.get("confidence", 0.5))))
            
            # Ensure adjustments exist and are valid
            if "adjustments" not in result:
                result["adjustments"] = {}
            for arch in valid_archetypes:
                if arch not in result["adjustments"]:
                    result["adjustments"][arch] = 0.0
                result["adjustments"][arch] = min(1.0, max(0.0, float(result["adjustments"][arch])))
            
            result["model_used"] = "gpt-4o"
            result["ai_source"] = "backboard"
            
            print(f"{GREEN}[AI Archetype] ✓ GPT-4 assigned: {result['archetype']} (confidence: {result['confidence']:.2f}){RESET}")
            print(f"{DIM}[AI Archetype] Reasoning: {result.get('reasoning', 'N/A')}{RESET}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"{RED}[AI Archetype] ✗ Failed to parse GPT-4 response: {e}{RESET}")
            return self._fallback_archetype_assignment(skill_vector)
        except Exception as e:
            print(f"{RED}[AI Archetype] ✗ GPT-4 archetype assignment failed: {e}{RESET}")
            return self._fallback_archetype_assignment(skill_vector)
    
    def _fallback_archetype_assignment(self, skill_vector: list[float]) -> dict:
        """
        Fallback to mathematical archetype assignment when AI is unavailable.
        """
        print(f"{YELLOW}[AI Archetype] Using mathematical fallback{RESET}")
        
        if not skill_vector or len(skill_vector) < 5:
            return {
                "archetype": "explorer",
                "confidence": 0.3,
                "reasoning": "Insufficient data for analysis",
                "adjustments": {},
                "model_used": "fallback",
                "ai_source": "none",
            }
        
        iteration_velocity = skill_vector[0]
        debug_efficiency = skill_vector[1]
        craftsmanship = skill_vector[2]
        tool_fluency = skill_vector[3]
        integrity = skill_vector[4]
        
        scores = {
            "fast_iterator": iteration_velocity * 0.5 + tool_fluency * 0.3 + debug_efficiency * 0.2,
            "careful_tester": craftsmanship * 0.4 + debug_efficiency * 0.4 + integrity * 0.2,
            "debugger": debug_efficiency * 0.5 + iteration_velocity * 0.3 + tool_fluency * 0.2,
            "craftsman": craftsmanship * 0.5 + integrity * 0.3 + debug_efficiency * 0.2,
            "explorer": iteration_velocity * 0.4 + debug_efficiency * 0.3 + craftsmanship * 0.3,
        }
        
        best_archetype = max(scores, key=scores.get)
        confidence = min(scores[best_archetype], 1.0)
        
        return {
            "archetype": best_archetype,
            "confidence": round(confidence, 3),
            "reasoning": "Assigned based on mathematical skill vector analysis",
            "adjustments": scores,
            "model_used": "fallback",
            "ai_source": "none",
        }

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
            return json.loads(self._strip_markdown_json(response))
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
    # ADAPTIVE INTERVENTION - Intelligent model routing with rich context
    # =========================================================================

    async def adaptive_intervention(self, session_context: dict, error_profile: dict = None) -> dict:
        """
        Intelligently choose intervention type and model based on rich behavioral context.
        Uses user's actual code, past problems, and behavioral patterns for personalized hints.
        """
        code = session_context.get("code", "")
        last_error = session_context.get("last_error")
        error_streak = session_context.get("error_streak", 0)
        time_stuck_ms = session_context.get("time_stuck_ms", 0)
        attempt_count = session_context.get("attempt_count", 1)

        # Enhanced context from behavioral analysis
        recent_errors = session_context.get("recent_errors", [])
        error_pattern = session_context.get("error_pattern")
        repeated_same_error = session_context.get("repeated_same_error", False)
        task_description = session_context.get("task_description", "")
        intervention_reason = session_context.get("intervention_reason", "unknown")
        tests_passed_trend = session_context.get("tests_passed_trend", "stable")

        print(f"\n{BLUE}[Intervention] Evaluating... (errors: {error_streak}, stuck: {time_stuck_ms // 1000}s, reason: {intervention_reason}){RESET}")

        use_personalized = error_profile and error_profile.get("has_data", False)

        # Build rich error context for the AI
        error_context = self._build_error_context(
            last_error=last_error,
            recent_errors=recent_errors,
            error_pattern=error_pattern,
            repeated_same_error=repeated_same_error,
        )

        # Determine intervention type based on the trigger reason
        if intervention_reason == "repeated_same_error" or repeated_same_error:
            # User keeps making the same mistake - need a different approach
            hint = await self.generate_targeted_hint(
                code=code,
                error_context=error_context,
                task_description=task_description,
                attempt_count=attempt_count,
                hint_type="different_approach",
                error_profile=error_profile if use_personalized else None,
            )
            return {
                "type": "technical_hint",
                "hint": hint["hint"],
                "personalization_badge": hint.get("personalization_badge", "Trying a different approach"),
                "hint_style": hint.get("hint_style", "alternative"),
                "model_used": ["gpt-4o"],
            }

        elif error_streak >= 3 and last_error:
            # Multiple errors - provide technical analysis
            analysis = await self.analyze_code_error(code, last_error)

            if use_personalized:
                hint_result = await self.generate_personalized_hint(
                    code, error_context, attempt_count, error_profile
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
                hint = await self.generate_hint(code, error_context, attempt_count)
                return {
                    "type": "technical_hint",
                    "analysis": analysis,
                    "hint": hint,
                    "model_used": ["gpt-4o-mini", "claude-3-haiku"],
                }

        elif intervention_reason == "declining_performance" or tests_passed_trend == "declining":
            # Tests were passing but now failing - something broke
            hint = await self.generate_targeted_hint(
                code=code,
                error_context=error_context,
                task_description=task_description,
                attempt_count=attempt_count,
                hint_type="regression",
                error_profile=error_profile if use_personalized else None,
            )
            return {
                "type": "technical_hint",
                "hint": hint["hint"],
                "personalization_badge": hint.get("personalization_badge", "Something changed"),
                "hint_style": hint.get("hint_style", "diagnostic"),
                "model_used": ["gpt-4o"],
            }

        elif time_stuck_ms > 180000 or intervention_reason == "time_stuck":
            if use_personalized:
                hint_result = await self.generate_personalized_hint(
                    code,
                    error_context or "User seems stuck (no progress for 3 minutes)",
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
                    error_context or "User seems stuck (no progress for 3 minutes)",
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

        elif intervention_reason == "stuck_not_changing_code":
            # User is stuck but not typing - might be confused
            hint = await self.generate_targeted_hint(
                code=code,
                error_context=error_context,
                task_description=task_description,
                attempt_count=attempt_count,
                hint_type="getting_started",
                error_profile=error_profile if use_personalized else None,
            )
            return {
                "type": "gentle_nudge",
                "hint": hint["hint"],
                "personalization_badge": hint.get("personalization_badge", "Getting unstuck"),
                "hint_style": hint.get("hint_style", "guiding"),
                "model_used": ["gpt-4o"],
            }

        elif error_streak >= 2:
            if use_personalized:
                hint_result = await self.generate_personalized_hint(
                    code, error_context or "struggling", attempt_count, error_profile
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
                    code, error_context or "struggling", attempt_count
                )
                return {
                    "type": "gentle_nudge",
                    "hint": hint,
                    "model_used": ["claude-3-haiku"],
                }

        return {"type": "none"}

    def _build_error_context(
        self,
        last_error: str,
        recent_errors: list,
        error_pattern: str,
        repeated_same_error: bool,
    ) -> str:
        """Build a rich error context string for hint generation."""
        if not last_error and not recent_errors:
            return ""

        context_parts = []

        if last_error:
            context_parts.append(f"Current error: {last_error[:300]}")

        if repeated_same_error:
            context_parts.append("NOTE: User has been getting the SAME error repeatedly.")

        if error_pattern:
            context_parts.append(f"Error pattern detected: {error_pattern}")

        if len(recent_errors) > 1:
            context_parts.append(f"Recent errors ({len(recent_errors)}): {', '.join(e[:50] for e in recent_errors[:3])}")

        return "\n".join(context_parts)

    async def generate_targeted_hint(
        self,
        code: str,
        error_context: str,
        task_description: str,
        attempt_count: int,
        hint_type: str,
        error_profile: dict = None,
    ) -> dict:
        """
        Generate a targeted hint based on specific intervention reasons.
        Primary: Claude (via Backboard) - Best for nuanced, context-aware hints
        Fallback: Gemini (direct API) - Fast and reliable backup
        """
        print(f"\n{MAGENTA}[Hint] Generating TARGETED hint with CLAUDE (type: {hint_type}, attempt #{attempt_count}){RESET}")

        # Build system prompt based on hint type
        if hint_type == "different_approach":
            system_prompt = """You are a coding mentor helping a student who keeps making the same error.

Rules:
- They've tried the same thing multiple times without success
- Suggest a COMPLETELY DIFFERENT approach to solve the problem
- Don't just fix the syntax - help them think about it differently
- Be encouraging but direct about trying something new
- Keep it brief (2-3 sentences)
- Don't give away the full solution"""

        elif hint_type == "regression":
            system_prompt = """You are a coding mentor helping a student whose tests were passing but are now failing.

Rules:
- Something they changed broke what was working
- Help them identify what might have changed
- Suggest using version control or undo to compare
- Ask them to think about what they last modified
- Keep it brief (2-3 sentences)"""

        elif hint_type == "getting_started":
            system_prompt = """You are a coding mentor helping a student who seems stuck and isn't making changes.

Rules:
- They might be confused about where to start
- Give them a concrete first step to try
- Break the problem down into a smaller piece
- Be encouraging and help them get momentum
- Keep it brief (2-3 sentences)"""

        else:
            system_prompt = """You are an encouraging coding mentor.

Rules:
- Give a brief, helpful hint (2-3 sentences)
- Don't give away the answer
- Be specific to their code and error
- Be encouraging"""

        # Build personalization context
        personalization_badge = "Helpful hint"
        hint_style = hint_type

        if error_profile and error_profile.get("has_data"):
            dominant_category = error_profile.get("dominant_category", "logic")
            trend = error_profile.get("recent_trend", "stable")

            if trend == "improving":
                personalization_badge = f"You're making progress! (Based on your {dominant_category} patterns)"
            elif trend == "struggling":
                personalization_badge = f"Tailored for your {dominant_category} challenges"
            else:
                personalization_badge = f"Based on your coding patterns"

        user_message = f"""Task: {task_description[:500] if task_description else 'Unknown task'}

Student's current code:
```
{code[:1500]}
```

{error_context}

This is attempt #{attempt_count}. Please provide a helpful hint."""

        hint = await self._call_model(
            assistant_name=f"TargetedHintAssistant_{hint_type}",
            system_prompt=system_prompt,
            user_message=user_message,
            llm_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",  # Claude for targeted hints
            thread_key=f"targeted_hints:{self.user_id}:{hint_type}",
            use_memory=True,
        )

        return {
            "hint": hint,
            "personalization_badge": personalization_badge,
            "hint_style": hint_style,
        }

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
            llm_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",  # Claude for contextual hints
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
            rankings = json.loads(self._strip_markdown_json(response))
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
            return json.loads(self._strip_markdown_json(response))
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
