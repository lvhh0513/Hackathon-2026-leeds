# CLAUDE.md — AI in Healthcare Hackathon (Leeds, 24–25 Oct 2026)

## Language rules (important)
- **Talk to me (Chemis) in Japanese** in the chat: explanations, plans, questions.
- **Write everything teammates or judges may see in English**, always:
  - code, code comments, variable names
  - commit messages and PR descriptions
  - README.md, files in `docs/`, `CLAUDE.md` itself
  - UI text, error messages, pitch notes
- When you show me English text meant for the team, add a short Japanese gloss in the chat (not in the file) if it helps me check the meaning.
- Use plain, simple English. Short sentences. Teammates are busy; judges are clinicians, not engineers.

## The hackathon
- Teams of 4: 1 medical student (brings the clinical problem) + 3 builders.
- **Build ends Sun 25 Oct 11:30.** Code freeze target: Sun 09:00. Pitch: 4 min + 2 min Q&A.
- Judging: Creativity & innovation · Technical sophistication (build, data, use of AI) · Impact (safe, feasible, real healthcare value) · Design & UX (clear, usable, accessible).
- Special award (£300, judged separately): most responsible use of data — Privacy, Security, Fairness, Transparency.

## Hard rules
- **Public or synthetic data only.** Never invent "real" patients or ask for real records.
- No PII: use age bands, IDs like `SYN-0001`, no names or dates of birth.
- The product gives **decision support, not diagnosis**. Keep the "Not medical advice — for clinician review" wording in AI output and UI.
- **Never put API keys in code or commit `.env`.** Keys live in `backend/.env` only.
- Do not set `ANTHROPIC_API_KEY` in the shell (Claude Code would bill the API instead of my Pro plan).

## Stack (starter)
- `backend/`: FastAPI. `llm.py` switches AI with `LLM_PROVIDER=gemini|claude|openai|mock` in `.env`. Falls back to mock if a key is missing — keep that behaviour so the demo never dies.
- `frontend/`: React + Vite. `/api/*` is proxied to `localhost:8000`. (I know Vue.js better than React; if we switch to Vue, keep the same API.)
- `backend/generate_synthetic.py`: synthetic patients, fixed seed for reproducibility.
- API docs live in `docs/api.md` (create it when the problem is decided). Frontend and backend follow it.

## How to work with me
- One feature per request. Show a short plan first for anything big.
- Keep changes small and easy to review. Explain what changed in Japanese.
- Prefer simple, working code over clever code. We have 24 hours.
- Accessibility by default: large text, good contrast, labels on inputs, keyboard focus visible.
- After a change, tell me how to test it (URL, command, or what to click).

## Problem
- Who struggles: people with diabetes who cannot easily reach an eye specialist, and the nurses or GPs who take their retina photos. Diabetic retinopathy (DR) can cause blindness, and early stages have no symptoms.
- When / how often: at every yearly diabetic eye screening. Specialists are few, so photos wait in a queue, and poor photos are only found late.
- What we build: we help screening staff to catch bad photos and risky cases early by adding a safety layer in front of an existing DR grading model: a photo quality check ("please retake"), an uncertainty flag ("clinician review"), and a provisional referral suggestion.
- Data source: public retina photos only (for example the test images in the model repo, IDRiD, APTOS). No real patient data. Test photos are degraded on the computer to study how the model fails.

## Our app (retina_app/)
- Streamlit app. Flow: upload photo -> quality gate -> model grade (5 levels) -> uncertain / retake / result -> optional GP referral letter draft (English, via `backend/llm.py`).
- The classifier (Branch-A v1 ONNX) is NOT ours. It comes from NetraSetu (team "Game Of Codes", Smart India Hackathon 2026). Always credit it. Our work is the quality gate, the uncertainty and referral logic, the UI and the safety experiments (`docs/safety-experiments.md`).
- Never show "no referral" as an all-clear. A clinician decides. Decision support, not diagnosis.
- Open decisions for the clinical lead: referral probability cut-off (now 0.5, provisional) and minimum sharpness (15 or 20).
- Not tested yet: mild DR that looks normal after the photo gets worse.
- Run: `streamlit run retina_app/retina_app.py` -> http://localhost:8501
