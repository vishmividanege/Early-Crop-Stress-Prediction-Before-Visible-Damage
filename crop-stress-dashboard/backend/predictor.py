from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import torch
import time

from predictor import Predictor, prob_to_risk

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load model ONCE
predictor = Predictor()

def build_dummy_6ch(size=224):
    """
    MVP: fake satellite patch (random).
    Replace later with real satellite pipeline.
    """
    rgb = np.random.randint(0, 256, (size, size, 3), dtype=np.uint8).astype(np.float32) / 255.0
    ndvi = np.clip(np.random.normal(0.55, 0.12, (size, size)), 0, 1).astype(np.float32)
    vh   = np.clip(np.random.normal(0.45, 0.12, (size, size)), 0, 1).astype(np.float32)
    vv   = np.clip(np.random.normal(0.55, 0.10, (size, size)), 0, 1).astype(np.float32)

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    x = np.stack([r, g, b, ndvi, vh, vv], axis=0)  # [6,H,W]
    return torch.from_numpy(x).unsqueeze(0)        # [1,6,H,W]

@app.post("/predict")
def predict(payload: dict):
    """
    payload includes boundary + crop info (accepted).
    Currently uses dummy data; later use polygon to fetch Sentinel.
    """

    # ⏱ timing (optional — keep for testing)
    t0 = time.time()
    x = build_dummy_6ch(224)
    t1 = time.time()

    # ✅ Set correct stress class index
    # Try 0 first. If results wrong, change to 1.
    stress_prob = predictor.predict_stress_prob(x, stress_class_index=0)
    t2 = time.time()

    risk = prob_to_risk(stress_prob)

    actions = {
        "High": ["Check irrigation within 24–48h", "Inspect pests/disease in high-risk zones", "Check nutrients (NPK)"],
        "Moderate": ["Monitor field in next 2–3 days", "Check irrigation schedule", "Inspect leaves for early issues"],
        "Healthy": ["Continue normal monitoring", "Maintain irrigation and nutrient schedule"]
    }[risk]

    # Print timing once in a while (not always)
    # print("TIMING build:", round(t1-t0,3), "sec | predict:", round(t2-t1,3), "sec")

    return {
        "risk_level": risk,
        "confidence": float(stress_prob),
        "recommended_actions": actions,
        "zones": [
            {"zone_id": "Z1", "risk": risk, "confidence": float(stress_prob)},
            {"zone_id": "Z2", "risk": risk, "confidence": float(stress_prob)},
        ]
    }
