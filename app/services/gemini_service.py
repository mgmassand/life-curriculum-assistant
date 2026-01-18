"""Gemini service for AI coaching chat and roadmap generation."""

from collections.abc import AsyncGenerator
import json

import google.generativeai as genai

from app.config import get_settings

settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)

# Interest-to-Standard mappings based on strategic document
INTEREST_TO_STANDARDS = {
    "music": {
        "subjects": ["Mathematics", "Language Arts", "Physics", "History"],
        "connections": [
            "Fractions and ratios through rhythm and time signatures",
            "Poetry and lyrics analysis for language comprehension",
            "Sound waves and acoustics for physics concepts",
            "Cultural history through music evolution"
        ]
    },
    "gaming": {
        "subjects": ["Mathematics", "Computer Science", "Economics", "Strategic Thinking"],
        "connections": [
            "Probability and statistics in game mechanics",
            "Basic programming and logic concepts",
            "Resource management and economic principles",
            "Problem-solving and critical analysis"
        ]
    },
    "sports": {
        "subjects": ["Physics", "Biology", "Mathematics", "Health"],
        "connections": [
            "Motion, force, and trajectory calculations",
            "Human anatomy and physiology",
            "Statistics and performance metrics",
            "Nutrition and wellness principles"
        ]
    },
    "art": {
        "subjects": ["Mathematics", "History", "Science", "Language Arts"],
        "connections": [
            "Geometry, symmetry, and proportions",
            "Art history and cultural movements",
            "Color theory and chemistry of materials",
            "Visual storytelling and narrative"
        ]
    },
    "nature": {
        "subjects": ["Biology", "Environmental Science", "Mathematics", "Geography"],
        "connections": [
            "Ecosystems and biodiversity",
            "Climate and sustainability concepts",
            "Data collection and analysis",
            "Map reading and spatial awareness"
        ]
    },
    "technology": {
        "subjects": ["Computer Science", "Mathematics", "Engineering", "Ethics"],
        "connections": [
            "Programming fundamentals and logic",
            "Applied mathematics and algorithms",
            "Design thinking and problem-solving",
            "Digital citizenship and ethics"
        ]
    },
    "cooking": {
        "subjects": ["Chemistry", "Mathematics", "Health", "Culture"],
        "connections": [
            "Chemical reactions in cooking processes",
            "Fractions, ratios, and measurement",
            "Nutrition and food science",
            "Cultural studies through cuisine"
        ]
    },
    "animals": {
        "subjects": ["Biology", "Mathematics", "Language Arts", "Ethics"],
        "connections": [
            "Animal behavior and classification",
            "Data tracking and analysis",
            "Research and report writing",
            "Animal welfare and responsibility"
        ]
    }
}


class GeminiService:
    """Service for Google Gemini API interactions with Interest-First Education approach."""

    def __init__(self):
        """Initialize Gemini client."""
        self.model = genai.GenerativeModel(settings.gemini_model)

    def _build_system_prompt(self, child_context: dict | None = None, parent_mood: str | None = None) -> str:
        """Build comprehensive therapeutic system prompt for AI Family Coach."""

        # Determine linguistic warmth based on parent mood
        warmth_level = "balanced"
        if parent_mood:
            mood_lower = parent_mood.lower()
            if any(word in mood_lower for word in ["frustrated", "sad", "overwhelmed", "anxious", "tired", "exhausted", "worried"]):
                warmth_level = "high_empathy"
            elif any(word in mood_lower for word in ["happy", "excited", "proud", "hopeful", "good", "great"]):
                warmth_level = "celebratory"

        base_prompt = """You are the AI Family Coach within the LifeCurriculum app. Your purpose is to act as a neutral, data-informed, and emotionally supportive partner for parents navigating their child's unique educational and developmental journey.

CORE PHILOSOPHY
LifeCurriculum replaces age-based milestones with skill and exposure pathways. You view children as "talented but unskilled" and parents as "nurturers of potential." Your goal is to maximize the "Returns of Joy" while reducing parental anxiety.

SENTIMENT CALIBRATION
The parent may be on a spectrum: "Peak Joy" (child is thriving) to "Deep Frustration/Sadness" (child is not responding). Perform immediate sentiment analysis on every input and adapt your "Linguistic Warmth" accordingly.

PERSONALITY ATTRIBUTES
1. NON-JUDGMENTAL & OBJECTIVE: Act as a safe harbor for frustration
2. STRENGTHS-BASED: Always highlight what the family is doing well BEFORE addressing friction
3. DEVELOPMENTAL INTELLIGENCE: Use age-appropriate context (5-10y, 11-15y, 15+). Shift perspective from "defiance" to "developmental milestone"
4. COGNITIVE EMPATHY: Identify emotional states (exhaustion, joy, guilt) and mirror with empathy while remaining stable and professional

THE 5-STEP THERAPEUTIC LOOP
For EVERY interaction, move through these phases:

**Phase 1 - Exploration & Opening**: Understand the "what" and "why"
**Phase 2 - Emotional Processing**: Dig into internal reactions and "the story the parent is telling themselves"
**Phase 3 - Relational Dynamics**: See how the child's lack of engagement affects the home "system." Spot the "Four Horsemen" (criticism, contempt, defensiveness, stonewalling)
**Phase 4 - Resilience & Strengths**: Remind the parent of past wins and existing resources
**Phase 5 - Action & Grounding**: Identify ONE tiny, tangible next step

QUESTION BANK (Use dynamically)

CATEGORY 1 - EXPLORATION & OPENING:
- "What brought this to your mind today?" -> Follow-up: "What made today the right time to address it?"
- "How would you describe your current mood in three words?" -> Follow-up: "Which of those words feels the most heavy right now?"
- "What is the most significant challenge you're facing this week?" -> Follow-up: "If that challenge were gone tomorrow, what would be the first thing you'd notice?"

CATEGORY 2 - EMOTIONAL PROCESSING:
- "Where in your body do you feel that stress or tension?" -> Follow-up: "If that tension had a voice, what would it be trying to tell you?"
- "What is the story you are telling yourself about this situation?" -> Follow-up: "Is that story based on facts, or on a fear of what might happen?"

CATEGORY 3 - RELATIONSHIPS & FAMILY DYNAMICS:
- "If I asked your partner/child how you are doing, what would they say?" -> Follow-up: "How does their perspective differ from your own?"
- "What does a 'perfect' day of connection look like for your family?" -> Follow-up: "What is one tiny piece of that day we can implement this week?"

CATEGORY 4 - STRENGTHS & RESILIENCE:
- "What is a challenge you've overcome in the past that surprised you?" -> Follow-up: "What strengths did you use then that you could use now?"
- "What is a small win you've had in the last 48 hours?" -> Follow-up: "How did you contribute to making that win happen?"

CATEGORY 5 - ACTION & CLOSING:
- "If we could only focus on one thing this week, what should it be?" -> Follow-up: "Why does that feel like the priority right now?"
- "On a scale of 1-10, how confident do you feel about [Goal]?" -> Follow-up: "What would it take to move that number up by just one point?"

CRITICAL CONSTRAINTS
- NEVER give "generic" advice - always personalize
- ALWAYS ask a follow-up question
- If a parent is "Sad/Frustrated," DO NOT jump to solutions. Use Reflective Listening first.
- If a parent is "Happy," celebrate the "Win" and help them document the "Curriculum Milestone"
- Keep responses warm, conversational, and focused

"""

        # Add warmth-specific instructions
        if warmth_level == "high_empathy":
            base_prompt += """
CURRENT MODE: HIGH EMPATHY
The parent appears stressed, frustrated, or overwhelmed.
- Lead with validation: "That sounds really hard" or "It makes complete sense you'd feel that way"
- DO NOT offer solutions until emotions are fully processed
- Use Category 2 questions first (Emotional Processing)
- Mirror their feelings before moving forward
"""
        elif warmth_level == "celebratory":
            base_prompt += """
CURRENT MODE: CELEBRATORY
The parent appears happy, proud, or excited.
- Match their energy with enthusiasm!
- Help them capture this WIN for their family's journey
- Use Category 4 questions (Strengths & Resilience)
- Ask what made this success possible so they can replicate it
"""

        if child_context:
            base_prompt += f"""

CHILD'S DIGITAL TWIN PROFILE
Name: {child_context.get('name', 'the child')}
Age: {child_context.get('age_description', 'not specified')}
Known Interests: {child_context.get('interests', 'not yet discovered')}
Recent Milestones: {child_context.get('recent_milestones', 'none recorded')}
Current Focus Areas: {child_context.get('focus_areas', 'general development')}

Use this profile to personalize all advice. Reference the child by name and connect suggestions to their specific interests.
"""
        return base_prompt

    async def stream_chat_response(
        self,
        messages: list[dict],
        child_context: dict | None = None,
        parent_mood: str | None = None,
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response for real-time display with mood-adaptive warmth."""
        system_prompt = self._build_system_prompt(child_context, parent_mood)

        # Build conversation history for Gemini
        # Gemini uses a different format - we need to combine system prompt with first user message
        chat_history = []

        for i, msg in enumerate(messages):
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]

            # Add system prompt to the first user message
            if i == 0 and role == "user":
                content = f"{system_prompt}\n\nUser message: {content}"

            chat_history.append({
                "role": role,
                "parts": [content]
            })

        try:
            # Use generate_content with streaming
            chat = self.model.start_chat(history=chat_history[:-1] if len(chat_history) > 1 else [])

            # Get the last message to send
            last_message = chat_history[-1]["parts"][0] if chat_history else ""

            response = chat.send_message(last_message, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"\n\n[Error: {str(e)}. Please try again.]"

    async def get_chat_response(
        self,
        messages: list[dict],
        child_context: dict | None = None,
        parent_mood: str | None = None,
    ) -> tuple[str, int]:
        """Get complete response (non-streaming) with mood-adaptive warmth."""
        system_prompt = self._build_system_prompt(child_context, parent_mood)

        # Build conversation for Gemini
        chat_history = []

        for i, msg in enumerate(messages):
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]

            if i == 0 and role == "user":
                content = f"{system_prompt}\n\nUser message: {content}"

            chat_history.append({
                "role": role,
                "parts": [content]
            })

        chat = self.model.start_chat(history=chat_history[:-1] if len(chat_history) > 1 else [])
        last_message = chat_history[-1]["parts"][0] if chat_history else ""

        response = chat.send_message(last_message)

        content = response.text if response.text else ""
        # Gemini doesn't provide token counts in the same way
        tokens = 0

        return content, tokens

    async def generate_12_week_roadmap(
        self,
        child_name: str,
        age: str,
        interests: list[str],
        current_challenges: str | None = None,
    ) -> dict:
        """Generate a personalized 12-week Interest-to-Standard roadmap."""

        # Map specific interests to categories and build connections
        interest_category_map = {
            "soccer": "sports", "football": "sports", "basketball": "sports",
            "baseball": "sports", "tennis": "sports", "swimming": "sports",
            "gymnastics": "sports", "dance": "sports", "martial arts": "sports",
            "piano": "music", "guitar": "music", "singing": "music", "drums": "music",
            "minecraft": "gaming", "roblox": "gaming", "fortnite": "gaming",
            "drawing": "art", "painting": "art", "sculpting": "art",
            "coding": "technology", "robots": "technology", "computers": "technology",
            "hiking": "nature", "gardening": "nature", "camping": "nature",
            "baking": "cooking", "dogs": "animals", "cats": "animals", "horses": "animals"
        }

        # Build interest connections with specific interest names preserved
        interest_connections = []
        processed_interests = []
        for interest in interests:
            interest_lower = interest.lower()
            category = interest_category_map.get(interest_lower, interest_lower)

            if category in INTEREST_TO_STANDARDS:
                data = INTEREST_TO_STANDARDS[category]
                interest_connections.append({
                    "specific_interest": interest,
                    "category": category,
                    "subjects": data["subjects"],
                    "connections": data["connections"]
                })
                processed_interests.append(interest)
            else:
                processed_interests.append(interest)
                interest_connections.append({
                    "specific_interest": interest,
                    "category": interest,
                    "subjects": ["Language Arts", "Science", "Mathematics", "Social Studies"],
                    "connections": ["Creative exploration", "Research skills", "Critical thinking"]
                })

        # Build explicit week assignment
        num_interests = len(processed_interests)
        week_assignments = []
        for i in range(12):
            assigned_interest = processed_interests[i % num_interests] if num_interests > 0 else "general"
            week_assignments.append(f"Week {i+1}: {assigned_interest}")

        prompt = f"""Create a personalized 12-week learning roadmap for:
- Child: {child_name}
- Age: {age}
- SELECTED INTERESTS (USE ONLY THESE): {', '.join(processed_interests)}
{f'- Current Challenges: {current_challenges}' if current_challenges else ''}

CRITICAL INSTRUCTIONS:
1. You MUST ONLY use the interests listed above: {', '.join(processed_interests)}
2. DO NOT introduce any other interests like gaming, technology, etc. unless explicitly listed above
3. Each week's "interest_focus" field MUST be one of: {', '.join(processed_interests)}
4. Distribute the 12 weeks evenly across the {num_interests} selected interest(s)
5. All activities must directly relate to the selected interests

Suggested Week Distribution:
{chr(10).join(week_assignments)}

Interest-to-Academic Connections for the SELECTED interests:
{json.dumps(interest_connections, indent=2)}

Generate a structured 12-week roadmap in JSON format with:
{{
    "title": "Personalized roadmap title mentioning the specific interests",
    "overview": "Brief description mentioning {', '.join(processed_interests)} specifically",
    "weeks": [
        {{
            "week": 1,
            "theme": "Weekly theme connecting the assigned interest to learning",
            "interest_focus": "MUST be one of: {', '.join(processed_interests)}",
            "academic_connections": ["Subject 1", "Subject 2"],
            "activities": [
                {{
                    "name": "Activity name related to the assigned interest",
                    "description": "What to do - must relate to the assigned interest",
                    "duration": "15-30 minutes",
                    "materials": ["item1", "item2"]
                }}
            ],
            "milestone": "What success looks like this week"
        }}
    ],
    "parent_tips": ["Tip 1", "Tip 2", "Tip 3"]
}}

REMINDER: Only use {', '.join(processed_interests)}. Do NOT include any other interests.
Make it practical, fun, and clearly connected to academic standards while feeling like play, not schoolwork.

IMPORTANT: Return ONLY valid JSON, no markdown formatting or code blocks."""

        try:
            response = self.model.generate_content(prompt)

            content = response.text if response.text else "{}"
            # Clean up any markdown formatting if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to generate roadmap"}
        except Exception as e:
            return {"error": f"Failed to generate roadmap: {str(e)}"}

    async def analyze_interests(self, quiz_responses: list[dict]) -> dict:
        """Analyze interest quiz responses to identify primary interests."""

        prompt = f"""Analyze these quiz responses to identify a child's primary interests:

{json.dumps(quiz_responses, indent=2)}

Return a JSON analysis with:
{{
    "primary_interests": ["Top 3 interests identified"],
    "interest_scores": {{"interest_name": score_0_to_100}},
    "learning_style": "Visual/Auditory/Kinesthetic/Reading-Writing",
    "recommended_approaches": ["Approach 1", "Approach 2"],
    "interest_to_standard_opportunities": [
        {{
            "interest": "interest_name",
            "academic_subject": "subject",
            "connection_example": "How they connect"
        }}
    ],
    "parent_insight": "One key insight for the parent about their child's learning profile"
}}

IMPORTANT: Return ONLY valid JSON, no markdown formatting or code blocks."""

        try:
            response = self.model.generate_content(prompt)

            content = response.text if response.text else "{}"
            # Clean up any markdown formatting if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to analyze interests"}
        except Exception as e:
            return {"error": f"Failed to analyze interests: {str(e)}"}


# Singleton instance
_gemini_service: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    """Get Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


# Backward compatibility alias
def get_openai_service() -> GeminiService:
    """Backward compatibility alias for get_gemini_service."""
    return get_gemini_service()
