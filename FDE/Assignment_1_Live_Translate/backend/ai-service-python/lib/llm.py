"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is your choice. The default example below is Anthropic Claude
(`pip install anthropic`, set ANTHROPIC_API_KEY). Hamza's launched version
used Google Gemini — either is fine. Whatever you pick:

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

from anthropic import AsyncAnthropic

MODEL_DEFAULT = os.getenv("MODEL", "claude-sonnet-4-6")

# One reusable async client, built lazily on first use so the service can boot
# (and answer /health) before a key is present. Reads ANTHROPIC_API_KEY from the
# environment (loaded from .env by app.py). Never hard-code the key here.
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()  # raises loudly if ANTHROPIC_API_KEY is unset
    return _client

_SYSTEM_PROMPT = (
    "You are a professional translator specializing in NATURAL, colloquial "
    "MEXICAN Spanish (es-MX) — the register spoken in Mexico, NOT Castilian/"
    "Spain Spanish and NOT generic 'neutral' Spanish. Translate the user's "
    "English text into Mexican Spanish and return ONLY the translation.\n"
    "Rules:\n"
    "- Output the translation and nothing else: no preamble, no explanations, "
    "no wrapping quotes, no notes.\n"
    "- Preserve numbers, prices (e.g. $1,299.00), URLs, emails, and product/"
    "model/SKU codes exactly as written — do not translate or reformat them.\n"
    "- Use Mexican vocabulary and phrasing (e.g. 'carro', 'computadora', "
    "'jugo', 'platicar') where it reads more natural to a Mexican reader.\n"
    "- If the input is already Spanish or has no translatable content (only "
    "numbers/symbols), return it unchanged."
)


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default).

    Fails loud: any provider/SDK error propagates so the caller returns a 502.
    We deliberately do NOT catch and return the original text — a silent
    English-passthrough fallback is an automatic fail on this assignment.
    """
    msg = await _get_client().messages.create(
        model=model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    # Concatenate any text blocks the model returns, then strip stray quotes
    # and whitespace it may have added around the translation.
    out = "".join(block.text for block in msg.content if block.type == "text")
    return out.strip().strip('"').strip("'").strip()
