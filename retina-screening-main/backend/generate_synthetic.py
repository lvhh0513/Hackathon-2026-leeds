"""Generate a small synthetic patient set (no real data, no PII).
Run: python generate_synthetic.py [n]
"""
import json
import random
import sys
from pathlib import Path

random.seed(42)  # reproducible = transparent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50

CONDITIONS = ["hypertension", "type 2 diabetes", "asthma", "COPD", "atrial fibrillation", "none"]
MEDS = {
    "hypertension": ["amlodipine", "ramipril"],
    "type 2 diabetes": ["metformin"],
    "asthma": ["salbutamol inhaler"],
    "COPD": ["tiotropium"],
    "atrial fibrillation": ["apixaban"],
    "none": [],
}
PATHWAY = ["referral", "pre-op assessment", "surgery", "post-op ward", "discharge", "follow-up"]

patients = []
for i in range(N):
    cond = random.choice(CONDITIONS)
    patients.append({
        "id": f"SYN-{i:04d}",
        "age_band": random.choice(["18-30", "31-45", "46-60", "61-75", "76+"]),
        "sex": random.choice(["F", "M"]),
        "condition": cond,
        "medications": MEDS[cond],
        "pathway_stage": random.choice(PATHWAY),
        "heart_rate": random.randint(55, 115),
        "systolic_bp": random.randint(100, 170),
        "spo2": random.randint(89, 100),
        "days_waiting": random.randint(0, 180),
        "synthetic": True,
    })

out = Path(__file__).parent / "data" / "synthetic_patients.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(patients, indent=2))
print(f"Wrote {N} synthetic patients -> {out}")
