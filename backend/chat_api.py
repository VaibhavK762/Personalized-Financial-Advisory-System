import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_MODEL = "gemini-1.5-flash"

# Configure Gemini properly
_gemini_available = False

if _GEMINI_KEY:
    try:
        genai.configure(api_key=_GEMINI_KEY)
        _gemini_available = True
        print(f"[ChatAPI] Gemini configured — model: {_GEMINI_MODEL}")
    except Exception as e:
        print(f"[ChatAPI] Gemini config failed: {e}")
else:
    print("[ChatAPI] No GEMINI_API_KEY found — fallback mode active")


# ---------------------------------------------------------------------------
# Chat Engine
# ---------------------------------------------------------------------------
class ChatCoach:
    def __init__(self):
        self.memory = {}

    def update_context(self, email: str, financials: dict):
        if email not in self.memory:
            self.memory[email] = {"history": []}
        self.memory[email]["financials"] = financials

    # ------------------------------------------------------------------
    # NEW: Context-based response (USED IN YOUR DASHBOARD)
    # ------------------------------------------------------------------
    def respond_with_context(self, user_message: str, context: dict) -> str:

        if not context:
            return "No financial data available. Please input data first."

        try:
            context_str = json.dumps(context, indent=2)

            prompt = f"""
You are an expert AI Financial Coach.

User Data:
{context_str}

User Question:
{user_message}

Rules:
- Always give helpful answer
- Use user's numbers
- Give actionable advice
- Never say "not enough data"
"""

            if _gemini_available:
                model = genai.GenerativeModel(_GEMINI_MODEL)
                response = model.generate_content(prompt)
                return response.text.strip()

            return self._fallback(context, user_message)

        except Exception as e:
            print("[ChatAPI ERROR]:", e)
            return self._fallback(context, user_message)

    # ------------------------------------------------------------------
    # FALLBACK (IMPORTANT FOR HACKATHON)
    # ------------------------------------------------------------------
    def _fallback(self, context, user_message):
        msg = user_message.lower()

        if "overview" in context:
            rev = context['overview'].get('total_revenue', 0)
            prof = context['overview'].get('total_profit', 0)

            return (
                f"💡 Based on your revenue ₹{rev:,.0f} and profit ₹{prof:,.0f}, "
                f"focus on improving operational efficiency and reducing variable costs."
            )

        if "financials" in context:
            inc = context['financials'].get('income', 0)
            sav = context['financials'].get('savings', 0)

            return (
                f"💡 You earn ₹{inc:,.0f} and save ₹{sav:,.0f}. "
                f"Try increasing savings rate by 10% via SIP."
            )

        return "⚠️ AI unavailable. Please try again."

    # ------------------------------------------------------------------
    # Legacy (not used much but safe)
    # ------------------------------------------------------------------
    def respond(self, email: str, user_message: str) -> str:
        context = self.memory.get(email, {})
        return self.respond_with_context(user_message, context)


chat_engine = ChatCoach()
