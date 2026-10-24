"""One function, three providers. Switch with LLM_PROVIDER in .env.

    LLM_PROVIDER=gemini   (free tier: GEMINI_API_KEY from aistudio.google.com)
    LLM_PROVIDER=claude   (ANTHROPIC_API_KEY from console.anthropic.com)
    LLM_PROVIDER=openai   (OPENAI_API_KEY from platform.openai.com)
    LLM_PROVIDER=mock     (no key, offline - the demo never dies)

Model names can be overridden with GEMINI_MODEL / CLAUDE_MODEL / OPENAI_MODEL.
"""
import os
import time

DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "claude": "claude-haiku-5-5",
    "openai": "gpt-4o-mini",
}
KEY_VARS = {
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def provider() -> str:
    p = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if p in KEY_VARS and not os.getenv(KEY_VARS[p]):
        return "mock"  # key missing -> fall back instead of crashing
    return p if p in KEY_VARS else "mock"


def model_name(p: str) -> str:
    return os.getenv(f"{p.upper()}_MODEL") or DEFAULT_MODELS.get(p, "mock")


RETRY_WAITS = (1, 2, 4)  # seconds; Gemini free tier is often busy (503) or rate-limited (429)


def _is_busy(e: Exception) -> bool:
    code = getattr(e, "code", None) or getattr(e, "status_code", None)
    return code in (503, 429) or any(t in str(e) for t in ("503", "429"))


def _gemini_call(client, model, contents, config):
    """Retry up to 3 times (waits 1s, 2s, 4s) on 503 / 429. Other errors are raised at once."""
    for wait in RETRY_WAITS:
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            if not _is_busy(e):
                raise
            time.sleep(wait)
    return client.models.generate_content(model=model, contents=contents, config=config)


def generate(system: str, user: str, temperature: float = 0.2) -> dict:
    """Returns {"text", "provider", "model"}."""
    p = provider()
    m = model_name(p)

    if p == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = _gemini_call(
            client,
            m,
            user,
            types.GenerateContentConfig(system_instruction=system, temperature=temperature),
        )
        text = resp.text

    elif p == "claude":
        import anthropic

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        resp = client.messages.create(
            model=m,
            max_tokens=1024,
            system=system,
            temperature=temperature,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")

    elif p == "openai":
        from openai import OpenAI

        client = OpenAI()  # reads OPENAI_API_KEY
        resp = client.chat.completions.create(
            model=m,
            temperature=temperature,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        text = resp.choices[0].message.content

    else:
        text = f"[mock answer] You asked: {user[-200:]}\n\nNot medical advice - for clinician review."

    return {"text": text, "provider": p, "model": m}
