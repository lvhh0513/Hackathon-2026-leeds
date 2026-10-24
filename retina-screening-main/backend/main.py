"""Hackathon starter API (FastAPI).
Run:  uvicorn main:app --reload --port 8000
Switch AI provider in .env: LLM_PROVIDER=gemini | claude | openai | mock
"""
import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

import llm  # noqa: E402  (after load_dotenv so it sees the keys)

app = FastAPI(title="AI in Healthcare Hackathon API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).parent / "data" / "synthetic_patients.json"
SYSTEM_PROMPT = (
    "You are a clinical decision-SUPPORT assistant for a hackathon demo. "
    "You never give a diagnosis. You summarise, flag risks and suggest questions "
    "a clinician might ask. Always end with: 'Not medical advice - for clinician review.' "
    "All data you see is synthetic."
)


class AskRequest(BaseModel):
    question: str
    patient_id: str | None = None


@app.get("/health")
def health():
    p = llm.provider()
    return {"ok": True, "provider": p, "model": llm.model_name(p)}


@app.get("/patients")
def patients():
    if not DATA_FILE.exists():
        raise HTTPException(404, "Run: python generate_synthetic.py")
    return json.loads(DATA_FILE.read_text())


@app.post("/ask")
def ask(req: AskRequest):
    context = ""
    if req.patient_id and DATA_FILE.exists():
        for p in json.loads(DATA_FILE.read_text()):
            if p["id"] == req.patient_id:
                context = f"Synthetic patient record:\n{json.dumps(p, indent=2)}\n\n"

    try:
        out = llm.generate(SYSTEM_PROMPT, context + req.question)
    except Exception as e:
        raise HTTPException(502, f"LLM error ({llm.provider()}): {e}")

    return {"answer": out["text"], "provider": out["provider"], "model": out["model"]}
