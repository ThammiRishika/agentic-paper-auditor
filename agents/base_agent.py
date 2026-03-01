import os
import time
import instructor
from pydantic import BaseModel
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)

# ── Provider configuration ────────────────────────────────────────────────────
# Set PROVIDER in .env to: "gemini" | "groq" | "local"
PROVIDER = os.environ.get("PROVIDER", "gemini").lower()

# Model defaults per provider (override with MODEL env var)
_DEFAULTS = {
    "gemini": "gemini-2.0-flash-lite",
    "groq":   "llama-3.3-70b-versatile",
    "local":  "llama-3.2-3b-instruct",
}
MODEL = os.environ.get("MODEL", _DEFAULTS.get(PROVIDER, "gemini-2.0-flash-lite"))

# Groq / LM Studio settings
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
LM_STUDIO_URL  = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")

# ── Instructor client (module-level singleton) ────────────────────────────────
_client = None


def get_client():
    global _client
    if _client is not None:
        return _client

    if PROVIDER == "groq":
        from groq import Groq
        _client = instructor.from_groq(
            Groq(api_key=GROQ_API_KEY),
            mode=instructor.Mode.JSON,
        )
        print(f"[LLM] Provider: Groq | Model: {MODEL}")

    elif PROVIDER == "local":
        from openai import OpenAI as _OpenAI
        _client = instructor.from_openai(
            _OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio"),
            mode=instructor.Mode.JSON_SCHEMA,
        )
        print(f"[LLM] Provider: LM Studio ({LM_STUDIO_URL}) | Model: {MODEL}")

    else:  # gemini (default)
        _client = instructor.from_provider(
            f"google/{MODEL}",
            api_key=os.environ["GEMINI_API_KEY"],
        )
        print(f"[LLM] Provider: Gemini | Model: {MODEL}")

    return _client


def get_llm():
    """LangChain LLM for plain-text summarization (not structured extraction)."""
    if PROVIDER == "groq":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY,
            model=MODEL,
            temperature=0.2,
        )
    elif PROVIDER == "local":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=LM_STUDIO_URL,
            api_key="lm-studio",
            model=MODEL,
            temperature=0.2,
        )
    else:  # gemini
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=MODEL,
            temperature=0.2,
            google_api_key=os.environ["GEMINI_API_KEY"],
        )


def extract_structured(prompt: str, model_class: Type[T], max_retries: int = 3) -> T:
    """
    Call the configured LLM via instructor and return a validated Pydantic model.
    Handles 429 RESOURCE_EXHAUSTED by sleeping before retrying.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            kwargs = {"model": MODEL} if PROVIDER in ("groq", "local") else {}
            return get_client().chat.completions.create(
                response_model=model_class,
                messages=[{"role": "user", "content": prompt}],
                max_retries=1,
                **kwargs,
            )
        except Exception as e:
            last_exc = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate_limit" in err_str.lower():
                import re as _re
                m = _re.search(r"(?:retryDelay.*?|try again in )(\d+)s", err_str)
                wait = int(m.group(1)) + 5 if m else 30
                print(f"[rate-limit] sleeping {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
    raise last_exc


# ── Token / chunking helpers ──────────────────────────────────────────────────

def chunk_text(text: str, max_tokens: int = 12_000) -> list[str]:
    max_chars = max_tokens * 4
    words = text.split()
    chunks, current, current_len = [], [], 0
    for word in words:
        wlen = len(word) + 1
        if current_len + wlen > max_chars:
            if current:
                chunks.append(" ".join(current))
            current, current_len = [word], len(word)
        else:
            current.append(word)
            current_len += wlen
    if current:
        chunks.append(" ".join(current))
    return chunks


def summarize_if_too_long(text: str, max_tokens: int = 12_000) -> str:
    if not text or len(text) / 4 <= max_tokens:
        return text
    llm = get_llm()
    summaries = []
    for chunk in chunk_text(text, max_tokens=8_000):
        response = llm.invoke(
            "Summarize the following section concisely. "
            "Do NOT drop formulas, key numerical results, statistical values, or unusual edge cases. "
            "Preserve all quantitative claims exactly as stated:\n\n" + chunk
        )
        summaries.append(response.content)
        time.sleep(1)
    return "\n\n".join(summaries)
