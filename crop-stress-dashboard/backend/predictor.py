import torch
import torch.nn as nn
import numpy as np
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from model_def import build_resnet18_6ch
from satellite_gee import fetch_patch_as_array

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "cnn_crop_stress_model1.pth"

class Predictor:
    def __init__(self, model_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = build_resnet18_6ch(num_classes=2)
        try:
            import os
            full_path = os.path.join(os.path.dirname(__file__), model_path)
            state_dict = torch.load(full_path, map_location=self.device)
            
            # Fix: Strip 'model.' prefix if present in the weights file
            new_state_dict = {}
            for k, v in state_dict.items():
                name = k[6:] if k.startswith('model.') else k
                new_state_dict[name] = v
                
            self.model.load_state_dict(new_state_dict)
            print(f"Success: Model loaded from {full_path}")
        except Exception as e:
            print(f"Warning: Could not load model ({e}). Inference will fail.")
        self.model.to(self.device)
        self.model.eval()

    def preprocess(self, patch_data: dict) -> torch.Tensor:
        import cv2 # Ensure cv2 is available for resizing
        
        # Reconstruct HxWx6 array from GEE dict
        # Training order: [R, G, B, NDVI, VH, VV]
        bands = ["B4", "B3", "B2", "NDVI", "VH", "VV"]
        layers = []
        
        for b in bands:
            if b in patch_data:
                arr = np.array(patch_data[b]).astype(np.float32)
                
                # Normalization logic from training notebook
                if b in ["B4", "B3", "B2"]:
                    # Visual scaling for RGB: Sentinel-2 SR 0-10000 mapping to 0-1
                    # Using 10000 to match standard Sentinel-2 range and avoid bias
                    arr = np.clip(arr / 10000.0, 0, 1)
                else:
                    # For NDVI, VH, VV, training used local min-max per patch
                    # We add a small epsilon and clip to ensure stability
                    p_min = arr.min()
                    p_max = arr.max()
                    if p_max - p_min < 1e-4:
                        arr = np.zeros_like(arr) # Neutral if no variation
                    else:
                        arr = (arr - p_min) / (p_max - p_min + 1e-6)
                
                # Center crop to 224, 224 (initial GEE fetch size)
                h, w = arr.shape
                start_h = (h - 224) // 2
                start_w = (w - 224) // 2
                cropped = arr[start_h:start_h+224, start_w:start_w+224]
                
                # IMPORTANT: Resize to 128x128 to match training dimensions
                resized = cv2.resize(cropped, (128, 128))
                layers.append(resized)
            else:
                layers.append(np.zeros((128, 128), dtype=np.float32))
        
        # Stack to 6-channel: (6, 128, 128)
        x = np.stack(layers, axis=0)
        return torch.from_numpy(x).unsqueeze(0).to(self.device)

    def predict_stress_prob(self, x: torch.Tensor, stress_class_index=1):
        with torch.no_grad():
            outputs = self.model(x)
            probs = torch.softmax(outputs, dim=1)
            return probs[0][stress_class_index].item()

# Load model ONCE
predictor = Predictor(MODEL_PATH)

def prob_to_risk(prob: float):
    if prob > 0.7: return "High"
    if prob > 0.4: return "Moderate"
    return "Healthy"

@app.post("/predict")
async def predict_endpoint(payload: dict):
    boundary = payload.get("boundary")
    if not boundary:
        raise HTTPException(status_code=400, detail="Missing 'boundary'")

    # Start timing
    t0 = time.time()

    # 1. Fetch real imagery patch from GEE
    res = fetch_patch_as_array(boundary)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=f"GEE Fetch Error: {res.get('message')}")

    # 2. Preprocess and Predict
    try:
        x = predictor.preprocess(res["patch_data"])
        stress_prob = predictor.predict_stress_prob(x, stress_class_index=1)
        risk = prob_to_risk(stress_prob)
        
        actions = {
            "High": ["Check irrigation within 24–48h", "Inspect pests/disease in high-risk zones", "Check nutrients (NPK)"],
            "Moderate": ["Monitor field in next 2–3 days", "Check irrigation schedule", "Inspect leaves for early issues"],
            "Healthy": ["Continue normal monitoring", "Maintain irrigation and nutrient schedule"]
        }[risk]

        return {
            "risk_level": risk,
            "confidence": round(stress_prob if stress_prob > 0.5 else 1 - stress_prob, 2),
            "stress_prob": round(float(stress_prob), 4),
            "recommended_actions": actions,
            "ml_based": True,
            "processing_time": round(time.time() - t0, 3)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference Error: {str(e)}")
