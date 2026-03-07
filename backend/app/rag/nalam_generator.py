import json
from typing import Any, Dict, Optional

import google.generativeai as genai

from ..config import get_settings


settings = get_settings()


class NalamGenerator:
    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash"):
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is required")
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(model_name)

    def generate_response(
        self,
        context: str,
        user_question: str,
        risk_profile: Optional[Dict[str, Any]] = None,
        structured_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates response using optional structured context, optional retrieved context,
        and optional risk profile.
        """
        if not context and not structured_context and not risk_profile:
            return (
                "I do not have enough context to answer this yet. "
                "Please provide more medical and lifestyle details."
            )

        risk_str = "None"
        if risk_profile:
            risk_str = "\n".join(
                [f"- {k.replace('_', ' ').title()}: {v}" for k, v in risk_profile.items()]
            )

        structured_str = "None"
        if structured_context:
            try:
                structured_str = json.dumps(
                    structured_context, indent=2, ensure_ascii=False
                )
            except Exception:
                structured_str = str(structured_context)

        prompt = f"""
You are "Nalam", an expert clinical nutritionist AI.

=========================================
USER HEALTH PROFILE (RISK FLAGS, IF AVAILABLE):
{risk_str}
=========================================

=========================================
STRUCTURED USER CONTEXT (PROFILE, MACROS, ETC):
{structured_str}
=========================================

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION:
{user_question}

INSTRUCTIONS:
1. Answer using the STRUCTURED USER CONTEXT and KNOWLEDGE BASE CONTEXT.
2. PERSONALIZATION: Adapt advice based on the USER HEALTH PROFILE.
3. If meal-wise macro targets are present, use them when asked about meal limits.
4. If the user asks for a recipe that is risky for their profile, suggest a safer alternative.
5. If the user asks for a food recommendation, suggest foods that are safe for their profile.
6. Do not mention knowledge base or internal sources; just answer directly.
7. If user explicitly asks for medical advice or medicine changes, say you cannot give medical advice and ask them to consult a doctor.
8. Keep explanations concise but clear, in simple English suitable for South Indian users.
9. Ignore small talk (like “how are you”) and redirect to nutrition and diabetes topics.

ANSWER:
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {e}"

