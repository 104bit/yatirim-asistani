import os
from typing import Optional

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Try to use Google Generative AI (Gemini)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

# Environment variable for API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

def get_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0.3):
    """
    Returns an LLM instance.
    Uses Google Gemini if API key is available, otherwise returns None (mock mode).
    """
    if HAS_GOOGLE and GOOGLE_API_KEY:
        print(f"[LLM Client] Using model: {model_name}")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GOOGLE_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True
        )
    else:
        print("[LLM Client] No API key found. Running in MOCK mode.")
        return None

def call_llm(system_prompt: str, user_prompt: str, llm=None) -> str:
    """
    Calls the LLM with the given prompts.
    If LLM is None (mock mode), returns a placeholder response.
    """
    if llm is None:
        # Mock response for testing without API key
        return """
{
    "action": "HOLD",
    "confidence": 0.7,
    "reasoning": "Mock response: Price change is minimal, news sentiment is mixed. Recommend holding position.",
    "timeframe": "SHORT_TERM"
}
"""
    
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        print(f"[LLM Client] Error calling LLM: {e}")
        return """
{
    "action": "HOLD",
    "confidence": 0.5,
    "reasoning": "Error occurred during LLM call. Defaulting to HOLD.",
    "timeframe": "SHORT_TERM",
    "risk_level": "MEDIUM"
}
"""
