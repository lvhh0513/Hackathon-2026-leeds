"""Test the AI provider set in .env with one real call.
Run: python check_keys.py            (tests LLM_PROVIDER)
     python check_keys.py all        (tests every provider that has a key)
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()
import llm  # noqa: E402

targets = list(llm.KEY_VARS) if (len(sys.argv) > 1 and sys.argv[1] == "all") else [os.getenv("LLM_PROVIDER", "mock")]

for p in targets:
    if p not in llm.KEY_VARS:
        print(f"{p}: mock mode (no API call)")
        continue
    if not os.getenv(llm.KEY_VARS[p]):
        print(f"{p}: SKIP - {llm.KEY_VARS[p]} is empty")
        continue
    os.environ["LLM_PROVIDER"] = p
    try:
        out = llm.generate("Reply with exactly: OK", "Say OK", temperature=0)
        print(f"{p}: OK  (model {out['model']}) -> {out['text'].strip()[:40]}")
    except Exception as e:
        print(f"{p}: FAIL - {e}")
