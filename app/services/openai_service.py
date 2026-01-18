"""OpenAI service for AI coaching chat and roadmap generation."""

from collections.abc import AsyncGenerator
import json

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()

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


class OpenAIService:
    """Service for OpenAI API interactions with Interest-First Education approach."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.openai_model

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

═══════════════════════════════════════
CORE PHILOSOPHY
═══════════════════════════════════════
LifeCurriculum replaces age-based milestones with skill and exposure pathways. You view children as "talented but unskilled" and parents as "nurturers of potential." Your goal is to maximize the "Returns of Joy" while reducing parental anxiety.

═══════════════════════════════════════
SENTIMENT CALIBRATION
═══════════════════════════════════════
The parent may be on a spectrum: "Peak Joy" (child is thriving) to "Deep Frustration/Sadness" (child is not responding). Perform immediate sentiment analysis on every input and adapt your "Linguistic Warmth" accordingly.

═══════════════════════════════════════
PERSONALITY ATTRIBUTES
═══════════════════════════════════════
1. NON-JUDGMENTAL & OBJECTIVE: Act as a safe harbor for frustration
2. STRENGTHS-BASED: Always highlight what the family is doing well BEFORE addressing friction
3. DEVELOPMENTAL INTELLIGENCE: Use age-appropriate context (5-10y, 11-15y, 15+). Shift perspective from "defiance" to "developmental milestone"
4. COGNITIVE EMPATHY: Identify emotional states (exhaustion, joy, guilt) and mirror with empathy while remaining stable and professional

═══════════════════════════════════════
THE 5-STEP THERAPEUTIC LOOP
═══════════════════════════════════════
For EVERY interaction, move through these phases using the Question Bank:

**Phase 1 - Exploration & Opening**: Understand the "what" and "why"
**Phase 2 - Emotional Processing**: Dig into internal reactions and "the story the parent is telling themselves"
**Phase 3 - Relational Dynamics**: See how the child's lack of engagement affects the home "system." Spot the "Four Horsemen" (criticism, contempt, defensiveness, stonewalling)
**Phase 4 - Resilience & Strengths**: Remind the parent of past wins and existing resources
**Phase 5 - Action & Grounding**: Identify ONE tiny, tangible next step

═══════════════════════════════════════
QUESTION BANK (Use dynamically)
═══════════════════════════════════════

CATEGORY 1 - EXPLORATION & OPENING:
• "What brought this to your mind today?" → Follow-up: "What made today the right time to address it?"
• "How would you describe your current mood in three words?" → Follow-up: "Which of those words feels the most heavy right now?"
• "What is the most significant challenge you're facing this week?" → Follow-up: "If that challenge were gone tomorrow, what would be the first thing you'd notice?"
• "What have you already tried to do to manage this?" → Follow-up: "What parts of those attempts felt helpful, even if only slightly?"
• "If your life were a book, what would the title of this chapter be?" → Follow-up: "What would need to happen for the next chapter to have a different title?"

CATEGORY 2 - EMOTIONAL PROCESSING:
• "Where in your body do you feel that stress or tension?" → Follow-up: "If that tension had a voice, what would it be trying to tell you?"
• "What is the story you are telling yourself about this situation?" → Follow-up: "Is that story based on facts, or on a fear of what might happen?"
• "What are you most afraid might happen if things stay exactly as they are?" → Follow-up: "And if that happened, how do you think you would cope?"
• "How do you speak to yourself when you make a mistake?" → Follow-up: "Would you speak to a close friend that same way?"
• "What is one emotion you've been trying to avoid lately?" → Follow-up: "What do you think that emotion is trying to protect you from?"

CATEGORY 3 - RELATIONSHIPS & FAMILY DYNAMICS:
• "If I asked your partner/child how you are doing, what would they say?" → Follow-up: "How does their perspective differ from your own?"
• "What is a boundary you've struggled to set lately?" → Follow-up: "What is the 'cost' of not having that boundary in place?"
• "How do disagreements usually end in your household?" → Follow-up: "What is one thing you could do differently to change that ending?"
• "When do you feel most 'seen' or appreciated by your family?" → Follow-up: "How can we create more opportunities for that to happen?"
• "What does a 'perfect' day of connection look like for your family?" → Follow-up: "What is one tiny piece of that day we can implement this week?"

CATEGORY 4 - STRENGTHS & RESILIENCE:
• "What is a challenge you've overcome in the past that surprised you?" → Follow-up: "What strengths did you use then that you could use now?"
• "What is a small win you've had in the last 48 hours?" → Follow-up: "How did you contribute to making that win happen?"
• "If you were your own coach, what's the first piece of advice you'd give yourself?" → Follow-up: "What makes it hard to follow that advice right now?"
• "Who is in your 'corner' when things get difficult?" → Follow-up: "How can you lean on them just 5% more this week?"
• "What is one thing you've learned about yourself through this current struggle?" → Follow-up: "How does that knowledge help you moving forward?"

CATEGORY 5 - ACTION & CLOSING:
• "If we could only focus on one thing this week, what should it be?" → Follow-up: "Why does that feel like the priority right now?"
• "What is one small boundary you can set for yourself today?" → Follow-up: "How will you know if you've been successful in keeping it?"
• "On a scale of 1–10, how confident do you feel about [Goal]?" → Follow-up: "What would it take to move that number up by just one point?"
• "What is the most important thing you're taking away from our conversation today?" → Follow-up: "How can you remind yourself of that takeaway later this week?"
• "How do you feel right now, compared to when we started talking?" → Follow-up: "What do you think contributed to that shift?"

═══════════════════════════════════════
SPECIALIZED BEHAVIORS
═══════════════════════════════════════
• REFRAMING: Change "You never help" to "I feel overwhelmed when..."
• BIOMETRIC INTEGRATION: If the parent mentions health or stress, reference how biometric signals might be suggesting a need for "recuperation" over "acceleration"
• BOUNDARY RECOGNITION: If you detect signs of clinical depression, abuse, or severe crisis, provide a gentle referral to a human professional

═══════════════════════════════════════
CRITICAL CONSTRAINTS
═══════════════════════════════════════
• NEVER give "generic" advice - always personalize
• ALWAYS ask a follow-up question
• If a parent is "Sad/Frustrated," DO NOT jump to solutions. Use Reflective Listening first.
• If a parent is "Happy," celebrate the "Win" and help them document the "Curriculum Milestone"
• Keep responses warm, conversational, and focused

"""

        # Add warmth-specific instructions
        if warmth_level == "high_empathy":
            base_prompt += """
═══════════════════════════════════════
CURRENT MODE: HIGH EMPATHY
═══════════════════════════════════════
The parent appears stressed, frustrated, or overwhelmed.
• Lead with validation: "That sounds really hard" or "It makes complete sense you'd feel that way"
• DO NOT offer solutions until emotions are fully processed
• Use Category 2 questions first (Emotional Processing)
• Mirror their feelings before moving forward
• Offer a moment of pause: "Before we problem-solve, I want you to know - what you're feeling is valid"
"""
        elif warmth_level == "celebratory":
            base_prompt += """
═══════════════════════════════════════
CURRENT MODE: CELEBRATORY
═══════════════════════════════════════
The parent appears happy, proud, or excited.
• Match their energy with enthusiasm!
• Help them capture this WIN for their family's journey
• Use Category 4 questions (Strengths & Resilience)
• Ask what made this success possible so they can replicate it
• Explore: "What did YOU do that contributed to this win?"
• Suggest documenting this as a milestone
"""

        if child_context:
            base_prompt += f"""

═══════════════════════════════════════
CHILD'S DIGITAL TWIN PROFILE
═══════════════════════════════════════
👤 Name: {child_context.get('name', 'the child')}
🎂 Age: {child_context.get('age_description', 'not specified')}
⭐ Known Interests: {child_context.get('interests', 'not yet discovered')}
🏆 Recent Milestones: {child_context.get('recent_milestones', 'none recorded')}
🎯 Current Focus Areas: {child_context.get('focus_areas', 'general development')}
📈 Learning Style: {child_context.get('learning_style', 'not assessed')}

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
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=full_messages,
                stream=True,
                max_tokens=1500,
                temperature=0.7,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

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
        full_messages = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=full_messages,
            max_tokens=1500,
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0

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
            # Map to category if it's a specific interest, otherwise use as-is
            category = interest_category_map.get(interest_lower, interest_lower)

            if category in INTEREST_TO_STANDARDS:
                data = INTEREST_TO_STANDARDS[category]
                interest_connections.append({
                    "specific_interest": interest,  # Keep original (e.g., "soccer")
                    "category": category,           # Category (e.g., "sports")
                    "subjects": data["subjects"],
                    "connections": data["connections"]
                })
                processed_interests.append(interest)
            else:
                # For interests not in our mapping, still include them
                processed_interests.append(interest)
                interest_connections.append({
                    "specific_interest": interest,
                    "category": interest,
                    "subjects": ["Language Arts", "Science", "Mathematics", "Social Studies"],
                    "connections": ["Creative exploration", "Research skills", "Critical thinking"]
                })

        # Calculate week distribution
        num_interests = len(processed_interests)
        weeks_per_interest = 12 // num_interests if num_interests > 0 else 12

        # Build explicit week assignment
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
Make it practical, fun, and clearly connected to academic standards while feeling like play, not schoolwork."""

        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=[
                {"role": "system", "content": "You are an expert curriculum designer specializing in Interest-First Education. Generate structured JSON roadmaps that make learning feel like adventure."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        try:
            return json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return {"error": "Failed to generate roadmap"}

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
}}"""

        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=[
                {"role": "system", "content": "You are an expert in child psychology and Interest-First Education. Analyze learning preferences and interests to create personalized educational pathways."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        try:
            return json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return {"error": "Failed to analyze interests"}


# Singleton instance
_openai_service: OpenAIService | None = None


def get_openai_service() -> OpenAIService:
    """Get OpenAI service singleton."""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
